# Xninetzy OS Unified Access and Grounding Plan

Last updated: 2026-08-01

This is the execution tracker for turning Xninetzy from a feature-rich assistant
into one OS shared by WhatsApp, internal LangGraph, Codex, Claude Code, and
OpenCode.

The Cyber Campus KRS, grades, and WhatsApp verification extension is tracked in
`docs/plan/CYBER_CAMPUS_KRS_GRADES_WHATSAPP_PLAN.md`. Portal writes remain
disabled until its read-only and approval-hardening gates are implemented.

## Architecture decision

All interfaces use the central Xninetzy tool registry and the same persisted OS
state. MCP stdio represents the trusted local owner. WhatsApp retains the real
sender context. External coding runtimes started from WhatsApp must pass an MCP
preflight and receive the repository OS contract in their task prompt.

Knowledge requests use:

`hybrid retrieval -> evidence selection -> bounded context -> synthesis -> citation validation`

Raw search output is never considered a final answer.

## Current implementation

- [x] Registry tools are exposed dynamically through stdio MCP.
- [x] MCP host/container path bootstrap uses the same SQLite and data directory.
- [x] Codex, Claude Code, and OpenCode coding runtime adapters exist.
- [x] WhatsApp `/agent` and `/code` select and run guarded coding runtimes.
- [x] Trusted local-owner MCP principal is injected server-side.
- [x] Identity/context arguments are hidden from dynamic MCP tool schemas.
- [x] Coding runtime task prompt requires `AGENTS.md` and Xninetzy MCP usage.
- [x] Coding runtime fails closed when MCP preflight does not find `xninetzy`.
- [x] Hybrid FAISS + FTS retrieval uses reciprocal-rank fusion.
- [x] Evidence bundles are deduplicated, bounded, labelled, and citation-addressable.
- [x] `knowledge_answer` performs synthesis and citation validation.
- [x] LangGraph routes relevant knowledge requests through the grounded agent path.
- [x] FAISS cold-start mapping and persisted map/vector invariant are repaired.
- [x] Agent Skills are dynamically discovered and injected into LangGraph and
  exposed through the same MCP tools for Codex, Claude Code, and OpenCode.
- [x] WhatsApp coding-agent and chat-failover execution is routed through an
  authenticated host bridge instead of running CLI binaries in Docker.

## P0 — Trust and reliability

- [x] Require service-to-service authentication on `/api/chat` and send the
  bearer token from WA engine and CLI.
- [x] Default debug endpoints to disabled and protect them with API auth.
- [x] Enforce owner JIDs before chat tools or LangGraph in single-owner mode.
- [x] Add durable WhatsApp message deduplication and a per-chat serial queue.
- [x] Add a durable prepared-reply outbox to avoid repeated LLM/tool execution.
- [x] Add verified backup/restore commands for SQLite and FAISS state. Secrets
  and deployment configuration are intentionally excluded.

Acceptance:

- The same WA message delivered three times causes one tool execution and reply.
- A non-owner cannot read or mutate vault, HEBAT, knowledge, or Life OS state.
- Restart before reply delivery does not repeat LLM/tool side effects. A crash
  after WhatsApp accepts a send but before its completion record is persisted
  can still repeat the outbound message; provider-level idempotency is unavailable.
- `faiss.ntotal == len(faiss_map)` after ingest, restart, and rebuild.

## P1 — Closed-loop Personal OS

- [x] Formalize domain state as installation-global in single-owner mode;
  `chat_id` records origin and conversation memory, not entity ownership.
- [x] Consume ecosystem events through idempotent, replayable reducers.
- [x] Link HEBAT assignment -> shared task -> deadline reminder.
- [x] Link task completion -> goal and roadmap progress.
- [x] Include roadmap, habit, workout, and recent events in Personal Context v2.
- [x] Build idempotent morning briefing, evening check-in, and weekly review jobs.
- [x] Add periodic HEBAT sync with freshness and failure status.
- [x] Add an installation-global OS Inbox for ambiguous capture.
- [x] Add atomic, replay-safe triage from capture to shared task or archive.
- [x] Replace `/today` with a deterministic attention queue across task,
  learning state, and pending capture.
