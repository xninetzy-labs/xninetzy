# Security, performance and scaling upgrade plan

Date: 2026-09-30. Status: implemented, see the status table. Author: Claude Code session in `ceria_fooundation`, at the owner's request ("if the xninetzy skills and security tooling fall short, write a complete upgrade plan in its docs for security, tools and other domains").

## Implementation status (2026-09-30)

Registry total after this work: 571 tools. Verification here is unit and contract tests plus local fake servers and fake Docker executors. No scanner image was pulled and run, no k6 run hit a real service, and no Redis or Postgres instance was queried, so every "Done" below means "implemented and covered by tests", not "proven against the CERIA stack".

| WP | Status | Notes |
|---|---|---|
| WP1 | Done | `skill_resource_read` accepts `resource`. `workflow.md`, `SKILL.md` and `install.md` describe only registered tools; `security_check_tools` is registered, and `security_execute` / `security_findings` stay in `PLANNED_TOOLS`. `tests/governance/test_security_skill_registry.py` covers the two security skills. `tests/governance/test_skill_tool_call_drift.py` covers every skill Markdown file: a `name(` call whose prefix is a registry tool group must be a registered tool. Bare identifiers are not matched, because that produced field-name false positives. |
| WP2 | Done, lab limits | `security_scope(kind="owner_lab")`: loopback only, TTL ≤ 8 h, request budget, rate cap, per-request loopback re-check (redirects and rebinding), second attestation for `active`. `docker_network` is rejected as unsupported. `XNINETZY_ALLOW_PRIVATE_TARGETS` logs a deprecation warning. Protected suffixes (`.ac.id`, `.go.id`, `.mil.id`) are enforced in `_normalize_target` for every scope kind. |
| WP3 | Done, not run against real images | `xninetzy/ecosystem/scanners/` (runner, lock, adapters, parsers). Hardened `docker run`: no network unless the scope allows it, read-only root, dropped capabilities, `docker.sock` mounts refused. Tools: `security_check_tools`, `security_run_gitleaks`, `security_run_trivy`, `security_run_osv`, `security_run_semgrep`, `security_sbom`, `security_run_zap`, `security_run_schemathesis`. A missing binary or image returns `TOOL_MISSING`. Secrets are redacted before anything is stored. No `security-tools.lock` ships in the repo; `security_check_tools(pin=True)` writes one from local digests. |
| WP4 | Done | Light-engine rules fixed and labelled confidence 0.3. `security_sast(engine="semgrep")` delegates to `security_run_semgrep`. With no `glob` it detects languages and scans each. `security_dependencies` walks the tree and parses 11 lockfile formats and points at `security_run_osv` / `security_run_trivy` for advisories; without them it reports `NOT_ASSESSED`. Both tools record a run (`sast-light`, `dependency-inventory`) so `security_report` can list them. |
| WP5 | Done | `security_http_probe` (`xninetzy/tools/ecosystem/security_probe_tools.py`): CORS reflection, CSRF content type, origin, introspection, GET mutation, batching and alias limits, depth, error masking, TRACE, security headers, and rate-limit spoofing (active profile plus a request budget only). Failed checks are upserted as findings. |
| WP6 | Done | `security_authz_matrix` (GraphQL SDL and OpenAPI, bun or pytest skeleton, refuses without a test-database guard, `target` must be `test`) and `security_role_paths` (role-write paths with guards, weaker or unguarded flagged). Both are confined to the file scope, including symlink escapes. |
| WP7 | Done | `security_compose_review` (optional `docker compose config` with `--no-interpolate`, YAML fallback) and `security_nginx_review` (`run_test` runs `nginx -t` in a hardened, network-less container). |
| WP8 | Done | `security_finding_update` (open, fixed, accepted, false_positive, with `fix_ref` and `regression_test`), de-duplication across runs via `last_seen`, `security_report` in Markdown. |
| WP9 | Done, not run against real k6 | `perf_plan`, `perf_run_k6` (memory watchdog, stops the generator below the floor; a missing Docker or image returns `TOOL_MISSING` before any budget is spent), `perf_profile`, `perf_compare`, `perf_capacity`. |
| WP10 | Done | `scaling_review` with file:line output and the connection-budget check (replicas × pool vs `max_connections`). |
| WP11 | Done, not run against real servers | `redis_review` (command allowlist: PING, INFO, CONFIG, SCAN, TTL, PTTL, MEMORY, TYPE, SELECT, AUTH, DBSIZE) and `postgres_review` (SELECT and SHOW only, otherwise `PsqlError`); secrets in output are redacted. |

