# XNINETZY REAL SYSTEM AUDIT — 2026-09-22

## 1. Executive summary

Xninetzy today is a **455-tool MCP server** built on FastMCP, exposed via
`stdio` (primary) or Streamable HTTP (loopback-only by default). The host
owns reasoning; Xninetzy owns capability, replay-safety, idempotency,
owner identity injection, and approval gates. There is no server-side
agent loop.

Headline counts (from `get_tool_names()` and the filesystem):

| Item | Count |
|---|---|
| Registered MCP tools | **455** |
| Python source files | 485 |
| Test files | 215 |
| Skill directories (`/.agents/skills/`) | 83 |
| `SKILL.md` files | 122 |
| `/apps/docs` pages | 28 |
| Domains with ≥15 tools | 7 |
| FINAL-class tools (HITL-required) | 3 |

The headline **gap** is documentation drift: the deployed site and
several doc pages still claim 343–406 tools; the prior audit
(2026-09-20) flagged the same drift and it was not fixed.

The headline **strength** is breadth: 12+ shipped domains, real Kaggle
provider abstraction (3 providers), real Tableau pipeline
(parser → IR → compiler → validator → TWBX packager), real Obsidian
vault tools, real HEBAT/Moodle integration, real evaluation harness
with 11 evaluator primitives.

---

## 2. Current capability map

| Domain | Status | Tool count | Real? |
|---|---|---:|---|
| Research (27 adapters + 4 MCP tools) | IMPLEMENTED | many | yes |
| Career (17 tools) | IMPLEMENTED | 17 | yes |
| Knowledge (FAISS + Obsidian) | IMPLEMENTED | 7 | yes |
| Learning (roadmaps + mastery + SM-2) | IMPLEMENTED | 25 | yes |
| OS kernel (capture/inbox/triage) | IMPLEMENTED | 12 | yes |
| Lightning (CPU contextual bandit) | IMPLEMENTED | 19 | yes |
| Security (HITL + scope + SSRF + redaction) | IMPLEMENTED | 10 | yes |
| Improvement (proposals + evaluation) | IMPLEMENTED | 7 | yes |
| Memory (semantic + episodic + procedure + failure) | IMPLEMENTED | 13 | yes |
| Evaluation (audit/benchmark/hallucination/etc.) | IMPLEMENTED | 18 | yes |
| Data intelligence (profile/quality/xlsx/dashboard) | IMPLEMENTED | 7 | yes |
| Kaggle integration | IMPLEMENTED | 20 | yes (3 providers) |
| Tableau generator | IMPLEMENTED | 15 | yes |
| Process engineering (BPMN/XPDL/Bizagi) | IMPLEMENTED | 16 | yes |
| External MCP gateway | IMPLEMENTED | 5 | yes |
| HEBAT / Moodle | IMPLEMENTED | 15 | yes |
| Mahasiswa portal (Cyber Campus + KRS) | IMPLEMENTED | 21 | yes |
| UACC SSO | IMPLEMENTED | 6 | yes |
| QA kuesioner portal | IMPLEMENTED | 2 | yes |
| Web intelligence (search/fetch/evidence) | IMPLEMENTED | 14 | yes |
| YouTube search | IMPLEMENTED | 4 | yes |
| Obsidian (vault tools) | IMPLEMENTED | ~35 | yes |
| Reminders | IMPLEMENTED | 3 | yes |
| Personal OS (goals/tasks/money/habits/etc.) | IMPLEMENTED | ~20 | yes |
| Vision (OpenCV/PIL/OCR) | IMPLEMENTED | 7 | yes |
| Reasoning (depth/strategy/critique) | IMPLEMENTED | 10 | yes |
| Graph RAG (SQLite + V3 tri-store) | IMPLEMENTED | 14 | yes |
| Repo introspection | IMPLEMENTED | 8 | yes |
| HITL approval | IMPLEMENTED | 6 | yes |
| Documentation generators (ADR/record) | IMPLEMENTED | 4 | yes |
| Colab / Google Drive | MISSING | 0 | n/a |
| Database access (SQL/etc.) | MISSING | 0 | n/a |
| Statistical analysis (mean/median/regression) | MISSING | 0 | n/a |
| MCP Tasks extension (SEP-2663) | MISSING | 0 | n/a |
| Golden task suite | MISSING | 0 | n/a |
| Replay system | MISSING | 0 | n/a |

