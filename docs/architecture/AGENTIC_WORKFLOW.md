# Durable recovery in the existing workflow engine

Verified scope: single-owner, local POSIX filesystem/SQLite, 2026-11-15. This extends `xninetzy/workflow/`; it is not another orchestrator, queue or agent framework. Domain outcome verification and independent consequential approval remain separate release gates.

## Execution contract

```mermaid
flowchart LR
    A[Exact persisted plan] --> B[Owner and effective policy]
    B --> C[Nonblocking local workflow lock]
    C --> D[Validate version, plan hash and state]
    D --> E[Reuse completed results]
    E --> F[Persist RUNNING before handler]
    F --> G[Execute one bounded logical step]
    G --> H[Commit result and working state atomically]
    H --> I[Optional progress notification]
    I --> J[Next step or final result]
```

Plans remain ordered, with existing noncritical-failure continuation semantics. Unknown/forward dependencies, duplicate step IDs and plans exceeding `WORKFLOW_MAX_ACTIONS` are held. This is not a new parallel DAG scheduler. The `XNINETZY_TOOL_TIMEOUT_SECONDS` budget is cooperative: no new step begins after expiry; an already executing operation may finish and its evidence must still be committed. It is not a promise to kill synchronous work or enforce a provider deadline externally.

Persisted execution and resume respect effective owner write policy and kill switch. The default approval mode is preserved; synthetic fixtures explicitly permit local automatic writes. The workflow's supported action types do not grant permission to perform FINAL institutional operations. Retrieved text, working memory, a plan hash and a checkpoint are never approval evidence.

## Canonical state and boundaries

Existing `workflow_runs.result_json` contains `WorkflowExecutionResult` with an optional version1 `WorkflowCheckpoint` (`plan_hash`, typed `WorkflowState`). Existing `workflow_action_runs` receives step input/result/timestamps; new ledger keys hash the workflow/step pair without deleting historical rows. Plan/status/result/state and the current step record are updated in one short SQLite transaction. No new table, column or destructive migration is required.

Owner, plan ID and original objective are immutable execution context. They are checked before persistence and before further effects. Immutable plan fields bind to a deterministic hash; mutable status/summary/error fields are excluded. This hash detects inconsistent snapshots, not a cryptographically authenticated writer with database-write privilege. The owner-controlled canonical SQLite store remains trusted state.

Working state and result fields are sanitized before persistence; sensitive initial plan content is held rather than silently rewritten and executed. The owner identity remains the trusted scope field. Intermediate checkpoint envelopes are capped at256KiB; final response text is also subject to the MCP output boundary. This is bounded workflow state, not permanent semantic memory or a transcript/reasoning store. Known-pattern/key redaction is not universal data-loss prevention. Results are validated and sanitized before progress notifications, and unexpected handler/notification errors log only exception types.

## Recovery decisions

| Persisted condition | Behavior |
|---|---|
| Successful completed step | Reuse its stored result and working state; do not invoke handler/notification again |
| Whole run completed | Return clearly labelled stored output; do not regenerate plan or reverify live artifacts |
| Failed/interrupted read-oriented step | Retry only a fixed server-owned whitelist, under current policy and new attempt budget |
| Failed/interrupted mutation | Hold with `workflow_uncertain_outcome_reconcile`; inspect canonical state/receipt before any new authorized operation |
| Retry would invalidate an already successful dependent action | Hold for review; do not repeat the successful mutation |
| Missing legacy state, changed plan, unsupported/corrupt checkpoint | Hold, preserving rows; never rebuild from the old message |
| Concurrent same-ID execution | Return in-progress hold; no concurrent effect |
| Persistence failure before effect | Stop before handler |
| Persistence failure after effect | Retain RUNNING/uncertain evidence; stop before any further step |
| Cancellation | Preserve completed evidence, stop future unclaimed steps; in-flight work may finish |

The retry whitelist is explicit: reminder listing, final synthesis, web/YouTube/paper search and academic course/assignment detail reads. Some perform idempotent local cache refresh. Deep research, planning, memory, note writes and other mutations are not blindly retried. There is one attempt per eligible step per explicit resume, not an autonomous unbounded retry loop. Current domain handlers can still report semantic success incorrectly; a stored SUCCESS does not substitute for a domain verifier.

Successful results remain in a checkpoint even if a different retry is interrupted again. Final cancellation is serialized with step claims/final commits so status and returned result cannot overwrite a winning cancellation. Failed workflows can also be cancelled to prohibit future resume. Existing strings/parameters of `workflow_resume`, `workflow_status` and `workflow_cancel` remain; `cancelled` is an additive internal/result status.

## Concurrency and deployment

An advisory lock under the selected database directory's `.workflow-locks/` is held for a run. Lock names hash the workflow ID; directory symlinks and symlink lock files are refused. Files are created with restrictive modes and never unlinked during normal execution. The last descriptor closing releases the lock; no network call runs under a SQLite write transaction. This uses [Python's Unix locking interface](https://docs.python.org/3/library/fcntl.html) alongside [SQLite transactions](https://www.sqlite.org/lang_transaction.html).

This assumes a trusted local data directory and cooperating updated runtimes. Non-POSIX systems fail closed for durable workflows while unrelated MCP capabilities remain independent. Multi-host/NFS locking, hostile same-owner processes and mixed old/new executors are not covered. Do not hot-roll the feature across active old workflow workers: old code can rebuild and replay regardless of the new lock. All clients must point to the same canonical owner store and deliberately reconnect to updated source after active work is reconciled.

## Verification and rollback

`tests/workflow/test_workflow_recovery.py` includes actual fixture-process SIGKILL during a read and during a write, real SQLite checkpoint/commit failures, concurrency, cancellation races, owner/objective corruption, symlink rejection, privacy and policy tests. `scripts/smoke_workflow_recovery.py` seeds synthetic SQLite writes in a separate process context, then resumes through actual MCP using canonical local reminder reads/final synthesis. It checks stable workflow IDs, unchanged completed-write ledger, completed replay and uncertain-write denial. No owner database, session or portal is used.

See [Phase3](../implementation/PHASE_3_REPORT.md) for exact counts/image/commands. Old records remain recoverable for inspection; records without checkpoint state are intentionally held. Back up/reconcile before any owner rollout. Do not remove reservations, edit status to force success, delete lock files while a participant could hold them, or downgrade to the previous replaying resume implementation against active state. Older readers may not understand checkpoint/cancelled results; rollback requires preserving data and holding resume until a reviewed compatible runtime is in place. No external exactly-once or general production-readiness claim follows.