Open items: a shipped `security-tools.lock` with reviewed digests, and running the WP3, WP9 and WP11 tools against the real CERIA stack, which is the only evidence for the acceptance lines below.

Later additions outside this plan: Tableau workbooks now validate against the official 2026.1 and 2026.2 XSDs, and four BPMN 2.0 tools (`process_bpmn_generate`, `process_bpmn_validate`, `process_bpmn_import`, `process_bpmn_convert`) produce diagram-interchange files for Bizagi Modeler. Neither was opened in Tableau Desktop or Bizagi Modeler; the tools return `verified_in_bizagi: false`.

## 1. Why

On 2026-09-30 the owner asked for three things on the CERIA monorepo:

- a k6 load test at 1,000, 5,000 and 10,000 VUs, with optimisation;
- a full security test through the xninetzy skills;
- horizontal scaling with nginx and Docker.

The skills `xninetzy-security-testing` and `api-security` supplied the doctrine, but most of the work ran outside xninetzy: Docker scanners, curl probes, Bun tests and hand-written k6 scripts. Every gap below was hit during that session. Section 8 has the evidence.

## 2. Gaps found

| ID | Area | What happened | Where |
|---|---|---|---|
| G1 | Skill ↔ tool drift | `xninetzy-security-testing/references/workflow.md` calls `security_check_tools`, `security_declare_target`, `security_run_nuclei`, `security_run_zap`, `security_run_trivy`, `security_run_sast`, `security_run_pentest`, `security_list_scans` and `security_generate_report`. None of them is registered. The registry has `security_scope`, `security_assets`, `security_headers`, `security_api_inventory`, `security_sast`, `security_dependencies`, `security_threat_model`, `security_validate_finding`, `security_regression`, `security_correlate` and `security_finding_record`. | `.agents/skills/xninetzy-security-testing/references/workflow.md`, `xninetzy/tools/ecosystem/security_tools.py` |
| G2 | Scope for owner labs | `security_scope(["http://localhost:8080"])` → `target tidak diizinkan (host private): localhost`. The only way around it is the process-wide `XNINETZY_ALLOW_PRIVATE_TARGETS`, which also opens every other private host for every tool. It was not used. There is no narrow, audited mode for "my own stack on this machine". | `_normalize_target`, `_private_ip_block_disabled` in `security_tools.py` |
| G3 | SAST quality | `security_sast` delegates to `repo_risk`: 4 regex rules, default glob `**/*.py`. On `services/api/src` it returned 18 findings, all false positives: Redis `.multi()...exec()` flagged as "dynamic code execution", `requests.push(id)` in TypeScript flagged as a Python `requests` call, test fixture passwords flagged high. It found none of the 9 real issues. Semgrep (362 rules) found the Dockerfile and nginx issues. | `repo_tools.py` rule table (`exec`, `requests_no_timeout`, `hardcoded_*`) |
| G4 | Dependency analysis | `security_dependencies` returned `dependency_count: 0` for a monorepo with 1,186 locked packages. It reads only a root `pyproject.toml` and `requirements*.txt`: no recursion, no lockfiles, no vulnerability database. Trivy found 2 HIGH and 8 MEDIUM advisories, and OSV-Scanner found further `undici` advisories and an `esbuild` one. | `security_dependencies` |
| G5 | Secrets | No Gitleaks adapter. A committed Bearer token was found only by running Gitleaks by hand. | — |
| G6 | DAST | No ZAP adapter; the baseline and production-edge scans were run by hand. | — |
| G7 | GraphQL and CORS checks | The most valuable findings came from hand-written probes, which no tool covers:<br>• graphql-yoga reflected any `Origin`, including `null`, with credentials;<br>• form-encoded POSTs ran mutations (CSRF);<br>• introspection was open in production. | — |
| G8 | Authorization testing | Two privilege escalations (ADMIN could create a SUPER_ADMIN, and `setRole` bypassed the super-admin rule) were found by reading resolvers and proven with a hand-written role × operation matrix. No tool generates or runs such a matrix. | — |
| G9 | Infrastructure checks | Nothing flagged that Redis, Postgres and the services listened on `0.0.0.0`, or that Redis answered on the LAN IP without a password. Both are simple to detect from `docker compose config` and `ss -ltn`. | — |
| G10 | Finding lifecycle | `security_finding_record` writes a note, but a finding cannot move to fixed or accepted, be linked to its regression test, or be de-duplicated across runs. | `security_finding_record` |
| G11 | Tool health | No `security_check_tools`, and no `security-tools.lock` as described in `references/install.md` §28. A missing scanner cannot be reported as `TOOL_MISSING` automatically. | — |
| G12 | Parameter naming | `skill_resource_read(name, resource=...)` fails validation. The required parameter is `relative_path`, while `skill_resource_list` returns items that read like `resource` values. | `skill_resource_read` |
| G13 | Performance domain | No load-test, profiling or capacity tools exist. The laptop rebooted twice during 10,000-VU runs because nothing capped memory or stopped the generator when available memory fell below 1 GB. | — |
| G14 | Scaling review | Horizontal scaling surfaced correctness bugs that a checklist tool would catch:<br>• an in-process chat bus;<br>• cron jobs running on every replica;<br>• per-replica caches without invalidation;<br>• no Celery beat in production;<br>• nginx upstreams resolved only at start. | — |
| G15 | Redis and Postgres insight | No read-only tool reports Redis TTL coverage, eviction policy, db separation or big keys, or Postgres top queries (`pg_stat_statements`) and connection budget. | — |