---

## 3. Where documentation disagrees with code

| Finding | Severity | Evidence |
|---|---|---|
| `mcp-system.md` says 406 tools | P0 | Runtime = 455 |
| `architecture.md` says 406 tools | P0 | Runtime = 455 |
| `audit-report-2026-09-20.md` said 385 tools | P0 | Runtime = 455 (drift grew) |
| `mcp-system.md` claims 4 `tasks_*` tools | P0 | Registry has 0 |
| `skills.md` says 78 skill dirs | P2 | Filesystem = 83 |
| `skills.md` says 116 SKILL.md files | P2 | Filesystem = 122 |
| `introduction.md` ships-domains table lacks Tableau | P1 | Tableau integration exists |
| `mcp.md`, `api.md`, `lightning.md` mention stale counts | P2 | various |

Prior audit (2026-09-20) flagged 4 P0 wrong-numbers findings. They were
**not fixed** before this audit ran; instead the drift grew from
385 → 455.

---

## 4. Findings (full set)

See `audit/findings.json` for the machine-readable form. Highlights:

- **F-001** Doc tool-count drift across every page. Fix via CI test.
- **F-002** Tableau not in `introduction.md` shipped-domains table.
- **F-003** `tasks_*` tools claimed in doc; 0 in registry.
- **F-004** `xninetzy/context/data_analysis/lineage.py` is dead code.
- **F-005** MCP annotations computed but never pushed to wire.
- **F-006** No CI verification of JSON Schema 2020-12 compliance.
- **F-009** Cross-integration Kaggle→Tableau chain lacks lineage.
- **F-010** No SEP-2663 Tasks extension.
- **F-011** Self-improvement patches not sandboxed.
- **F-012** No OpenTelemetry exporter wired.
- **F-013** No golden task suite.
- **F-019** 455 tools risks context-window saturation.

---

## 5. MCP conformance summary

- FastMCP server, stdio|streamable-http
- `stateless_http=True`, `json_response=True`
- Loopback-only enforcement for HTTP
- 2 resources, 1 prompt
- W3C traceparent + request_id ContextVar
- Pydantic-driven input schemas via langchain-core
- **Annotations computed but NOT pushed** (F-005)
- **No SEP-2663 Tasks** (F-010)
- **No JSON Schema 2020-12 CI gate** (F-006)

---

## 6. Workflow / state / task

- `xninetzy/workflow/` provides:
  - Deterministic planner (no LLM, keyword-based)
  - Executor with skip-on-cascade dependency
  - SQLite-backed store (`workflow_runs` + `workflow_action_runs`)
  - 4 user-facing tools: `workflow_status`, `workflow_latest`,
    `workflow_resume`, `workflow_cancel`
- States: `PENDING | RUNNING | SUCCESS | FAILED | SKIPPED`
- Mode: INLINE (per docstring — no background queue)
- **Gap:** no durable async task handles (SEP-2663)
- **Gap:** no checkpoint/resume at the action level for long-running ops

---

## 7. Data analysis engine

`xninetzy/context/data_analysis/` ships:

- `dataset.py`: format detection (CSV/TSV/XLSX/XLS/JSON/JSONL/Parquet/SQLite), SHA-256 checksum
- `profiling.py`: per-column physical_type + semantic_type (identifier/measure/temporal/categorical)
- `quality.py`: 4-dimension scoring (completeness/validity/uniqueness/consistency)
- `table_artifact.py`: openpyxl write + reopen-validate
- `dashboard/`: DashboardSpec + ProviderRouter (NativeEChartsProvider default)

**Missing:**

- Statistical analysis (mean/median/correlation/regression/ANOVA)
- Time-series analysis
- Sampling + memory estimation
- Streaming / chunked processing for large datasets
- DuckDB / Polars backend

---

## 8. Artifact + provenance

`TableArtifact` exists with `artifact_id`, `path`, `checksum`, `schema`,
`row_count`, `source`, `transformation`, `validation_status`.

**Gap (F-004):** `lineage.py` defines `LineageEdge` + `LineageRecord`
but is never called by `generate_xlsx_artifact` or any tool.

**Consequence:** Cross-integration workflows (Kaggle→Tableau) cannot
record provenance. The chain works by passing paths, not artifact IDs.

---

## 9. Security

**Implemented:**

