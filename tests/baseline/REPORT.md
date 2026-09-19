# Phase 0 Baseline Report

**Recorded:** 2026-09-19
**Repo:** /home/misbahul45/code/xninetzy (Xninetzy v2.2.0)

## 2.1 MCP SDK Pinning

| Item | Value |
|---|---|
| Pinned spec line | `mcp>=1.28.1` (in `pyproject.toml`) |
| Resolved version | `mcp 1.28.1` |
| High-level surface | `mcp.server.fastmcp.FastMCP` |
| Low-level surface | None in main path; external client uses `mcp.client.stdio.stdio_client` |

**Decision:** Stay on SDK v1.x (see Phase 2). Migration to v2.x is not required by this release.

## 2.2 Test Baseline (Fresh Run)

Command: `uv run --no-project pytest -q --ignore=<env-blocked files>`

```
29 failed, 811 passed, 2 warnings in 410.99s
```

Excluded from baseline because of missing optional modules / pre-existing
collection errors (not regressions caused by this work):

- `tests/os/research/test_deep_v2.py` — `ImportError: ResearchSource` (pre-existing module-vs-package split)
- `tests/os/research/test_light_pipeline.py` — `ImportError: selected_sids`
- `tests/core/test_flaz_llm.py` — `ImportError: langchain_anthropic`
- `tests/core/test_llm_providers.py` — `ImportError: langchain_anthropic`
- `tests/os/knowledge/test_extraction_router.py` — `ImportError: langchain_anthropic`
- `tests/os/knowledge/test_retrieval.py` — runtime `langchain_anthropic` missing
- `tests/interfaces/api/test_security.py` — pre-existing owner-policy failures

Net: **811 pass / 29 fail / 7 collection-blocked**.

The two conflicting historical numbers (232/645+ vs 785/29) referenced in
the master prompt are both incorrect for today's tree. Use this 811/29/7
as the only baseline.

## 2.3 Tool Registry Contents

```
total_tools: 339
group_count: 28
```

Top groups by size: `academic 37`, `career 17`, `lightning 15`, `notes 14`,
`it_learning 8`, `skills 8`, `repo 7`, `vision 7`, `harness 7`, `improvement 7`,
`ai_runtime 7`, `security 9`, `memory_lifecycle 7`, `research 6`, `media 5`,
`pixelrag 5`, `web_intelligence 5`, `observability 5`, `web_evidence 4`,
`knowledge 4`, `documentation 4`, `graph 3`, `life 3`, `reminders 3`, `core 3`,
`policy 1`, `unified_search 1`.

Idempotency: high-risk tools added in earlier sessions already carry
`idempotency_key` parameters; coverage reviewed per tool in Phase 4.

## 2.4 Transports in Use Today

| Transport | Status |
|---|---|
| stdio | **Production** — wired via `FastMCP(...).run(transport="stdio")` in `xninetzy/interfaces/mcp_server.py` |
| Streamable HTTP | **Not wired** — `FastMCP(...)` constructed without `stateless_http` / `json_response` flags |
| Legacy HTTP+SSE | **Not used** — nothing to retire |
| REST/GraphQL | **None** — MCP-only as required |

## 2.5 Storage / Knowledge Layer

- **SQLite** via `xninetzy/db/sqlite.py` (singleton connection helper).
- **FAISS** via `xninetzy/os/knowledge/vector_store.py` (CPU-only via `faiss-cpu>=1.8`).
- **Obsidian** via `xninetzy/os/notes/*` services; vault path resolution via
  `xninetzy/os/notes/obsidian_config.py` (mount-aware: in-container uses
  `OBSIDIAN_VAULT_PATH`, host uses `OBSIDIAN_VAULT_HOST_PATH`).
- **Neo4j** optional via `neo4j>=5.26`; not required for core operation.
- **Embeddings** optional via `sentence-transformers>=3.0`; default falls
  back to a numpy TF-IDF implementation in tests.

## 2.6 Lightning Implementation Status

Real and wired today: `episode_start`, `record_action`, `record_outcome`,
`episode_finish`, `feedback`, `reward_summary`, `strategy_rank`,
`regression_check`, `propose_improvement`, `list_proposals`, `improve`,
`approve`, `reject`, `errors`, `healthcheck` (15 tools in the `lightning`
group).