## 3. Principles

1. **Scope first.** Every target goes through `security_scope`. A lab mode is narrower than today's global switch, never wider.
2. **Protected targets stay refused.** The `.ac.id`, `.go.id` and third-party refusal list is unchanged and cannot be overridden from chat.
3. **Non-destructive by default.** Active or aggressive profiles need a separate attestation. Credential brute force, DoS and session-token extraction are never offered.
4. **Redaction.** Secret values never reach tool output, logs, the vault or reports. Findings store rule id, file, line, fingerprint and a hash prefix.
5. **Report `TOOL_MISSING` and `TOOL_BLOCKED`, never fake success.**
6. **Architecture boundary.** Scanner adapters live under `xninetzy/tools/ecosystem/` or a new `xninetzy/ecosystem/scanners/`. Domain modules stay free of `httpx`, `fastapi` and MCP imports (`tests/architecture/`).
7. **No comments in code.** Tool descriptions move out of docstrings into the registry metadata where the MCP layer allows it.

## 4. Work packages

### WP1 — Align the skill with the registry (G1, G12)

- Choose one surface. Recommended: implement the tools that `workflow.md` names, as thin wrappers over WP3–WP6. Then rewrite `workflow.md` and `install.md` against the real names.
- Add a registry test: every tool name in any `SKILL.md` or `references/*.md` exists in `xninetzy/tools/registry.py`.
- `skill_resource_read`:
  - accept `resource` as an alias of `relative_path`;
  - make the validation error name the expected parameter.

**Accept when:** the registry test passes over all 121 skills; the owner can run `workflow.md` §6 end to end.

### WP2 — Owner lab scope (G2)

- New scope kind `owner_lab`, created with `security_scope(targets, kind="owner_lab", attestation=...)`.
- Allowed targets:
  - `http(s)://localhost|127.0.0.1|[::1]:<port>`;
  - addresses on a Docker bridge network that the owner names (`docker_network="ceria-dev_default"`). They are resolved at scope time and pinned.
- Limits:
  - TTL of at most 8 h;
  - a request budget and rate cap per scope (default 20 r/s, 50,000 requests);
  - profile `passive` by default; `active` requires a second attestation string.
- Every tool that takes a `scope_token` checks the pinned addresses on each request, and redirects are re-checked.
- Deprecate `XNINETZY_ALLOW_PRIVATE_TARGETS`. Once `owner_lab` ships, log a warning while the variable is set and remove it in the next minor release.

**Tests:**

