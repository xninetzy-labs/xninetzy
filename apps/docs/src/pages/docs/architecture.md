---
layout: ../../layouts/DocsLayout.astro
title: System architecture
description: Service boundaries, request flow, tool registry, persistence, and the MCP transports.
section: Start
---

Xninetzy is an MCP-only monorepo. There is one runtime surface — the MCP
server — and one documentation application.

## Service boundaries

```text
MCP host (Claude / Claude Code / Cursor / Codex / OpenCode)
  ↓ stdio OR Streamable HTTP (loopback)
Xninetzy MCP server / FastMCP :8765 (Streamable) or stdio
  ↓
Application core (xninetzy/)
  ↓
Canonical tool registry → 343 tools across 29 groups
  ↓
Domain modules (knowledge | research | career | learning | security |
                os_kernel | lightning | harness | improvement | ...)
  ↓
Shared engine: router + planner + source registry + cache + dedup +
                entity-resolution + evidence + citation + security
```

There is no server-side agent loop. Clients do their own reasoning. The MCP
server exposes capabilities; it does not decide what to do next.

### Application core

`xninetzy/` owns routing, prompts, the provider registry, the canonical tool
registry, persistence, knowledge retrieval, research, career intelligence,
HEBAT, Obsidian, approvals, Lightning, and the security guards.

### MCP server

`xninetzy/interfaces/mcp_server.py` constructs a `FastMCP("xninetzy",
...)` with `stateless_http=True`, `json_response=True`, and tools registered
from `xninetzy/tools/registry.py`. Tools are exposed at runtime via
`mcp.tool()` decorators — no separate MCP-server code per tool.

There is exactly one MCP server in v2.2.0. No WhatsApp tool server, no
LangGraph runtime, no CLI client.

## Three request paths

1. **Direct tool invocation** — host calls a single tool, returns result.
2. **Multi-step plans** — host uses the CLI orchestrator (`xninetzy
   cli/orchestrator.py`) to execute a YAML plan with per-step tier gates.
3. **Sequential workflows** — host composes tools via its own reasoning;
   Xninetzy provides capability, not orchestration.

## The tool registry is the source of truth

`xninetzy/tools/registry.py` collects all tools. The MCP server reads
this catalog dynamically, so a registered tool does not need a separate
client-specific wrapper. Per-tool metadata (risk class, idempotency,
feature pack, stability) comes from `xninetzy/tools/manifest.py::manifest_for`.

| Field | Source | Example |
|---|---|---|
| `risk` | `RiskClass.READ/DRAFT/WRITE/FINAL` | `FINAL` for `improvement_approve` |
| `requires_approval` | derived from `risk == FINAL` | True for FINAL |
| `requires_idempotency` | `risk in (WRITE, FINAL)` | True for state-changing tools |
| `feature_pack` | `CORE / ACADEMIC_UNAIR / RESEARCH / CODING` | derived from tool name |
| `stability` | `STABLE / EXPERIMENTAL` | `STABLE` |

## Transports

| Transport | Default | Binding | Notes |
|---|---|---|---|
| stdio | YES | (OS process boundary) | Always on; clients launch the binary |
| Streamable HTTP | opt-in via `XNINETZY_MCP_TRANSPORT=streamable-http` | `127.0.0.1` default; warns if non-loopback | stateless + json_response; OAuth 2.1 required for non-loopback |
| Legacy HTTP+SSE | N/A | N/A | deprecated in 2026-07-28 spec; not shipped |

## Persistence

| Data | Default path |
|---|---|
| SQLite | per-`SQLITE_PATH` env var |
| FAISS | per-`VECTOR_DATA_DIR` env var |
| Obsidian vault | per-`OBSIDIAN_VAULT_HOST_PATH` env var (host) / `OBSIDIAN_VAULT_PATH` (container) |
| MCP tasks | `long_tasks` table in the same SQLite |
| Lightning episodes | `lightning_*` tables in the same SQLite |
| Approval ledger | `approval_requests` + `file_operations` tables |

There is no forced external database. Optional backends (Neo4j,
sentence-transformers, Ollama) are opt-in via env vars.

## Single-owner state and the closed loop

Goals, tasks, roadmaps, habits, workouts, HEBAT state, knowledge, and events
belong to the installation rather than a transport. `chat_id` records origin
without splitting owner entities.

```text
HEBAT assignment ─represented_by→ shared task ─reminded_by→ reminder
roadmap item     ─represented_by→ shared task
                                      ↓ task_completed event
                           goal progress + roadmap progress
                                      ↓
                            Personal Context v2
```

Events are persisted before reducers consume them transactionally and write
consumption markers. Unconsumed events are replayed at startup.

## Security boundaries

- Tools have explicit `RiskClass` (READ/DRAFT/WRITE/FINAL).
- `FINAL`-class tools require HITL approval server-side.
- Streamable HTTP non-loopback requires OAuth 2.1 + Resource Indicators
  (RFC 8707) + Client ID Metadata Documents (CIMD); never a custom scheme.
- External MCP servers are untrusted by default; `allowed_tools` allowlist.
- Obsidian restricts paths to the vault + safe extensions; `.backup` is
  blocked at the safety layer.
- `safe_fetch` (SSRF guard) rejects non-http(s) schemes and private hosts.
- `redact_secrets` strips known secret patterns from any logged text.

Full mapping to NSA CSI U/OO/6030316-26 in `/SECURITY.md` at repo root.

## Add a feature

1. define the owning domain and data boundary;
2. implement a service or tool without transport coupling;
3. register the tool in the canonical registry;
4. add domain tests;
5. add MCP protocol tests if the signature changes;
6. update documentation and command examples.