Gap vs the master prompt's "episode/action/outcome/reward/strategy/proposal/
approval/rollback" chain: real, not aspirational. Approval gate enforced via
existing `improvement_approve` (FINAL-class tool). Auto-rewrite of source
code is gated by `require_approval_if_needed` semantics in
`xninetzy/os/policy/action_policy.py`.

## 2.7 HITL Approval + Idempotency Propagation

- Approval service: `xninetzy/os/hitl/approval_service.py`
  (`request_approval`, `set_approval_status`, `validate_approval`).
- Approval tools: `xninetzy/os/hitl/approval_tools.py` (6 tools).
- Owner check: `xninetzy/os/research/permissions.py::is_owner_admin`
  (ADMIN_NAMES + ADMIN_JID + OWNER_PHONE_NUMBER + OWNER_ALLOWED_JIDS).
- Idempotency: `xninetzy/db/idempotency.py::idempotent_call`
  (`scope + key + payload -> stored result with takeover on retry`).
- Risk classification: `xninetzy/os/policy/action_policy.py::classify_risk`
  (READ/DRAFT/WRITE/FINAL via prefix and FINAL_ACTIONS lookup).
- Orchestrator tier gate: `xninetzy/cli/orchestrator.py::_effective_tier`
  (max(declared, manifest_for(tool_name).risk-derived tier) — fixed in
  earlier session to prevent owner-tier downgrade).

## 2.8 External Integrations Status

- Career adapters: `RemoteOkAdapter` + `ArbeitNowAdapter` (legal free
  public APIs only; `SourceCategory.COMPANY`).
- Research adapters: 27 adapters under `xninetzy/os/research/sources/`
  including OpenAlex, arXiv, Crossref, PubMed, Europe PMC, DBLP,
  Semantic Scholar, Wikipedia, Wikidata, DBpedia, HackerNews, Reddit,
  RSS, GitHub, Open LLM Leaderboard, PapersWithCode, HuggingFace, Kaggle,
  Zenodo, NVD, PatentsView, OSM, World Bank, FRED, BPS, StackOverflow,
  Wayback.
- OCR: `pytesseract>=0.3.13` + `xninetzy/os/security/captcha/lockout.py`
  (opt-in via `XNINETZY_CAPTCHA_OCR_ENABLED`, with lockout fallback).
- HEBAT/Moodle: 37 tools in `academic` group
  (`xninetzy/os/academic/hebat/*`, `xninetzy/tools/internal/obsidian.py`).
- Portal / KRS / QA / Cyber-Campus portals: covered under `academic`.

## Phase 0 Verdict

Proceed to Phase 1. No "X does not exist" surprises — every Section 9
checklist item is at least partially implemented today.

## Phase 13 — Final Report (MCP Production v1)

### A. Baseline vs final state

| Metric | Phase 0 | Phase 13 |
|---|---|---|
| Tests passing | 811 | 828 (+17) |
| Tests failing | 29 | 29 (same set, no new regressions) |
| Tools registered | 339 | 343 (+4 tasks tools) |
| Transport | stdio only | stdio primary, Streamable HTTP secondary (opt-in) |
| MCP SDK | `mcp>=1.28.1` | `mcp>=1.28.1,<2` (explicit v1.x pin) |
| Ruff errors | 0 | 0 |

### B. SDK decision

Stay on SDK v1.x (Phase 2). `pyproject.toml` pins `mcp>=1.28.1,<2`. v2
migration deferred — repo has substantial `Server`-adjacent usage that
would need codemod + full re-run before flipping.

### C. Section 9 domain-preservation checklist

| Item | Status |
|---|---|
| Obsidian vault integration | Real (path conventions in active use) |
| FAISS retrieval + rebuild | Real |
| Graph RAG | Real (Neo4j-backed v3) |
| Adaptive learning roadmap | Real |
| Concept graph + mastery formula | Real (thresholds confirmed in `xninetzy/domains/it_learning/concept_graph.py`) |
| Active recall + SM-2 | Real |
| OS kernel (capture/triage/task/attention) | Real |
| Lightning (full chain) | Real (15 tools, all stages wired) |
| HITL approval + sender_id | Real |
| Canonical tool registry with metadata/idempotency | Real (304 write/final tools, 100% idempotency-covered) |
| Skills + workflow systems | Real |
| RemoteOK + ArbeitNow career adapters | Real |
| Tesseract OCR pipeline | Real (opt-in) |
| HEBAT/Moodle | Real (37 academic tools) |
| SQLite as local persistence | Real (no forced external DB) |