- a `localhost` scope works only with `kind="owner_lab"`;
- a public host inside an `owner_lab` scope is rejected;
- rebinding to a new address after scope creation is rejected;
- the budget is enforced;
- protected suffixes are still refused.

### WP3 — Scanner gateway and tool health (G5, G6, G11)

- `xninetzy/ecosystem/scanners/runner.py` runs a pinned image by digest with:
  - `--rm --read-only --cap-drop=ALL --security-opt=no-new-privileges`;
  - `--memory`, `--pids-limit` and `--cpus`;
  - a read-only source mount and a write mount limited to `UNTRACKED_OUTPUT_DIR/security/<session>`;
  - no Docker socket.
- `security-tools.lock`: image digests, versions and database timestamps. `security_check_tools` reports `READY`, `DEGRADED`, `MISSING` or `UNHEALTHY` per capability.
- Adapters, each normalising output into one `ScanHit` schema (tool, rule, severity, file/url, line, fingerprint, redacted evidence):

  | Adapter | Command | Notes |
  |---|---|---|
  | `security_run_gitleaks` | `git`, `dir` | `--redact` is always on |
  | `security_run_trivy` | `fs`, `config`, `image` | |
  | `security_run_osv` | | |
  | `security_run_semgrep` | | Rulesets chosen by detected languages: `p/typescript`, `p/python`, `p/dockerfile`, `p/nginx` and others |
  | `security_run_zap` | `baseline`; `api` with an OpenAPI or GraphQL schema | |
  | `security_run_schemathesis` | GraphQL and OpenAPI | Bounded examples |
  | `security_sbom` | Syft, then Grype | |

- `security_correlate` consumes `ScanHit` from several tools, so agreement raises confidence (Trivy + OSV on the same advisory = high).

**Accept when:** on CERIA the gateway reproduces §8's scanner results: the same advisory ids, 0 unredacted secrets in any output, and `TOOL_MISSING` when an image is absent.

### WP4 — Real SAST and dependency tools (G3, G4)

- `security_sast` becomes a front for `security_run_semgrep`. The regex engine stays only as an explicit `engine="light"` with confidence ≤ 0.3. Its rules are fixed:
  - `exec` must not match `.exec()` method calls on objects;
  - `requests_no_timeout` applies to Python files only;
  - `hardcoded_*` skips `__tests__`, `tests`, `*.test.*` and fixture seeds unless `include_tests=true`.
- The default glob is replaced by language detection.
- `security_dependencies` walks the tree (respecting `.gitignore`) and parses:
  - `bun.lock`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`;
  - `uv.lock`, `poetry.lock`, `requirements*.txt`, `pyproject.toml`;
  - `pubspec.lock`, `go.sum`, `Cargo.lock`, `composer.lock`.
- Vulnerabilities come from WP3's OSV and Trivy adapters. Output: package, version, ecosystem, advisory ids, fixed version, and whether it is a direct dependency and a dev dependency.

**Accept when:** on CERIA the tool lists 5 lockfiles and 1,186 packages, and reports the pre-fix advisories: fast-uri, undici, qs and morgan in the dashboard; hono and esbuild in the API. The light engine produces 0 findings on `lib/cache.ts` and `middleware/rate-limit.ts`.

### WP5 — Web and GraphQL probes (G7)

`security_http_probe(scope_token, base_url, profile="passive")` sends bounded, read-only requests and returns structured results.

| Check | Request | Fails when |
|---|---|---|
| CORS reflection | `GET` and `OPTIONS` with `Origin: https://evil.example` and `Origin: null` | `Access-Control-Allow-Origin` echoes the origin while `Allow-Credentials: true` |
| CSRF content types | `POST` with `application/x-www-form-urlencoded` and `text/plain` bodies containing `{__typename}` | 2xx |
| Origin enforcement | JSON `POST` with a foreign `Origin` | 2xx on a state-changing endpoint |
| GraphQL introspection | `{ __schema { queryType { name } } }` anonymously | Succeeds while the target is flagged `production` |
| GraphQL over GET | `GET ?query=mutation{__typename}` | Not 405 |
| Batching and aliases | An array body, and 200 aliases of `__typename` | Executed without limits |
| Depth | 20 levels of nested `__type { ofType }` | Accepted |
| Error masking | A malformed query | A stack trace appears |
| Methods and headers | `TRACE`; security headers; `Server` version | TRACE allowed, or headers missing |
| Rate-limit spoofing | N requests, each with a different `X-Forwarded-For` | No 429 within the configured budget (needs an explicit `budget`) |

