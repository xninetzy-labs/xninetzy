# Workflow examples for `xninetzy-security-testing`

Every tool named here is registered in `xninetzy/tools/registry.py`. A tool that is not registered is never called; report `TOOL_MISSING` instead. `tests/governance/test_security_skill_registry.py` enforces this.

Available today:

- scope and network: `security_scope`, `security_assets`, `security_headers`, `security_api_inventory`, `security_http_probe`
- static: `security_sast`, `security_dependencies`, `security_authz_matrix`, `security_role_paths`, `security_compose_review`, `security_nginx_review`, `scaling_review`
- scanner gateway: `security_check_tools`, `security_run_gitleaks`, `security_run_trivy`, `security_run_osv`, `security_run_semgrep`, `security_sbom`, `security_run_zap`, `security_run_schemathesis`
- findings: `security_threat_model`, `security_validate_finding`, `security_finding_record`, `security_finding_update`, `security_correlate`, `security_regression`, `security_report`
- performance and data stores: `perf_plan`, `perf_run_k6`, `perf_profile`, `perf_compare`, `perf_capacity`, `redis_review`, `postgres_review`

Scanner tools run only from images that are already installed locally; a missing image returns `TOOL_MISSING` and is never pulled. Nuclei is not integrated. Say so in the report; do not simulate a scanner that did not run.

## 1. Quick posture check on the owner's public site

```text
owner: scan https://misbah.dev
orchestrator:
  1. security_scope(
       targets=["https://misbah.dev"],
       rationale="posture check of my own site"
     )                                  → scope_token=sec-...
  2. security_headers(scope_token, target="https://misbah.dev")
  3. security_assets(scope_token, target="https://misbah.dev")
  4. security_api_inventory(scope_token, target="https://misbah.dev")
  5. security_threat_model(scope_token, inventory_summary=<steps 2-4 as JSON>)
```

Steps 2-4 are bounded, read-only GET requests.

## 2. Owner's own stack on this machine (owner lab)

```text
owner: scan my dev stack at http://localhost:8080
orchestrator:
  1. security_scope(
       targets=["http://localhost:8080"],
       rationale="my own dev stack",
       kind="owner_lab",
       attestation="I own and operate this stack",
       request_budget=5000
     )                                  → scope_token, TTL capped at 8 h
  2. security_headers / security_assets / security_api_inventory with that scope_token
```

Rules of `owner_lab`:

- only `localhost`, `127.0.0.1`, `[::1]`; any other host is rejected;
- profile `passive` by default; `active` needs `active_attestation` as well;
- request budget and rate cap per scope; every request is re-checked, so redirects to other hosts and DNS rebinding to a non-loopback address fail;
- `docker_network` is not supported yet.

Do not use `XNINETZY_ALLOW_PRIVATE_TARGETS`: it is deprecated, logs a warning and opens every private host for every tool.

## 3. SAST of the owner's codebase

```text
owner: scan kerentanan di repo saya ~/code/myapp
orchestrator:
  1. security_scope(targets=["file:///home/owner/code/myapp"], rationale="own repo")
  2. security_sast(scope_token, root="/home/owner/code/myapp")
```

`security_sast` defaults to the `light` regex engine (`confidence` 0.3). Findings are leads, not verified vulnerabilities. With no `glob` it detects the languages present (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.go`, `.rb`, `.php`, `.java`) and scans each; the chosen patterns come back in `globs`. `engine="semgrep"` delegates to `security_run_semgrep` and returns `TOOL_MISSING` when Docker or the pinned image is absent; any other engine is rejected. Test and fixture files are skipped for credential rules unless `include_tests=true`. Python-only rules do not run on other languages. Each run is recorded as `sast-light`, and `security_dependencies` records `dependency-inventory`, so `security_report` lists them.

## 4. Dependency inventory

```text
owner: apa saja dependency di monorepo saya
orchestrator:
  1. security_scope(targets=["file:///home/owner/code/monorepo"], rationale="own repo")
  2. security_dependencies(scope_token, root="/home/owner/code/monorepo")
```

Walks the tree (respecting `.gitignore`) and reads `package-lock.json`, `bun.lock`, `pnpm-lock.yaml`, `yarn.lock`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `Cargo.lock`, `pubspec.lock`, `go.sum`, `composer.lock`. The result always has `vulnerabilities: "NOT_ASSESSED"`: it is an inventory. Never present it as a vulnerability scan.

## 5. Record, correlate and regress findings

```text
orchestrator:
  1. security_validate_finding(scope_token, title, asset, location, category, evidence, severity, confidence)
  2. security_correlate(hits=[...], persist=True, scope_token)      → de-duplicated findings
  3. security_finding_record(title, asset, severity, category, evidence, remediation, scope_token)
  4. security_regression(scope_token, finding_id, test_id="tests/security/test_x.py", status="proposed")
```

Evidence must never contain secret values; store rule id, file, line and a hash prefix.

## 6. Full cycle on an owned application

```text
owner: saya mau audit lengkap app saya
orchestrator:
  1. security_scope(...)            for the URL, or owner_lab for localhost
  2. security_scope(...)            a second, file:// scope for the repository
  3. security_headers, security_assets, security_api_inventory
  4. security_sast, security_dependencies
  5. security_threat_model
  6. security_validate_finding for each verified issue, then security_correlate
  7. security_finding_record + security_regression for each fixed issue
```

Call `security_report(scope_token)` for the consolidated report. It lists every tool that did not run as `NOT_ASSESSED`; keep those under limitations.

## 7. Refusal example: third-party or protected host

```text
owner: scan fst.unair.ac.id
orchestrator:
  → security_scope refuses: "target dilindungi (institusi pihak ketiga)"
  → hosts ending in .ac.id, .go.id and .mil.id are refused
  → offer alternative: a self-hosted mirror, run through owner_lab
```

The refusal is in `_normalize_target` (`xninetzy/tools/ecosystem/security_tools.py`), applies to every scope kind, and cannot be overridden from chat or by `XNINETZY_ALLOW_PRIVATE_TARGETS`.

## 8. Scanner gateway on the owner's repository

```text
owner: cek secret dan CVE di repo saya
orchestrator:
  1. security_scope(targets=["file:///home/owner/code/myapp"], rationale="own repo")
  2. security_check_tools()                         → per-scanner READY/DEGRADED/MISSING/UNHEALTHY
  3. security_run_gitleaks(scope_token, root="/home/owner/code/myapp", persist=True)
  4. security_run_trivy(scope_token, root="/home/owner/code/myapp", persist=True)
  5. security_run_osv(scope_token, root="/home/owner/code/myapp", persist=True)
  6. security_report(scope_token)
```

A scanner whose image is not installed returns `TOOL_MISSING` with the `docker pull` command; tell the owner to pull it, do not run it yourself. Secrets are never returned: only rule id, file, line and a hash prefix.

## 9. Load test and capacity on an owner lab

```text
owner: load test API saya di localhost:3000
orchestrator:
  1. security_scope(targets=["http://localhost:3000"], kind="owner_lab", attestation="...", request_budget=20000)
  2. perf_plan(scope_token, target="http://localhost:3000", endpoints=[...])   → k6 script, nothing executed
  3. perf_run_k6(scope_token, ...)          → runs in the k6 container under the memory watchdog
  4. perf_compare(baseline, candidate)  /  perf_capacity(...)
```

`perf_run_k6` requires an `owner_lab` scope, reserves the request budget up front, and aborts the run when available memory falls under the watchdog floor.

