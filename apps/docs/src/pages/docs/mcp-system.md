---
layout: ../../layouts/DocsLayout.astro
title: MCP system reference
description: "Canonical reference for the Xninetzy MCP server: transports, registry, gateway, tasks, trace, and security."
section: Start
badge: Reference
difficulty: intermediate
readingTime: 15 min
---

The MCP server is the only public interface Xninetzy exposes. Every
capability — Obsidian, HEBAT, Cyber Campus, Lightning, Knowledge,
Career, reminders, automation, skills, security — is delivered as an
MCP tool under one canonical registry.

```text
host (Claude / Claude Code / Cursor / Codex / OpenCode)
  │  stdio   or   Streamable HTTP (loopback by default)
  ▼
xninetzy.interfaces.mcp_server   ─── FastMCP("xninetzy", ...)
  │
  ├── xninetzy.tools.registry.get_all_tools()   (385 tools)
  │     │
  │     └── xninetzy.tools.manifest.manifest_for(name)
  │           ├── feature_pack: core | academic-unair | research | coding
  │           ├── risk:         read | draft | write | final
  │           ├── stability:    stable | experimental
  │           └── requires_approval / requires_idempotency / requires_evidence
  │
  ├── xninetzy.interfaces.tasks_extension          (SEP-2663, 4 tools)
  ├── xninetzy.interfaces.external_mcp             (gateway, 5 tools)
  ├── xninetzy.observability.trace                 (SEP-414, W3C traceparent)
  └── xninetzy.os.security.captcha.lockout         (CAPTCHA auto-OCR guard)
```

The host owns reasoning, planning, and tool selection. Xninetzy owns
capability, replay safety, idempotency, owner identity, and approval
gates. There is no server-side agent loop.

## Tool registry

Live probe at any time:

```bash
uv run --no-project --directory . python scripts/mcp_audit.py
```

Install scripts:

| Script | OS | Install via |
|---|---|---|
| `scripts/install-mcp.sh` | Linux + macOS | `curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh \| bash` |
| `scripts/install-mcp.ps1` | Windows (PowerShell 5.1+) | `iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 \| iex` |

Both scripts clone the repo, ensure `uv`, write `.env` with a random
`AI_API_KEY`, run `uv sync --all-extras`, and execute the release gate.
`XNINETZY_INSTALL_MODE=docker` switches the path to `docker compose up
-d --build`.

The audit script emits a JSON snapshot and exits non-zero if the
canonical FINAL-tool set drifts.

| Metric | Value |
|---|---|
| Total tools | **385** |
| Risk = `read` | 22 |
| Risk = `draft` | 13 |
| Risk = `write` | 347 |
| Risk = `final` | **3** |
| Feature pack = `core` | 305 |
| Feature pack = `academic-unair` | 40 |
| Feature pack = `research` | 37 |
| Feature pack = `coding` | 3 |
| Stability | 385/385 `stable` |

Risk classifier (`xninetzy/os/policy/action_policy.py::classify_risk`):

- `_FINAL_ACTIONS` set or suffix `_final_submit` → `final`
- contains `prepare|plan|draft|preview|dry_run|analyze` → `draft`
- matches `_READ_ACTIONS` set or prefix `read|list|get|check|search|status`
  or suffix `_status|_info` → `read`
- everything else → `write`

The orchestrator enforces `_effective_tier = max(declared, manifest_tier)`
so an owner-supplied tier downgrade cannot demote a `final` tool
(`xninetzy/cli/orchestrator.py`).

## FINAL-class tools

These three tools always require HITL approval server-side:

1. `hebat_upload_submission` (alias-mapped from
   `hebat_submit_submission` in `xninetzy/tools/manifest.py`)
2. `portal_krs_war_arm`
3. `qa_fill_kuesioner`

Approval is enforced through `xninetzy/os/hitl/approval_service.py`
(`request_approval`, `set_approval_status`, `validate_approval`).
Owner check: `xninetzy/os/research/permissions.py::is_owner_admin`.

## Transports

| Transport | Status | Default | Source |
|---|---|---|---|
| stdio | primary | yes | `xninetzy/interfaces/mcp_server.py` |
| Streamable HTTP | secondary (loopback) | opt-in | `XNINETZY_MCP_TRANSPORT=streamable-http` |
| Legacy HTTP+SSE | n/a | n/a | not used |
| REST / GraphQL | n/a | n/a | MCP-only |

Bootstrap validation:

- `_TRANSPORT ∈ {"stdio", "streamable-http"}` else `ValueError`
- `_HTTP_HOST` must parse as IP
- non-loopback host → stderr WARNING advising OAuth 2.1 + Resource
  Indicators (RFC 8707) + Client ID Metadata Documents before real use

`FastMCP(...)` is constructed with `stateless_http=True`,
`json_response=True`, `host`, `port`, `streamable_http_path`.

| Env var | Default |
|---|---|
| `XNINETZY_MCP_TRANSPORT` | `stdio` |
| `XNINETZY_MCP_HTTP_HOST` | `127.0.0.1` |
| `XNINETZY_MCP_HTTP_PORT` | `8765` |
| `XNINETZY_MCP_HTTP_PATH` | `/mcp` |
| `XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS` | `20` |
| `XNINETZY_MCP_CALL_TIMEOUT_SECONDS` | `180` |

## SDK pin

`pyproject.toml` pins `mcp>=1.28.1,<2`. Resolved at install time:
`mcp==1.28.1`. Stay on SDK v1.x; v2 migration is a follow-up.

## External MCP gateway

`xninetzy/interfaces/external_mcp.py` registers untrusted third-party
MCP servers with:

- `risk_level` ∈ `unreviewed` / `low` / `medium` / `high`
- `allowed_tools` allowlist (empty = no calls permitted)
- `last_reviewed_at` timestamp on add
- owner-scoped registration via `is_owner_admin`

`external_mcp_call` rejects any tool not in `allowed_tools` before
issuing the upstream call. Every result is tagged
`untrusted_source=True`. Enable flags (all `false` by default):

- `EXTERNAL_MCP_ENABLED`
- `EXTERNAL_MCP_ALLOW_CALLS`
- `EXTERNAL_MCP_MAX_SERVERS` (`8`)

Note: `EXTERNAL_MCP_TIMEOUT_SECONDS` exists in config but the gateway
reuses `XNINETZY_MCP_CALL_TIMEOUT_SECONDS` for the actual ceiling.

## Tasks extension (SEP-2663)

`xninetzy/interfaces/tasks_extension.py` exposes a generic long-task
abstraction over MCP `io.modelcontextprotocol/tasks`:

- `tasks_submit(name, payload_json)` → `task_id`
- `tasks_get(task_id)` → status + result
- `tasks_cancel(task_id)` → cancel
- `tasks_list(limit)` → recent

Backed by the `long_tasks` SQLite table. Genuinely long tools
(`deep_research`, `mcp_security_audit`, `system_security_analyze`,
HEBAT ingest) keep their sync fast paths today; migration to Tasks
handles is a follow-up.

## Trace context (SEP-414)

`xninetzy/observability/trace.py` provides W3C `traceparent` /
`tracestate` propagation through MCP `_meta`. Each request gets:

- `request_id` (`req-<16-hex>`)
- 32-hex `trace_id`
- 16-hex `span_id`
- 2-hex `trace_flags`
- optional `tracestate`

`TraceContext.to_meta()` is what callers attach to outbound tool calls.
Malformed input falls back to a fresh trace; regex
`_TRACEPARENT_RE` enforces the W3C shape.

## CAPTCHA / OTP guard

`xninetzy/os/security/captcha/lockout.py` enforces:

- `XNINETZY_CAPTCHA_OCR_ENABLED` (default `false`)
- `XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE` (`0.6`)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD` (`3`)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS` (`600`)
- `XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS` (`3600`)

After threshold failures in window, `should_allow_ocr()` returns `False`
for the cooldown window. Owner fallback via WA delivery is controlled
by `XNINETZY_CAPTCHA_WA_PREFERRED` (default `true`).

## Source adapters (Research + Career)

`xninetzy/os/research/sources/` — 30 adapter modules all wrapping
`SourceAdapter` ABC + `SourceRecord` + `RateLimiter` + `RetryPolicy` +
`CircuitBreakerGuard`.

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

No paid API key is a hard dependency. LinkedIn / Indeed / JobStreet /
Glints are deliberately not integrated.

## Authorization model

`xninetzy/interfaces/mcp_tool_adapter.py::mcp_principal()` injects the
trusted local-owner principal at startup. Tools receive `sender_id` /
`sender_name` from the host call, but those values are never
authorization evidence on their own. Tools that require owner scope
(`external_mcp_*`, `obsidian_organize_apply`, `improvement_approve`,
etc.) check via
`xninetzy/os/research/permissions.py::is_owner_admin`.

FINAL-class tools always require HITL approval regardless of declared
tier in orchestrator plans.

## Release gate

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Six checks must all PASS:

| Check | Verifies |
|---|---|
| `tool_registry` | 385 tools classified, no unknown risk, no missing idempotency |
| `secret_redaction` | `redact_secrets` strips sample OpenAI / GitHub / Google keys |
| `safe_fetch` | SSRF guard rejects non-http(s), private/loopback, oversize |
| `transport_config` | transport ∈ stdio\|streamable-http; default loopback |
| `sdk_pin` | resolved `mcp` version on v1.x |
| `canonical_final_tools` | the 3 FINAL tools match the canonical set |

## Path conventions

| Env var | Default |
|---|---|
| `DATA_DIR` | `~/.local/share/xninetzy` |
| `OUTPUT_DIR` | `~/Documents/xninetzy/output` |
| `GENERATED_DOCUMENTS_DIR` | `~/Documents/xninetzy/generated/documents` |
| `RESEARCH_OUTPUT_DIR` | `~/Documents/xninetzy/generated/research` |
| `UNTRACKED_OUTPUT_DIR` | `~/Documents/xninetzy/generated/untracked` |
| `HEBAT_DATA_DIR` | `~/.local/share/xninetzy/hebat` |
| `HEBAT_DOWNLOAD_DIR` | `~/Documents` |
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` |
| `OBSIDIAN_VAULT_PATH` | `/app/obsidian-vault` |
| `EXTERNAL_MCP_REGISTRY_PATH` | `/app/data/external-mcp.json` |

`ARTIFACT_ALLOWLIST=true` (default) rejects writes outside the four
`*_DIR` roots.

## Removed in v2.2.0

If any doc references these, the doc is wrong:

| Removed | Replacement |
|---|---|
| WhatsApp engine (Baileys) | none — `/docs/whatsapp/` deleted |
| LangGraph agent loop | host does reasoning |
| Ink CLI binary | `xninetzy.cli.supervisor {init,start,release-check}` |
| `services/ai` HTTP service | MCP server is the only long-running process |
| `MCP_API_KEY` + `WA_MCP_API_KEY` pairing | single `AI_API_KEY`; stdio = OS process boundary |
| `/api/chat` slash commands | `/api/chat` HTTP bridge for non-stdio hosts; slash commands removed |
| Wall-garden career scrapers | RemoteOK + ArbeitNow only |