**Accept when:** against the pre-fix CERIA commit (`62aa7c3`) it reports CORS, CSRF and introspection. Against the fixed commit it reports none.

### WP6 — Authorization matrix generator (G8)

- `security_authz_matrix(schema_source, roles, operations, target="test")`:
  - reads the GraphQL SDL or OpenAPI;
  - builds a role × operation × ownership table (own, linked, foreign, anonymous);
  - emits test skeletons for the project's framework (Bun `bun:test`, pytest).
- It never runs against a non-test database. It refuses unless the project declares a test database guard, as CERIA does with `assertFixtureDatabase` or `isTestDatabase`.
- A static helper, `security_role_paths`, lists every resolver that writes a role, capability or privilege field and the guard each one applies. Two write paths that disagree on the rule are flagged, as with `updateUser` vs `adminCreateUser` / `setRole`.

**Accept when:** on CERIA at `62aa7c3` it flags `adminCreateUser` and `setRole` as weaker than `updateUser`.

### WP7 — Infrastructure exposure checks (G9)

`security_compose_review(path)`:

- parses `docker compose config`;
- flags host ports bound to `0.0.0.0` or `::` for data stores (5432, 6379, 3306, 27017, 9200) and internal services;
- flags Redis without `requirepass` when published;
- flags containers without a `user`, and `privileged` or Docker-socket mounts;
- flags missing `mem_limit` in load-test profiles.

`security_nginx_review(conf)`:

- runs `nginx -t` in a pinned container;
- checks `server_tokens`, security headers, `X-Forwarded-For` handling (overwrite vs append), `limit_req`, `client_max_body_size`, and upstream `resolve`;
- flags public locations for `/docs`, `/openapi.json` and `/metrics`.

**Accept when:** on CERIA at `62aa7c3` both tools flag every item in §8's infrastructure rows.

### WP8 — Finding lifecycle (G10)

- `security_finding_update(finding_id, status=open|fixed|accepted|false_positive, fix_ref, regression_test)`.
- Add a `fingerprint` from the scanner, or `rule + normalized location`. Re-running a scanner updates `last_seen` instead of creating duplicates.
- `security_report(session|project)` renders a Markdown report containing:
  - scope and tools with versions;
  - findings with verified or suspected status;
  - passed checks;
  - limitations.

  The CERIA report `docs/SECURITY/pentest-2026-09-30.md` is the target shape.

### WP9 — Performance domain (G13)

New tools, under the same `owner_lab` scope as WP2:

| Tool | Purpose |
|---|---|
| `perf_plan(target, slo)` | Writes a k6 script skeleton from a GraphQL or OpenAPI operation list, with per-operation tags, think time, a ramp/hold/down schedule and thresholds (default p95 < 500 ms, p99 < 1.5 s, errors < 1%). |
| `perf_run_k6(scope_token, script, vus, duration, mem_limit)` | Runs `grafana/k6:<pinned>` in Docker with a memory cap and a **watchdog**: it samples `MemAvailable` every 2 s and stops k6 below a floor (default 1.5 GB). This prevents the reboots seen on the CERIA laptop. It also samples `docker stats` into a CSV. |
| `perf_profile(service, seconds)` | Bun `--cpu-prof-md`, Python `py-spy` in the container. Returns the top self-time frames. |
| `perf_compare(run_a, run_b)` | Table of throughput and p50/p95/p99/error per operation, with the delta. |
| `perf_capacity(runs, replicas)` | Throughput per replica and the saturation point, and names the bottleneck (API CPU, DB CPU, or generator CPU on the same host). |

Rules:

- The generator must not run on the target host for capacity claims. If it does, the report labels the result `same-host`.
- The tools refuse any database whose name does not end in `_test`, unless the owner passes `allow_demo_db=true` for read-only scenarios.

**Accept when:** on CERIA it reproduces the documented run (1,000 VUs × 4 replicas, p95 about 33 ms), and the watchdog stops k6 in a forced low-memory test.

