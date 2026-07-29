# Xninetzy OS Implementation Progress

Last updated: 2026-07-29

This log tracks implementation batches from
`docs/plan/XNINETZY_OS_UNIFIED_ACCESS_PLAN.md`. A batch is complete only after
code, tests, configuration, and documentation agree.

## Summary

| Batch | Scope | Status | Verification |
|---|---|---|---|
| Foundation-01 | Shared MCP principal, coding-agent preflight, grounded retrieval | Complete | 264 AI tests; WA/docs builds |
| P0-01 | API authentication and single-owner request boundary | Complete | 5 focused API tests; AI lint |
| P0-02 | Durable WA deduplication, per-chat queue, prepared-reply outbox | Complete | 6 WA tests; TypeScript build |
| P0-03 | Verified SQLite/FAISS backup and restore | Complete | 2 backup tests; AI lint |
| P1-01 | Event reducers, entity links, and Personal Context v2 | Complete | 31 focused + 264 full AI tests; focused lint |
| P1-02 | Scheduled briefing/review and HEBAT freshness worker | Complete | 6 scheduler + 29 parity + 264 full AI tests |
| P2-01 | Duration/level/source-aware roadmap planner | Complete | 21 focused + 264 full AI tests; focused lint |
| P2-02 | Study sessions, progress metrics, and adaptive today plan | Complete | 21 focused + 271 full AI tests; focused lint |
| Security-02 | Per-installation runtime data isolation | Complete | Git tracked-file audit; docs build |
| Academic/Telegram plan | Cyber Campus KRS, grades, and owner Telegram bridge | Planned | Design only; no actions enabled |

## Batch P0-01 — API authentication and owner boundary

Started: 2026-07-28

- [x] Protect chat, reminders, and debug routes with the AI API key.
- [x] Send bearer auth from WA engine and CLI.
- [x] Disable debug endpoints by default.
- [x] Enforce configured owner JIDs before tools or LangGraph run.
- [x] Add tests and documentation.

## Batch P0-02 — WhatsApp replay safety

- [x] Durable processing claims keyed by chat and message ID.
- [x] Lease recovery for interrupted processing.
- [x] Durable `reply_ready` state to avoid repeated LLM/tool calls.
- [x] Per-chat serial execution with cross-chat concurrency.
- [x] Retention, retry, and queue-order tests.

Known boundary: if the process dies after WhatsApp accepts a send but before the
completion record is flushed, the reply may be resent. The LLM/tool phase is not
repeated. Closing this final window needs an upstream idempotency primitive or a
delivery reconciliation protocol.

## Batch P0-03 — Backup and restore

Completed: 2026-07-28

- [x] Use SQLite online backup instead of copying a live WAL database.
- [x] Include FAISS index/map when present.
- [x] Write SHA-256 manifest and verify before restore.
- [x] Require explicit restore confirmation and atomic target replacement.
- [x] Apply retention and exclude backup data from Git.
- [x] Document operator workflow and recovery drill.

Secrets, `.env`, browser sessions, WhatsApp sessions, downloads, and vault files
are excluded by design and need their own encrypted backup policy.

## Batch P1-01 — Closed-loop shared OS

Completed: 2026-07-29

- [x] Formalize Life OS and Learning OS state as installation-global for the
  trusted single owner; retain `chat_id` only for origin/delivery/memory.
- [x] Add generic, unique entity links shared across interfaces.
- [x] Project approved learning-roadmap items into shared tasks exactly once.
- [x] Project HEBAT assignments into shared tasks and link deadline reminders.
- [x] Consume `task_completed` events transactionally and exactly once.
- [x] Advance linked goal values, learning task progress, milestones, and roadmap status.
- [x] Replay unconsumed events at AI startup.
- [x] Add roadmap, habit, workout, and cross-interface recent events to Personal Context v2.

## Batch P1-02 — Durable automation

Completed: 2026-07-29

- [x] Persist unique job keys, status, attempts, leases, outputs, and errors.
- [x] Reclaim interrupted internal jobs only after lease expiry.
- [x] Generate morning briefing from task/deadline/roadmap/freshness state.
- [x] Generate evening check-in and weekly review from persisted events.
- [x] Track WhatsApp delivery at-most-once and surface ambiguous delivery.
- [x] Run optional periodic HEBAT sync with persisted retry backoff.
- [x] Expose job/freshness status through the shared registry and MCP.
- [x] Add startup grace period so WA engine can establish its socket first.

Periodic HEBAT sync remains opt-in (`HEBAT_PERIODIC_SYNC_ENABLED=false`) because
it uses an authenticated institutional session. A `delivery_uncertain` job is
never retried automatically; inspect WhatsApp and the status tool first.

## Batch P2-01 — Source-aware adaptive roadmap

Completed: 2026-07-29

- [x] Produce structurally different 7-, 14-, and 30-day roadmaps.
- [x] Cover every day deterministically with bounded phases and outcomes.
- [x] Adapt the first phase/tasks for beginner, intermediate, and advanced levels.
- [x] Resolve optional source IDs or relevant internal knowledge sources.
- [x] Deduplicate and bound source references.
- [x] Persist source references as roadmap metadata and `learning_resources`.
- [x] Disclose when the roadmap has no validated internal source.

## Batch P2-02 — Study session and progress tracking

Completed: 2026-07-29

- [x] Replace the study-session and progress-tracker placeholders.
- [x] Enforce one active owner session and accept stable idempotency keys.
- [x] Persist planned/actual duration, energy, mastery, reflection, and evidence.
- [x] Write completion progress and ecosystem event atomically and exactly once.
- [x] Adapt today plan across start, resume, reinforce, practice, and advance modes.
- [x] Include adaptive focus in Personal Context for internal LangGraph.
- [x] Expose the same tools through the central registry and dynamic MCP adapter.

Next P2 work: prerequisite/concept/mastery relationships, active recall and
spaced-repetition scheduling, deadline-aware plan adaptation, and retrieval evals.

## Batch Security-02 — Open-source local data isolation

Completed: 2026-07-29

- [x] Treat SQLite as private state created independently for every clone.
- [x] Ignore all `services/ai/data/**` runtime artifacts by default.
- [x] Keep only a tracked data-policy README.
- [x] Remove SQLite WAL/SHM, FAISS, HEBAT browser state, and generated analysis from Git tracking.
- [x] Document encrypted backup migration and Git-history sanitization.

This removes runtime files from the current repository tree. Existing public Git
history must still be sanitized separately; history rewrite is intentionally not
automated because it affects every collaborator.
