# Phase 1: foundational hardening batches

Date: 2026-11-10. Status: **PARTIAL phase, verified local batches; release NOT_READY**. Scope: existing runtime and contracts, no architectural replacement. [Phase 0](PHASE_0_REPORT.md) records the baseline; [test results](../audits/BASELINE_TEST_RESULTS.md) distinguish individual runs.

## Findings, implementation and verification

| ID | Current behavior change | Evidence | Status / remaining boundary |
|---|---|---|---|
| SEC-01 | Invalid explicit side-effect names now raise ValueError; pure policy returns BLOCK with invalid_side_effect | 28 new/updated regressions failed before; 90 invocation/policy/orchestrator + 16 reasoning-depth tests passed after | Fixed explicit malformed declaration path; omitted None and valid caller-declared read-only remain compatible and require canonical risk binding |
| SEC-04 | Redact nested credential-key values/text assignments and shared token patterns before telemetry truncation | Synthetic baseline 14 failures/1 pass; 39 combined redaction/Lightning tests pass, including persisted SQLite assertions | Fixed tested future event path; prior traces and other persistence hooks unchanged |
| SEC-05 | Reject existing pending idempotency reservation instead of executing again | Two failing deterministic tests before; 9 idempotency tests pass after | Stored results replay; crashes require reconciliation; no exactly-once external promise |
| SEC-06 | Resolve flat package root correctly; preserve legacy services/ai fixtures and explicit paths; refuse ambiguous existing store selection | Four original regressions fail before; 17 mapping tests pass after guard | No data moved; process environment must explicitly select store if sibling legacy DB exists, including when corrected env lookup discovers a different .env choice |
| AUD-01 | Strict audit checks required FINAL policies, approval/idempotency declarations and duplicate names; optional full inventory | Six regression tests fail before; 25 audit/manifest/registry tests pass after | Runtime enforcement and provider availability remain UNKNOWN |
| SKL-01 | Replace broad skill xfails with strict YAML, eligible runtime validation and explicit two legacy rejections | 14 focused tests pass; no xfail | No skills deleted, renamed or installed; nested metadata/routing issues remain |
| PKG-01 | Correct mandatory/optional dependency boundaries for minimal MCP bootstrap | Initial base wheel failed; 34 import/provider/vision/spreadsheet regressions pass; actual base wheel exposes/lists 571 tools and calls datetime with optional packages absent | Fixed minimal bootstrap; 49→64 distributions from existing dependency transitives; all 168 lock package identities/versions unchanged |

## Exact implementation files

Idempotency: `xninetzy/db/idempotency.py`, `tests/db/test_idempotency_store.py`.

Runtime mapping: `xninetzy/interfaces/mcp_runtime.py`, `tests/interfaces/test_mcp_runtime.py`.

Telemetry: `xninetzy/os/lightning/rl.py`, `tests/os/lightning/test_input_redaction.py`.

Policy: `xninetzy/context/invocation/classify.py`, `xninetzy/context/policy/gate.py`, `tests/invocation/test_invocation_contract.py`, `tests/policy/test_policy_gate.py`, `tests/orchestrator/test_orchestrator_pipeline.py`.

Audit: `scripts/mcp_audit.py`, `tests/tools/test_mcp_audit.py`, `docs/audits/TOOL_INVENTORY.md`, `docs/audits/tool_inventory.json`.

Skill evidence: `tests/governance/test_skill_frontmatter.py`, `tests/os/skills/test_skills.py`, the instruction/skill/context reports linked from Phase 0.

Minimal dependencies: `pyproject.toml`, `uv.lock`, `xninetzy/core/llm.py`, `xninetzy/tools/ecosystem/vision_tools.py`, `xninetzy/context/data_analysis/profiling.py`, `xninetzy/context/data_analysis/table_artifact.py`, `tests/architecture/test_minimal_dependencies.py`.

CI: `.github/workflows/quality-gates.yml` now runs critical execution regressions and canonical prompt validation, plus a separate frozen base-only installed-wheel smoke outside the checkout. YAML parses; the exact smoke step was executed locally with the isolated installed interpreter and passed (571 tools + safe read). Remote Actions and Python 3.11 execution remain unverified in this environment.

## Contracts, compatibility and state

No public tool was added, deleted or renamed. No database schema migration, owner configuration installation or production data change occurred. Invalid explicit side-effect declarations intentionally stop being accepted; valid normalized classes and omitted legacy classification retain behavior. Idempotency keeps its existing `(scope,key,payload)` identity; changed payloads remain separate executions until a separately designed compatibility change. Ordinary callable exceptions still release reservations, so callers must reconcile external uncertain delivery rather than blindly retry.

Path correction intentionally refuses an ambiguous host restart rather than selecting a different existing database. This can require an explicit process setting before restart. It never chooses a database by size/mtime or copies/migrates data. Installed package path behavior and legacy paths have separate tests.

The dependency correction reuses an already-supported library; provider/embedding/browser/document extras stay optional. Installed package versions in the lock are preserved; only dependency ownership changes. CPU/RSS/latency improvements from lazy imports are NOT_MEASURED.

## Performance and limitations

The verified benefits are prevented duplicate execution in concurrency fixtures, blocked malformed-class invocation, removed synthetic secret persistence and successful invariant checks. Before/after runtime throughput, production incidence and end-user completion gains are NOT_MEASURED. [Performance baseline](../evaluation/PERFORMANCE_BASELINE.md) contains a single-process smoke, not a speedup comparison.

Open release blockers include approval authenticity and single-use consumption, caller-controlled valid risk declarations, obsolete container entrypoint/health contract, graph false acknowledgements, and unexecuted full release acceptance. Full repository Ruff reports 125 findings outside this focused batch. No failures were hidden through new skips or xfails.

## Rollback and next priorities

Review/reverse only these source/test hunks; preserve initial user deletions/untracked directories. No database rollback is needed. Reverting security fixes restores the reproduced failures and should require deliberate review. Never remove pending reservations without reconciling their effects. Restore dependency manifest and lock together if reverting packaging changes.

Next: independent exact approval verification and atomic consumption; canonical risk at execution; then deployment and truthful workflow/graph recovery. Keep release NOT_READY until those boundaries have sufficient acceptance evidence.

## Final foundation checkpoint

Combined foundation/domain/contract run: **411 passed in 108.92s**, no failed/skipped/xfail reported. This includes the earlier suite selections plus all new malformed-class, reasoning and minimal-import tests and existing provider factory tests. Separate image/spreadsheet/optional import run: **34 passed in 10.21s** (overlaps the combined run; do not add counts). Subsequent workflow/graph batches are recorded separately in Phase 3 and require their own final regression.

Strict audit and regenerated-schema comparison confirm all **571** saved inventory rows match current registry declarations. All six installed shared/client instruction hashes still equal the initial snapshot. Focused Ruff, shell syntax and diff whitespace checks pass; full Ruff remains **125 findings**. No full-suite or release-green claim follows from this checkpoint.
