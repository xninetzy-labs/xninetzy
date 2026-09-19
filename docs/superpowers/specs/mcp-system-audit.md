# MCP System Audit (canonical truth for v2.2.0)

Audit date: 2026-09-19. Source: direct read of `xninetzy/` source tree +
live tool-registry probe. This file is the source of truth that any docs
rewrite must match.

## 1. Tool count + risk distribution

Live probe via `xninetzy.tools.registry.get_all_tools()`:

| Metric | Value |
|---|---|
| Total tools | **343** |
| Risk = `read` | 23 |
| Risk = `draft` | 12 |
| Risk = `write` | 305 |
| Risk = `final` | **3** |
| Feature pack = `core` | 259 |
| Feature pack = `academic-unair` | 40 |
| Feature pack = `research` | 37 |
| Feature pack = `coding` | 7 |
| All stable | 343/343 |

FINAL-class tools (require HITL approval):

1. `hebat_upload_submission` (alias mapped from `hebat_submit_submission`)
2. `portal_krs_war_arm`
3. `qa_fill_kuesioner`

Risk classifier (`xninetzy/os/policy/action_policy.py::classify_risk`):

- matches `_FINAL_ACTIONS` set OR name ends with `_final_submit` → `final`
- contains any of `prepare|plan|draft|preview|dry_run|analyze` → `draft`
- matches `_READ_ACTIONS` set OR starts with `read/list/get/check/search/status`
  OR ends with `_status`/`_info` → `read`
- everything else → `write`

Implication: most tool names look like imperative verbs that don't match
the read-prefix list, so they default to `write`. Manifest still requires
`idempotency_key` for every `write`/`final` tool, and release_check
fails when missing (0 such tools today — all write/final are idempotency-covered).

## 2. Transports

| Transport | Status | Source |
|---|---|---|
| stdio (default) | wired in `xninetzy/interfaces/mcp_server.py` via `FastMCP("xninetzy").run(transport="stdio")` | primary |
| Streamable HTTP (opt-in) | `FastMCP(..., stateless_http=True, json_response=True, host=..., port=..., ...)` bound to `XNINETZY_MCP_HTTP_HOST` (default `127.0.0.1`) | secondary |
| Legacy HTTP+SSE | not used | n/a |
| REST/GraphQL | none | n/a |

Bootstrap validation in `mcp_server.py`:

- `_TRANSPORT ∈ {"stdio", "streamable-http"}` else `ValueError`
- `_HTTP_HOST` must parse as IP
- non-loopback host triggers stderr WARNING advising OAuth 2.1 + Resource Indicators

Env vars:

| Var | Default |
|---|---|
| `XNINETZY_MCP_TRANSPORT` | `stdio` |
| `XNINETZY_MCP_HTTP_HOST` | `127.0.0.1` |
| `XNINETZY_MCP_HTTP_PORT` | `8765` |
| `XNINETZY_MCP_HTTP_PATH` | `/mcp` |

## 3. SDK pin

`pyproject.toml` pins `mcp>=1.28.1,<2`. Resolved: `mcp==1.28.1`. Stay on
v1.x; v2 migration is a follow-up.

## 4. Lifecycle / supervisor

`xninetzy/cli/supervisor.py` provides `init / start / release-check`
subcommands. `init` ensures `DATA_DIR`, `OUTPUT_DIR`, `OBSIDIAN_VAULT_HOST_PATH`
exist; `start` prints which transport it is starting; `release-check`
runs 5 gate checks (`tool_registry`, `secret_redaction`, `safe_fetch`,
`transport_config`, `sdk_pin`) — all PASS in v2.2.0.

There is no `xninetzy/cli/orchestrator.py` walk-through entrypoint in the
default flow — the orchestrator exists for YAML plan-driven execution
(`tier: 0..3` gate, HITL approval for FINAL) but is opt-in, not the
default start path.

## 5. Auth + identity