- Chat-ID redaction (`xninetzy/core/security.py`)
- Secret redaction (regex over known patterns: sk-, AKIA, ghp_, etc.)
- 10 `security_*` tools for HITL-scoped pentest
- `safe_paths.py` per integration (Kaggle + Tableau tested)
- CAPTCHA auto-OCR with lockout (opt-in)
- mcp_principal injection strips trusted context from outputs

**Gaps:**

- No global path-traversal regression suite (F-015)
- SSRF guards partial (web_discover uses GET-only)
- Prompt-injection guard: trusted context stripping exists; no general
  content-source labeling

---

## 10. Observability

**Implemented:**

- W3C `traceparent` parsing
- `request_id` ContextVar
- `measure()` perf context manager (p50/p95/avg per label)
- 5 `observability_*` tools
- Lightning episode recording (every MCP tool call)

**Gaps:**

- No OTLP exporter (F-012)
- No Prometheus pull endpoint
- No log shipping

---

## 11. Evaluation harness

`xninetzy/context/evaluation/` provides 11 evaluator primitives:

- audit_trail, benchmark, context_eval, hallucination, memory_eval,
  outcome, root_cause, routing_eval, scoring, security, skill, tool

Exposed via 18 `evaluation_*` tools.

**Gaps:**

- No golden task suite (F-013)
- No replay system (F-020)
- No fault injection harness
- No security load test
- No performance benchmark suite

---

## 12. Self-improvement loop

**Implemented:**

- `improvement_*` (7): detect, propose, evaluate, approve, reject,
  regress, list
- `lightning_*` (19): full episode lifecycle + bandit strategy rank +
  regression check + rollback
- `learning_*` (25+): benchmarks, A/B tests, evolution proposals with
  stages (proposed → validated → approved → deployed → rejected)

**Gaps:**

- `lightning_approve` + `apply_proposal` are admin actions
  with no sandbox isolation (F-011)
- No automatic baseline capture before promotion
- No automatic rollback-on-regression
- No failure→regression-test auto-generation (F-016)

---

## 13. Kaggle integration (real, tested)

20 tools; 3 providers (API, CLI, Official MCP); capability map with
fallback; safe_paths with traversal check; tested in
`tests/integrations/kaggle/` (5 files).

**Status:** IMPLEMENTED. Opt-in via env vars.

---

## 14. Tableau integration (real, tested)

15 tools; pipeline:
`parse_workbook → TableauWorkbookIR → compile_workbook → validate_workbook → package_twbx`.

9 visualization types (bar/line/area/pie/scatter/table/map/kpi/histogram).
CSV datasource derivation via header inspection. Tested in
`tests/integrations/tableau/` (6 files).

**Status:** IMPLEMENTED. Template at `xninetzy/templates/tableau/Progres1ya.twb`.

---

## 15. Cross-integration audit

The headline workflow (Kaggle → Colab → Tableau) is **blocked**:

1. Kaggle download works → local CSV path.
2. Colab layer **does not exist** (F-018) — 0 colab_* tools.
3. Tableau works on local CSV → local TWB/TWBX.

What works without Colab: `kaggle_dataset_download` →
`compile_datasource_from_csv` → `tableau_workbook_generate` →
`package_twbx`. But no lineage recorded across the boundary (F-004).

---

## 16. Redundancy / delete candidates

| Item | Action |
|---|---|
| `audit-report-2026-09-20.md` (docs) | REMOVE after this report lands |
| Tool count mentions in 4+ docs | MERGE to scripts/mcp_audit.py |
| `tool_meta.py` annotations | MERGE into `mcp_tool_adapter.add_tool` call |
| `lineage.py` (unused) | KEEP + WIRE |

---

## 17. Target architecture (next phase)

Six of nine layers are already real:

```
MCP Interface       IMPLEMENTED
Discovery           PARTIAL  (capability layer missing)
Execution           PARTIAL  (no SEP-2663 Tasks)
Data                PARTIAL  (no statistical analysis)
Artifact            PARTIAL  (lineage not wired)
Evaluation          PARTIAL  (no golden/replay)
Improvement         PARTIAL  (no sandbox)
Governance          IMPLEMENTED
Integrations        PARTIAL  (no Colab/Drive, no DB)
```

Minimum target = 4 small additions:

1. CI doc-drift test (F-001)
2. Push MCP annotations (F-005)
3. Wire lineage into artifact pipeline (F-004 + F-009)
4. Statistical analysis tools (mean/median/correlate)