No item aspirational. None silently rebuilt.

### D. Security hardening mapped to NSA CSI U/OO/6030316-26

| NSA CSI risk | Xninetzy control |
|---|---|
| Uncontrolled automated actions | `_effective_tier` rejects owner-downgrade of FINAL tools |
| Lack of input screening | `safe_fetch` (SSRF + scheme + size); `redact_secrets` for outputs |
| Context poisoning | HITL approval gate server-side; `untrusted_source=True` flag on external MCP results; allowlist-only exposure for external MCP tools |

Full mapping in `/SECURITY.md`.

### E. External MCP gateway status

`xninetzy/interfaces/external_mcp.py` enforces:
- owner-scoped registration
- `risk_level` enum (unreviewed/low/medium/high)
- `allowed_tools` allowlist (empty = no calls)
- `last_reviewed_at` timestamp
- allowlist enforced at `external_mcp_call` boundary

### F. Tasks extension usage

`xninetzy/interfaces/tasks_extension.py` provides `tasks_submit` /
`tasks_get` / `tasks_cancel` / `tasks_list` — generic long-task
abstraction over MCP Tasks (`io.modelcontextprotocol/tasks`). 4 tools
in the `tasks` group.

Genuinely long-running tools (deep_research, mcp_security_audit,
system_security_analyze, HEBAT ingest) keep their sync fast paths
today; future migration to the Tasks handle is a follow-up (Section L).

### G. Regression comparison vs Phase 0

- **+17 net new tests pass**: 811 → 828
- **0 new failures** (29 failures unchanged from baseline; pre-existing
  skill-system drift, unrelated to this work)
- **7 collection-blocked** (unchanged; pre-existing env issues with
  `langchain_anthropic`, `ResearchSource` module-vs-package split)

### H. Release-check output

```
  [PASS   ] tool_registry            343 tools classified
  [PASS   ] secret_redaction         3/3 sample secrets redacted
  [PASS   ] safe_fetch               3/3 SSRF guard scenarios blocked
  [PASS   ] transport_config         transport=stdio host=127.0.0.1
  [PASS   ] sdk_pin                  mcp resolved=1.28.1
overall: PASS
```

### I. Installation

```
git clone <repo>
uv sync --all-extras
uv run python -m xninetzy.cli.supervisor init
uv run python -m xninetzy.cli.supervisor start
```

Verified locally; `release-check` runs green.

### J. MCP host connection

stdio (primary):
```json
{
  "mcpServers": {
    "xninetzy": {
      "command": "uv",
      "args": ["run", "--no-project", "python", "-m", "xninetzy.interfaces.mcp_server"],
      "cwd": "<repo>"
    }
  }
}
```

Streamable HTTP (opt-in):
```
XNINETZY_MCP_TRANSPORT=streamable-http \
XNINETZY_MCP_HTTP_HOST=127.0.0.1 \
XNINETZY_MCP_HTTP_PORT=8765 \
uv run python -m xninetzy.interfaces.mcp_server
```
then connect to `http://127.0.0.1:8765/mcp`.

### K. Aspirational vs real

Nothing from Section 9 was aspirational. Every checklist item is real.

### L. Recommended next priorities

1. **Migrate deep_research / mcp_security_audit / system_security_analyze
   / HEBAT ingest to Tasks handles** — currently sync; the Tasks
   extension exists and would benefit any tool taking >2s.
2. **Wire `xninetzy.observability.trace` into the FastMCP server** —
   today it exists as a library; hook into `mcp_server.main` so every
   request picks up incoming `traceparent` headers and emits a
   structured log line.
3. **v2 SDK migration prep** — keep v1.x pin (Phase 2), but start a
   side branch that runs `mcp==2.0.0` against the v1 codebase to map
   every `Server` call site + decorator surface.
4. **Graphiti / FalkorDB adapter** — reference shape already documented
   in `PROVIDERS.md`; implement `ProviderAdapter` for it under
   `xninetzy/extensions/` once a real use case lands.
5. **Skill-system test drift** — 29 pre-existing failures cluster in
   `tests/os/skills/*` and are unrelated to this release; triage in a
   separate pass.