Single auth surface: `AI_API_KEY` in `xninetzy/core/config.py`. No
`MCP_API_KEY`. No `WA_MCP_API_KEY`. No `WA_LOGIN_*` env vars. The
v2.2.0 pivot removed all WhatsApp engine config.

`xninetzy/os/research/permissions.py::is_owner_admin` checks
`ADMIN_NAMES`, `ADMIN_JID`, `OWNER_PHONE_NUMBER`, `OWNER_ALLOWED_JIDS`.

## 6. CAPTCHA / OTP

Opt-in via `XNINETZY_CAPTCHA_OCR_ENABLED` (default `false`). Guard lives
at `xninetzy/os/security/captcha/lockout.py` and enforces:

- `XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE` (default `0.6`)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD` (default `3`)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS` (default `600`)
- `XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS` (default `3600`)

After threshold failures in window → `should_allow_ocr()` returns False
for the cooldown window. Owner fallback via WA delivery is controlled by
`XNINETZY_CAPTCHA_WA_PREFERRED` (default `true`) and
`XNINETZY_CAPTCHA_DIR` (default `/tmp/opencode`).

## 7. Path conventions (env-driven, from `core/config.py`)

| Env var | Default |
|---|---|
| `DATA_DIR` | `~/.local/share/xninetzy` |
| `OUTPUT_DIR` | `~/Documents/xninetzy/output` |
| `GENERATED_DOCUMENTS_DIR` | `~/Documents/xninetzy/generated/documents` |
| `RESEARCH_OUTPUT_DIR` | `~/Documents/xninetzy/generated/research` |
| `UNTRACKED_OUTPUT_DIR` | `~/Documents/xninetzy/generated/untracked` |
| `HEBAT_DOWNLOAD_DIR` | `~/Documents` |
| `HEBAT_DATA_DIR` | `~/.local/share/xninetzy/hebat` |
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` |
| `OBSIDIAN_VAULT_PATH` | `/app/obsidian-vault` |
| `EXTERNAL_MCP_REGISTRY_PATH` | `/app/data/external-mcp.json` |

`ARTIFACT_ALLOWLIST` (default `true`) rejects writes outside the four
`*_DIR` roots.

## 8. External MCP gateway

Lives at `xninetzy/interfaces/external_mcp.py`. Server entries
(`ExternalMcpServer` dataclass) carry:

- `name`, `command`, `args`, `env_vars`
- `enabled: bool`
- `risk_level: "unreviewed"|"low"|"medium"|"high"` (default `unreviewed`)
- `allowed_tools: tuple[str, ...]` (empty = no calls permitted)
- `last_reviewed_at: str | None`

`external_mcp_call` enforces the allowlist before any upstream call; every
result is tagged `untrusted_source=True`. Owner-scoped registration via
`is_owner_admin`. Enable flags:

- `EXTERNAL_MCP_ENABLED` (default `false`)
- `EXTERNAL_MCP_ALLOW_CALLS` (default `false`)
- `EXTERNAL_MCP_MAX_SERVERS` (default `8`)

Note: `EXTERNAL_MCP_TIMEOUT_SECONDS` exists in `core/config.py` (default
`30.0`) but `external_mcp_call` actually reuses
`XNINETZY_MCP_CALL_TIMEOUT_SECONDS` (default `180`). The 30-second
default is a stale config knob; the effective ceiling is the MCP call
timeout.

## 9. Tasks extension (SEP-2663)

`xninetzy/interfaces/tasks_extension.py` exposes generic long-task
abstraction over MCP `io.modelcontextprotocol/tasks`. Tools:

- `tasks_submit`, `tasks_get`, `tasks_cancel`, `tasks_list`

Backed by `long_tasks` SQLite table. Today, genuinely long-running
tools (`deep_research`, `mcp_security_audit`, `system_security_analyze`,
HEBAT ingest) keep their sync fast paths; the migration to Tasks
handles is a follow-up.

## 10. Trace context (SEP-414)

`xninetzy/observability/trace.py` provides W3C traceparent / tracestate
propagation through MCP `_meta`. Each request gets:

- `request_id` (`req-<16-hex>`)
- 32-hex `trace_id`
- 16-hex `span_id`
- 2-hex `trace_flags`
- optional `tracestate`

Parsing uses regex `_TRACEPARENT_RE`; malformed input falls back to a
fresh trace. `TraceContext.to_meta()` is what callers attach to outbound
tool calls.

## 11. Source adapters (Research + Career)

`xninetzy/os/research/sources/` — 30 adapter modules:

| Category | Adapters |
|---|---|
| Academic preprint | arxiv, openalex, crossref, pubmed, europe_pmc, dblp, semantic_scholar |
| General ref | wikipedia, wikidata, dbpedia |
| Tech / community | hackernews, reddit, rss, github, stackoverflow |
| ML registries | open_llm_leaderboard, papers_with_code, huggingface, kaggle, zenodo |
| Security | nvd |
| Patents / geo | patentsview, osm |
| Economics / stats | world_bank, fred, bps |
| Archive | wayback |
| Career | remoteok, arbeitnow |

All wrap `SourceAdapter` ABC + `SourceRecord` dataclass with
`RateLimiter`, `RetryPolicy`, `CircuitBreakerGuard`. No paid API key is
a hard dependency. LinkedIn / Indeed / JobStreet / Glints are deliberately
not integrated.

## 12. Subsystems present

| Subsystem | Module |
|---|---|
| Lightning (CPU bandit) | `xninetzy/os/lightning/` — 15 tools |
| HITL approval | `xninetzy/os/hitl/` |
| HEBAT academic | `xninetzy/os/academic/hebat/` — login, courses, materials, assignments |
| Mahasiswa Portal | `xninetzy/os/academic/mahasiswa_portal/` — profile, grades, KRS, grade token |
| QA Kuesioner | academic group |
| Obsidian vault | `xninetzy/os/notes/` |
| Knowledge (FAISS) | `xninetzy/os/knowledge/` |
| Inbox / OS kernel | `xninetzy/os/inbox/` |
| Memory lifecycle | `xninetzy/os/memory/` |
| Policy / risk | `xninetzy/os/policy/` |
| Security guards | `xninetzy/os/security/` |
| Backup | `xninetzy/os/backup/` |

## 13. Subsystems removed in v2.2.0

If a doc references any of these, the doc is wrong and must be deleted or
rewritten with the v2.2.0 replacement:

| Removed | Replacement |
|---|---|
| WhatsApp engine (Baileys) | none — doc deleted |
| LangGraph agent loop | none — host does reasoning |
| Ink CLI | `xninetzy.cli.supervisor {init,start,release-check}` |
| `services/ai` HTTP service | `xninetzy.cli.supervisor start` (MCP server is the only long-running process) |
| `MCP_API_KEY` + `WA_MCP_API_KEY` pairing | single `AI_API_KEY`; transport = OS process boundary for stdio |
| `/api/chat` slash commands | MCP tools only |
| Wall-garden career scrapers (LinkedIn, Indeed, JobStreet, Glints) | RemoteOK + ArbeitNow only |

## 13b. Skill catalog size

| Path | Count |
|---|---|
| `.agents/skills/` total | 68 skill bodies |
| `.agents/skills/career/` | 19 career skills |
| Skills installed by `scripts/install_skills.py` | harness-symlinked |

## 14. Tests (snapshot from baseline)

- Baseline pass: 811 (Phase 0) → 828 (Phase 13). Net +17.
- Baseline fail: 29 (unchanged across both phases; pre-existing
  skill-system drift + collection-blocked files).
- Collection-blocked: 7 (langchain_anthropic missing in env; module
  package split for `ResearchSource` / `selected_sids`).
- ruff: 0 errors.
- release-check: 5/5 PASS.