---

## 18. Implementation plan

| Order | Finding | Effort |
|---|---|---|
| P0 | F-001 CI doc drift test | S |
| P0 | F-005 push annotations | S |
| P0 | F-002 fix introduction.md | XS |
| P0 | F-003 fix or implement tasks_* | M |
| P1 | F-004 wire lineage | M |
| P1 | F-009 cross-integration artifact contract | M |
| P1 | F-012 OTLP exporter | M |
| P1 | F-015 global path-traversal regression | S |
| P1 | F-019 cap tool count via tool_route | M |
| P2 | F-013 golden task suite | L |
| P2 | F-016 failure→regression automation | M |
| P2 | F-011 sandbox self-improvement | L |
| P2 | F-018 Colab/Drive integration | XL |
| P2 | F-006 JSON Schema CI gate | S |

XS=trivially small, S=small, M=medium, L=large, XL=spans multiple PRs.

---

## 19. Regression suite (must remain passing)

The audit did NOT change any code. The following existing suites must
remain green:

- `tests/integrations/tableau/` (44 tests)
- `tests/integrations/kaggle/` (5+ tests)
- `tests/architecture/` (boundary enforcement)
- `tests/governance/` (skill frontmatter, MCP surface)
- `tests/process_engineering/` (BPMN round-trip)

---

## 20. Self-improvement loop status

| Stage | Status |
|---|---|
| OBSERVE | IMPLEMENTED (lightning episode + observability) |
| DETECT | IMPLEMENTED (improvement_detect) |
| CLASSIFY | IMPLEMENTED (evaluation_root_cause) |
| REPLAY | MISSING |
| CREATE REGRESSION | MANUAL (no auto-derivation) |
| CANDIDATE FIX | IMPLEMENTED (improvement_propose) |
| SANDBOX | MISSING |
| EVALUATION | IMPLEMENTED (evaluation_compare_benchmark) |
| BASELINE COMPARISON | IMPLEMENTED (lightning_regression_check) |
| SECURITY CHECK | IMPLEMENTED (evaluation_security) |
| PERFORMANCE CHECK | PARTIAL (perf snapshot) |
| APPROVAL | IMPLEMENTED (improvement_approve) |
| PROMOTE | IMPLEMENTED (apply_proposal via lightning) |
| MONITOR | IMPLEMENTED (lightning episode) |
| ROLLBACK | IMPLEMENTED (lightning_rollback_proposal) |

12 of 15 stages implemented; the 3 missing (REPLAY, SANDBOX, automatic
CREATE REGRESSION) are the load-bearing gap.

---

## 21. Files changed by this audit

- `audit/findings.json` (created)
- `audit/README.md` (this file, created)
- No source code modified.

---

## 22. Tests executed

This audit did not run tests. It is a read-only reconciliation.
Before acting on any finding, re-run:

```bash
uv run --no-project --directory . ruff check xninetzy tests
uv run --no-project --directory . pytest -ra
uv run --no-project --directory . python scripts/mcp_audit.py
uv run --no-project --directory . python scripts/verify_cpu_only.py
cd apps/docs && yarn check && yarn build
```

---

## 23. Known limitations of this audit

- **Deployed website (`https://xninetzy.vercel.app/`) could not be
  fetched** from this environment. Doc drift was measured against
  `/apps/docs/src/`, not the live URL.
- **No real Tableau Desktop** to confirm generated TWB renders.
- **No real Colab API access** (no allowlist).
- **No load test** executed.
- **No real Google OAuth** configured (Colab would need it).
- **Live MCP server** was not started; registry was read via
  `get_tool_names()` from the source tree.

---

## 24. Remaining unknowns

- Whether the deployed site has the same drift (cannot fetch).
- Whether any tool in the registry silently fails at runtime despite
  registering successfully.
- Whether the test suite passes (not run; previous summary says 184+ pass).
- Whether the `lightning_*` bandit strategy converges on real traffic.
- Whether `apply_proposal` has ever been invoked in production.

---

## Final note

Xninetzy is a **broad, real system** — not a stub MCP. The audit's
single most important finding is **F-001 (doc drift)**: the deployed
docs lie about tool count, and prior audits flagged the same issue
without remediation. The cheapest single fix is a CI test that
parses every doc page and asserts the runtime tool total.
