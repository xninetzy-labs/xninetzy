# Deep Research

Status: implemented (Deep Research V2). Supersedes the earlier per-topic
notes (`DEEP_RESEARCH_ADMIN_ONLY.md`, `DEEP_RESEARCH_SUBPLANNING.md`,
`DEEP_RESEARCH_WORKFLOW.md`, `RESEARCH_ACTION_REGISTRY.md`,
`RESEARCH_NOTIFICATION_POLICY.md`), all now folded here.

## Goal

Give the internal agent — and any external MCP agent — a strong, safe
deep-research capability: multi-source retrieval (web, YouTube, academic),
ranked selection, and a grounded brief with validated citations. Deep
research NEVER auto-saves, sends, uploads, or writes to any store.

## Flow

`run_deep_research` (`os/research/deep_research.py`):

1. Normalize mode (`speed` | `balanced` | `quality`).
2. Access gate — `can_run_deep_research` (`os/research/permissions.py`),
   toggled by `DEEP_RESEARCH_ADMIN_ONLY` (default on).
3. Resource guards — `check_resource_guards` (`os/research/guards.py`),
   enforced regardless of the gate (concurrent-run cap per chat).
4. Create session, run subplans, execute search actions.
5. Rank sources, assign `[S<n>]` sids (`os/research/sources.py`).
6. Generate brief, validate citations (`os/research/citations.py`) —
   unbacked `[S<n>]` refs are stripped; a `*Sumber*` block is appended.
7. Finish session. Result returned to caller only.

## Sources & evidence discipline

`ResearchSource` (`os/research/sources.py`) with `evidence_level`:
`metadata` | `snippet` | `abstract` | `fulltext`. Never claim a higher
level than retrieved. arXiv/Crossref map to `abstract` (or `metadata` when
no abstract). No URL/DOI/author/year/citation is ever fabricated.

Providers:
- Web: Tavily → Serper → DDGS free fallback → `[]`.
- YouTube: YouTube Data API (key required).
- Academic: arXiv + Crossref (`os/research/academic_search.py`).

## Safety

- API keys read only from environment; never enter prompts, SQLite,
  reports, source metadata, logs, or MCP results.
- Retrieved page content is untrusted. `safe_get`
  (`os/research/safe_fetch.py`): HTTP(S)+GET only, DNS-resolve and reject
  private/loopback/link-local/multicast/reserved/unspecified, re-validate
  host after each redirect (max 3), content-type allowlist, size cap,
  `trust_env=False`.
- Saving a brief to Obsidian/Knowledge/Graph goes through HITL approval
  (`research_save_brief`); it is never automatic.

## MCP bridge

All research tools auto-expose via `expose_xninetzy_tools`. External MCP
agents get:
- `deep_research_topic` — run a session.
- `deep_research_get` — status/result by session id (chat-scoped).
- `deep_research_list` — recent sessions for the chat.

Identity is injected server-side; caller-supplied identity is never trusted
for authorization.

## Config

Access gate: `DEEP_RESEARCH_ADMIN_ONLY`, `DEEP_RESEARCH_ALLOW_GROUP_ADMINS`,
`DEEP_RESEARCH_ALLOW_ADMIN_NAMES`.

Resource guards: `DEEP_RESEARCH_MAX_CONCURRENT_PER_CHAT`,
`DEEP_RESEARCH_MAX_SOURCES`, `DEEP_RESEARCH_MAX_QUERIES`,
`DEEP_RESEARCH_TIMEOUT_SECONDS`.

## Storage

`research_sessions` (session state, plan, substeps, sources, brief) and
`research_sources` (per-source rows). Migrations in `db/migrations.py`
(`run_migrations`, idempotent). Neo4j/Graph is never dual-written from this
flow.