### WP10 — Scaling review (G14)

`scaling_review(repo)` runs static checks that report risks for running N replicas:

- in-process pub/sub or event buses;
- `setInterval` and cron jobs without leader election;
- module-level caches without cross-instance invalidation;
- local file writes;
- in-memory sessions and rate limits;
- a Celery app without a single beat;
- nginx upstreams without `resolve`, or with `Connection "upgrade"` hard-coded, which disables keepalive;
- a DB connection budget, `replicas × pool + others`, compared with `max_connections`.

Output: a checklist with file and line references. The CERIA fixes (`chat-bus.ts`, `leader-lock.ts`, `cache.ts` pub/sub, `ai-beat`) are the reference cases.

### WP11 — Redis and Postgres insight (G15)

- `redis_review(url)`, read-only:
  - `INFO`, `CONFIG GET maxmemory*`;
  - key counts per db;
  - TTL coverage from `SCAN` samples;
  - `MEMORY USAGE` on samples, and big keys.

  It flags `noeviction` and `allkeys-*` policies when a Celery broker shares the instance.
- `postgres_review(dsn)`, read-only:
  - `pg_stat_statements` top 20 by total time;
  - missing index hints from sequential scans on large tables;
  - connections by application;
  - `max_connections` vs the pool budget.

## 5. Order and size

| Phase | Packages | Effort | Unblocks |
|---|---|---|---|
| 1 | WP1, WP2, WP3 (runner + Gitleaks, Trivy, OSV, Semgrep) | about 5 days | Real scans of owner stacks, honest `TOOL_MISSING` |
| 2 | WP4, WP5, WP7 | about 4 days | Tool-driven findings of the CERIA classes |
| 3 | WP6, WP8 | about 4 days | Authorization coverage and finding lifecycle |
| 4 | WP9, WP10, WP11 | about 5 days | Performance and scaling work without hand-written scripts |

Each phase ends with:

- `pytest` green, including `tests/architecture/`;
- the registry-vs-skills test from WP1;
- a replay against the CERIA fixtures and commits named above.

## 6. Risks

| Risk | Mitigation |
|---|---|
| A lab scope becomes a bypass | Only loopback and the owner's named Docker networks; pinned addresses; TTL; budget; audit entry per request batch; protected-suffix list unchanged |
| Scanner supply chain | Images pinned by digest in `security-tools.lock`; update procedure from `install.md` §37 |
| Secret leakage through outputs | Redaction on every adapter output before it is written; test with a planted fake secret |
| Load tests harm the host | Watchdog and memory caps are on by default and cannot be disabled below a 512 MB floor |
| Authorization generator touches real data | Test-database guard required; refuses otherwise |

## 7. Out of scope

- Kubernetes tooling (kube-bench, KubeLinter). The owner runs Docker and nginx only.
- Cloud posture (Prowler).
- Mobile dynamic analysis. MobSF static analysis can join phase 4 if wanted.

## 8. Evidence from the CERIA session (2026-09-30)

| Item | Result |
|---|---|
| Hand-run scanners | Gitleaks 8.30.1, Trivy 0.74.0, OSV-Scanner 2.6.0, Semgrep 1.177.0 (362 rules, 1,518 files), ZAP 2.17.0 baseline |
| Verified findings | 2 High (admin role escalation; dev data stores on the LAN) · 3 Medium (CORS reflection; CSRF via form posts; vulnerable packages) · 4 Low. All fixed, with regression tests. |
| xninetzy tools | `security_scope(localhost)` refused. `security_sast`: 18 of 18 false positives. `security_dependencies`: 0 packages. `security_finding_record`: worked, 6 findings recorded. |
| Load test | k6 1.3.0. Before optimisation, 1 replica: 274 req/s, p95 3.5 s. After, 4 replicas: 777 req/s, p95 33 ms at 1,000 VUs; 0.04% failures at 10,000 VUs. Two host reboots during 10,000-VU runs before memory caps and a watchdog were added. |
| Reports | `ceria_fooundation/docs/SECURITY/pentest-2026-09-30.md`, `docs/OPERATIONS/performance-load-test.md`, `docs/OPERATIONS/horizontal-scaling.md` |
