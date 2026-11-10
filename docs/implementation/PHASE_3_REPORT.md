# Phase 3: truthful workflow and projection outcomes

Date: 2026-11-10. Status: **PARTIAL phase**. These batches improve existing execution/persistence behavior. They do not create a new orchestrator or establish complete restart/resume safety.

## Workflow outcome correction

VERIFIED_CODE: `WorkflowExecutor` previously assigned overall SUCCESS whenever execution did not stop on a critical failure, even if noncritical actions failed or skipped. Its text already said the workflow completed partially, so persisted status and visible evidence disagreed.

Tests were updated/added before implementation: **4 failed, 3 passed** in the executor suite. Aggregate status now uses existing FAILED whenever any executed result is not SUCCESS. Successful actions still run/are retained, noncritical continuation is preserved, and existing partial response text remains. No new enum value or schema migration is introduced.

The new regression writes a real temporary SQLite workflow and checks both stored status/result JSON and retained successful steps. A preexisting reminder fixture omitted academic detail/download handlers yet expected aggregate SUCCESS. It was corrected to explicitly assert those two SKIPPED outcomes, aggregate FAILED, successful REMINDER_INFER and a genuinely persisted pending reminder. This strengthens the original reminder assertions rather than removing the case or masking a product failure.

Files: `xninetzy/workflow/executor.py`, `tests/workflow/test_workflow_executor.py`, `tests/workflow/test_workflow_reminder.py`. Compatibility: consumers that previously interpreted partial execution as SUCCESS now receive the existing FAILED value; partial completion details remain in per-step results/text. This intentional behavior correction must not be mistaken for durable recovery or policy enforcement.

Remaining workflow limits: dependency skipping is not a general validated DAG scheduler; generated placeholder academic steps and continuation semantics need a separate product decision; persistence errors, pending approvals and restart replay still require acceptance tests. No external academic operation ran in these fixtures.

## Projection acknowledgement batch

VERIFIED_CODE: the worker ignored False acknowledgement and marked SQLite projection sync/outbox completion despite Neo4j failure. Tests first reproduced **10 failures / 2 passes**. Enabled projection writes/deletes now require acknowledgement before reporting success; failures enter the existing outbox failed/backoff path. FAISS is still attempted independently for node upserts. Disabled Neo4j remains optional, is not invoked, and does not get a synchronized timestamp.

A prerequisite retry defect was also reproduced: exhausted rows had `next_retry_at=NULL`, which the claim query interpreted as ready immediately. A dedicated real temporary SQLite test failed before the correction. Claiming now filters `attempts < GRAPH_SYNC_MAX_ATTEMPTS` across pending, failed and expired-processing branches. Exhausted rows remain inspectable; no rows are reset/deleted and no rebuild is automatic.

Final expanded projection suite: **19 passed in 21.35s**. The earlier existing graph suite with the initial projection cases: **36 passed in 40.06s**, with one preexisting embedding FutureWarning; counts overlap and must not be added. Workflow suite: **30 passed in 1.73s**. Scoped Ruff and diff whitespace checks pass.

Files: `xninetzy/os/graph/v3/projection_worker.py`, `xninetzy/os/graph/v3/sqlite_store.py`, `tests/os/graph/test_projection_worker.py`. CI now includes graph and workflow regression directories in the critical execution step. No live Neo4j, destructive projection rebuild, schema migration, new dependency or owner database change occurred.

Limits: disabled Neo4j work is drained for configured projections and leaves its sync timestamp unset; enabling it later requires an explicit resync. Exhausted rows need deliberate reconciliation; simply restoring connectivity does not reset attempts. FAISS may append duplicate vectors during bounded retries under its existing API. General projection consistency, edge-deletion semantics and whole-index reconciliation are not established by these tests. None of this proves live graph availability or exact-once external projection effects.

## Rollback

Reverse only the reviewed workflow/projection hunks and tests if required; no data migration is needed. Restoring the old status behavior restores false success. Existing stored historical workflow statuses are not rewritten. No failed graph rows are deleted/reset automatically; recovery must preserve canonical SQLite and existing approvals.

## Final integrated verification

**476 passed, 1 warning in 162.36s** in the final combined foundation, policy, workflow, graph, knowledge/memory, minimal-import, provider, vision and spreadsheet regression run. No failed/skipped/xfail reported. This is a selected local suite, not all collected tests or live provider acceptance. One preexisting embedding-method FutureWarning remains visible. Every changed Python file passes scoped Ruff; global Ruff remains 125 findings. Diff whitespace, shell syntax, CI YAML and report links pass. The CI installed-wheel smoke was also executed locally and lists 571 tools plus a successful safe read.

Measured production task success, runtime CPU/RSS improvement, citation quality and cross-client parity remain NOT_MEASURED/NOT_VERIFIED. Highest next work: exact approval authenticity/atomic consumption and canonical risk binding, then corrected container deployment and safe durable resume. Current release decision stays NOT_READY.