- [x] Inject the same attention state into LangGraph context and automation.

Acceptance:

- Completing a linked task updates the associated roadmap or goal.
- A briefing is generated at most once per owner/date and identifies stale data.
- Weekly review uses actual events instead of a static question template.
- The same capture key produces one inbox item and one lifecycle event.
- Replaying triage produces no duplicate task, link, or reducer consumption.

## P2 — Adaptive Learning OS

- [x] Replace the fixed 14-day roadmap template with a source-aware planner.
- [x] Implement study sessions and progress tracker modules.
- [x] Model prerequisite, concept, milestone, task, session, evidence, and mastery relationships.
- [x] Add deterministic active recall and spaced repetition scheduling.
- [ ] Adapt the daily plan to mastery, available time, energy, and deadlines.
- [ ] Add a retrieval evaluation set for ranking, groundedness, and citations.

Acceptance:

- Seven-, fourteen-, and thirty-day roadmaps differ structurally.
- Every internal-knowledge claim cites a real evidence ID.
- Today plan changes after a study session or mastery update.

## P3 — Production hardening

- [ ] Replace inline long workflows with a durable worker and leases.
- [ ] Supervise background loops and support graceful shutdown.
- [ ] Add metrics for WA delivery, routing, retrieval, tools, reminders, and jobs.
- [ ] Add CI for Python, WA engine, CLI, docs, secret scanning, and Compose config.
- [ ] Run documented backup/restore and workflow-resume drills.

## Runtime-03 — Host coding bridge and cross-client skills

- [x] Force Docker MCP persistence paths to `/app/data` even when the shared
  `.env` contains host paths.
- [x] Add authenticated host bridge endpoints for `/code` and read-only chat
  failover with bounded payloads and workspace guards.
- [x] Add Linux systemd user installer so the bridge starts automatically.
- [x] Remove coding CLI installation from the AI Docker image.
- [x] Keep dynamic skills in the shared Agent Skills catalog and expose them
  through the canonical MCP registry.
- [x] Verify production MCP configuration for Codex, Claude Code, and OpenCode
  on the target host without exposing credentials.

## Change log

### 2026-07-29

- Added installation-global entity links shared by WA, MCP, and LangGraph.
- Projected activated roadmap tasks and HEBAT assignments into shared Life OS tasks.
- Added idempotent task-completion reducer for goal and roadmap progress.
- Added reducer replay on AI startup and Personal Context v2 signals.
- Added leased scheduled jobs with at-most-once WhatsApp delivery tracking.
- Added event-backed morning/evening/weekly messages and inspectable HEBAT freshness.
- Added duration/level-aware roadmap phases and persisted knowledge source links.
- Added idempotent study sessions, progress metrics, and mastery/energy adaptive daily plans.
- Added a shared OS Inbox, atomic triage, and deterministic attention queue.
- Routed `/today`, Personal Context, morning briefing, and MCP through the same OS state.
- Added a replay-safe concept graph linked to roadmap milestones, tasks, study
  sessions, evidence, mastery, today planning, review, Personal Context, and MCP.
- Added recall cards, keyword-based grading, confidence tracking, SM-2 scheduling,
  and atomic mastery evidence shared across WhatsApp, LangGraph, and MCP.
- Added an admin-only WhatsApp startup menu with 15 command buttons, reconnect
  deduplication, and complete text fallback.

### 2026-07-28

- Established shared MCP owner identity and schema-level context injection.
- Added coding-runtime MCP preflight and Xninetzy OS task contract.
- Added hybrid retrieval, evidence bundling, grounded synthesis, and citations.
- Added deterministic auto-ground routing for relevant LangGraph requests.
- Added root `AGENTS.md` and this implementation tracker.
- Protected AI routes with fail-closed bearer auth and explicit owner scope.
- Added durable WA processing claims, per-chat ordering, and prepared replies.
- Added checksum-verified SQLite/FAISS backup and explicit restore tooling.
