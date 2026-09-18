---
name: 2026-09-18-research-mcp-design
description: Design doc for Research MCP expansion. Foundation = all-from-scratch (Q1=a). Source registry + adapters + router + tools + skills + harness wiring. Phase 1 vertical slice this turn, phases 2-3 deferred.
metadata:
  type: design
  date: 2026-09-18
  scope: project
  authority:
    - AGENTS.md
    - global opencode AGENTS.md
  supersedes: []
---

# Research MCP Design — 2026-09-18

## Goal

Evolve Xninetzy MCP from "search wrapper" into a **multi-source research
engine**: discover, retrieve, validate, compare, monitor, synthesize
information across free public APIs, with paid providers as opt-in.

## Foundation decision

Per Q1=a: **all-from-scratch**. No external MCP gateway (no spawning GitHub
MCP / Reddit MCP / HF MCP as child processes).

Rationale:
- Avoid upstream dependency on third-party MCP server availability
- Avoid transitive security surface (child MCP = arbitrary code execution)
- Avoid ToS drift when upstream changes
- Reuse existing Xninetzy infra: idempotency, harness, tier gate, audit

Trade-off accepted: more in-tree code, slower to reach breadth. Mitigated
by small per-adapter footprint and shared base class.

## Architecture (Phase 1)

```text
xninetzy/os/research/
├── sources/
│   ├── __init__.py
│   ├── base.py           # SourceAdapter ABC + SourceRecord dataclass
│   ├── registry.py       # SOURCE_REGISTRY dict, get_adapter(id)
│   ├── rate_limit.py     # RateLimiter, RetryPolicy, CircuitBreaker
│   ├── openalex.py       # OpenAlex (free, no key)
│   ├── arxiv.py          # wraps existing academic_search arXiv
│   └── crossref.py       # wraps existing academic_search Crossref
├── router.py             # intent classification → source list
├── dedup.py              # DOI / arXiv ID / URL normalization + dedup
└── evidence.py           # evidence grading helpers

xninetzy/tools/ecosystem/
└── research_v2_tools.py  # 4 new MCP tools wired in _ALL_TOOLS

.agents/skills/
├── research-planner/SKILL.md
├── source-selector/SKILL.md
├── evidence-grader/SKILL.md
├── contradiction-hunter/SKILL.md
└── research-critic/SKILL.md

xninetzy/cli/
├── __init__.py
└── orchestrator.py       # YAML plan loader + tier gate

scripts/
└── optimize_run.py       # ruff+pytest+verify_cpu_only+yarn build
```

## Source adapter pattern

```python
class SourceAdapter(ABC):
    id: str
    category: str
    base_url: str
    requires_api_key: bool
    rate_limit: RateLimit
    retry: RetryPolicy
    circuit_breaker: CircuitBreaker

    @abstractmethod
    async def search(self, query: str, limit: int, **kwargs) -> list[SourceRecord]: ...

    @abstractmethod
    async def fetch(self, identifier: str) -> SourceRecord | None: ...

    @abstractmethod
    async def health(self) -> HealthStatus: ...
```

Each adapter:
- Emits `harness_checkpoint_commit(plan_id, step_id, status)` on completion
- Honors `idempotency_key` if provided
- Returns `SourceRecord` (frozen dataclass)
- Circuit breaker: 5 failures → open for 60s → half-open probe
- Never raises on transient failure — returns `[]` + logs warning
- Never exposes API keys in logs (`{provider}: query returned N results`)
- Honors rate limit per provider via `RateLimit` instance

## SourceRecord shape

```python
@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    source: str           # "openalex", "arxiv", "crossref"
    source_type: str      # "paper", "dataset", "news", "code", ...
    published_at: str | None
    updated_at: str | None
    author: str | None
    snippet: str
    content: str | None
    language: str
    license: str | None
    retrieved_at: str
    confidence: float     # 0.0-1.0
    primary_source: bool
    citation: str | None
    identifiers: dict[str, str]  # doi, arxiv_id, openalex_id, etc.
```

## Source router

Pure-logic intent classifier → source list. No LLM.

```python
def route(intent: ResearchIntent) -> list[str]:
    """Return list of source adapter ids for the intent."""
```

Intent inputs:
- `category: Literal["paper", "code", "dataset", "news", "company", "model",
  "benchmark", "security", "patent", "economics", "geographic", "entity",
  "general"]`
- `requires_open_access: bool`
- `language: str`
- `freshness_days: int | None`

Routing table:

| Intent | Sources |
|---|---|
| `paper` | openalex, arxiv, crossref, semantic_scholar (Phase 2), pubmed (Phase 2) |
| `code` | github (Phase 2), npm, pypi, crates (Phase 2) |
| `dataset` | huggingface (Phase 2), kaggle (Phase 2), world_bank (Phase 2) |
| `news` | web_search (existing), rss (Phase 2), gdelt (Phase 3) |
| `company` | web_search (existing), crunchbase (OUT-OF-SCOPE paid) |
| `model` | huggingface (Phase 2), openrouter (OUT-OF-SCOPE) |
| `benchmark` | papers_with_code (Phase 2) |
| `security` | nvd_cve (Phase 2), osv (Phase 3) |
| `patent` | google_patents (Phase 3) |
| `economics` | world_bank (Phase 2) |
| `geographic` | osm_nominatim (Phase 3) |
| `entity` | wikidata (Phase 2), wikipedia (Phase 2) |
| `general` | web_search (existing), youtube (existing) |

## New MCP tools (Phase 1)

| Tool | RiskClass | Tier | Notes |
|---|---|---|---|
| `research_search` | READ | 0 | Multi-source search via router; emits harness checkpoint |
| `research_fetch` | READ | 0 | Fetch single record by identifier; emits harness record_step |
| `research_compare_sources` | READ | 0 | Dedup + cross-source confirmation; emits harness record_step |
| `research_grade_evidence` | READ | 0 | Evidence grading per source quality rubric; emits claim_ledger |

All Tier 0/1. None touch external academic sources for mutation. None bypass
CAPTCHA. None touch FINAL actions. Safe for auto-execution.

## CLI orchestrator

`xninetzy/cli/orchestrator.py` + `[project.scripts]` entry in pyproject.

YAML plan shape:

```yaml
version: 1
title: "Research self-improving LLM"
steps:
  - id: search_papers
    tool: research_search
    args:
      intent: paper
      query: "self-improving LLM"
      limit: 10
    tier: 0  # auto
    idempotency_key: "auto"
  - id: grade_evidence
    tool: research_grade_evidence
    args:
      records_from: search_papers
    tier: 0
    depends_on: [search_papers]
```

Tier gate per step:
- `tier: 0` (READ) — auto-execute
- `tier: 1` (WRITE/DRAFT) — auto with idempotency_key required
- `tier: 2` — halt, emit preview, request approval
- `tier: 3` (FINAL) — halt, request `approval_id`

CLI entry:
- `python -m xninetzy.cli.orchestrator run plan.yaml`
- `python -m xninetzy.cli.orchestrator validate plan.yaml`
- `python -m xninetzy.cli.orchestrator resume plan.yaml`

## CAPTCHA OCR lockout

Add env: `CAPTCHA_OCR_LOCKOUT_THRESHOLD` (default 3).

Behavior:
- Each CAPTCHA OCR attempt increments counter
- Counter resets every 10 minutes
- If counter >= threshold → auto-disable OCR for 1 hour
- Force fallback to manual delivery via `os_inbox` kind=`captcha`
- Log event via `observability_emit`

## Batch HITL approval

Extend `hitl_request_approval` to accept `plan_id`. Single `approval_id`
covers all FINAL steps in plan. Per-step receipts via `claim_ledger_record`.

Plan with 5 FINAL steps → 1 approval flow, 5 receipts.

## Harness drift/resume/checkpoint

3 new tools in `xninetzy/tools/ecosystem/harness_tools.py`:

| Tool | Purpose |
|---|---|
| `harness_plan_drift_detect` | Compare plan's `required_tools` vs current `_ALL_TOOLS`. Return drift report. |
| `harness_resume_safe` | Read last checkpoint, replay only steps with `outcome != "ok"` from same sequence. Validates `idempotency_key`. |
| `harness_checkpoint_commit` | Persist checkpoint with hash of args + outcome. |

All Tier 0/1. Idempotent.

## Optimization runner

`scripts/optimize_run.py`:
1. Run `ruff check xninetzy tests`
2. Run `pytest -ra`
3. Run `python scripts/verify_cpu_only.py`
4. Run `cd apps/docs && yarn check && yarn build`
5. Emit JSON report to `OUTPUT_DIR/optimize-report-{timestamp}.json`

No auto-fix. Owner reviews report.

## Improvement applier (dry-run)

`xninetzy/os/improvement/applier.py`:
- Read `improvement_proposals` table
- Filter `tier <= Tier 1` (auto-eligible)
- Emit dry-run diff (no source modification)
- Owner signs via `hitl_request_approval` to apply
- Apply path gated through `improvement_approve` (already FINAL, requires approval)

## 5 meta-skills (Phase 1 bodies)

Each skill body follows Agent Skills contract:
- YAML frontmatter (no wrapper, no leading title)
- Workflow guidance, NOT factual evidence

Skills:
1. `research-planner` — decompose query into research plan
2. `source-selector` — pick sources per intent
3. `evidence-grader` — grade evidence strength
4. `contradiction-hunter` — find contradicting findings
5. `research-critic` — critique research synthesis

Deferred skills (Phase 3): discovery/*, ai/*, engineering/*, business/*,
security/*, mcp/* — 25 skills.

## Out of scope this design

- External MCP gateway (Q1=a permanently)
- LinkedIn/Indeed Jobs (ToS barrier)
- Amazon/Shopee/Tokopedia (anti-bot)
- X/IG/TikTok (paywalled API)
- Crunchbase/PitchBook (paid only)
- Trend engine (Phase 3)
- Citation graph full layer (graph_v3 already partial, Phase 3)
- Skill bodies beyond 5 meta (Phase 3)

## Verification (Phase 1 acceptance)

- `ruff check xninetzy tests` — clean
- `pytest -ra` — all pass, including new tests for adapters + tools + skills
- `python scripts/verify_cpu_only.py` — clean
- `python -m xninetzy.cli.orchestrator validate examples/research-sample.yaml` — exits 0
- Live test of OpenAlex adapter (real HTTP call to `api.openalex.org`)
- Harness checkpoint recorded for every state-changing tool call

## Risks

- Phase 1 may exceed this turn's time budget → split: ship OpenAlex adapter
  + 3 tools + audit docs this turn, defer rest
- Rate limits on free APIs may throttle — circuit breaker mitigates
- Source registry schema may evolve — keep `SourceRecord` minimal in Phase 1

## Sources

- `xninetzy/os/research/academic_search.py` — existing arXiv/Crossref
- `xninetzy/os/research/web_search.py` — existing web search providers
- `xninetzy/tools/manifest.py` — `manifest_for()` + RiskClass
- `xninetzy/tools/ecosystem/harness_tools.py` — S6 surface
- Audit v1: `2026-09-18-audit-tool-surface.md`
- Audit v2: `2026-09-18-audit-research-expansion.md`
