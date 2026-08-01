# Xninetzy OS Implementation Progress

Last updated: 2026-08-01

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
| P1-03 | OS Inbox, replay-safe triage, and shared attention queue | Complete | 15 focused + 307 full AI tests; full lint; WA/docs/runtime gates |
| P2-01 | Duration/level/source-aware roadmap planner | Complete | 21 focused + 264 full AI tests; focused lint |
| P2-02 | Study sessions, progress metrics, and adaptive today plan | Complete | 21 focused + 271 full AI tests; focused lint |
| P2-03 | Concept/prerequisite graph and evidence-backed mastery | Complete | 23 focused + 354 full AI tests; Ruff; docs build |
| P2-04 | Active recall and bounded spaced repetition | Complete | 34 focused + 365 full AI tests; Ruff; docs build |
| Security-02 | Per-installation runtime data isolation | Complete | Git tracked-file audit; docs build |
| Academic-01a | Cyber login, CAPTCHA HITL, encrypted session, runtime navigation | Partial | 315 full AI tests; 27/27 safe unique routes reachable |
| WA-Approval-01 | Admin buttons, media forwarding, LID normalization | Complete | 11 WA tests; 6 AI notification/media tests; TypeScript lint/build |
| WA-Menu-01 | Admin startup menu with 15 buttons and fallback | Complete | 20 WA tests; lint/build; live 5-card/15-button delivery |
| Runtime-01 | Fixed Playwright Docker layer and laptop boot restart | Complete | Docker images built; both services healthy; Docker enabled/active |
| Academic-01b | Typed Cyber Campus reads + private WhatsApp grade-token reader | Partial | 346 AI tests; live profile/status/10 KRS rows; offering model pending |
| Runtime-02 | Cross-platform bridge Compose + bootstrap installers | Complete | Compose config; Bash syntax; Docker health; docs build |
| Runtime-03 | Host coding bridge, Docker path isolation, and cross-client skills | Complete | Docker import; host bridge health/auth; Codex, Claude Code, and OpenCode MCP smoke; focused tests |
| Academic-01c | Shared academic credentials, live session validation, and QA CAPTCHA handling | Complete | 20 focused login tests; Ruff; live QA rejection classified for human verification |
| Reliability-01 | Graph path mapping, Flaz thinking guard, skill ranking, and inbox triage | Complete | 27 focused tests; GraphRAG host smoke; provider error diagnosis |
| Academic-01d | QA standard-browser login and HEBAT Moodle upload smoke | Complete | QA headed login live; HEBAT overdue assignment verified `Submitted for grading`; uploader selector fix |
| Academic-01e | Academic parser hardening, grade snapshot idempotency, and KRS watcher timing | Complete | 31 focused academic tests; Ruff; hash regression X→Y→X; adaptive watcher intervals |

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

## Batch P1-03 — OS Inbox and attention kernel

Completed: 2026-07-29

- [x] Add an installation-global inbox for important, ambiguous capture.
- [x] Classify capture deterministically without another LLM call.
- [x] Make capture idempotent by caller-supplied key.
- [x] Promote capture to a shared task or archive it in one transaction.
- [x] Persist exactly one entity link, lifecycle event, and reducer consumption.
- [x] Replace `/today` with a deterministic attention queue across tasks,
  learning state, and pending capture.
- [x] Inject the same attention state into Personal Context and morning briefing.
- [x] Expose the four OS tools through the central registry and dynamic MCP.
- [x] Document the behavior and known boundaries in Astro docs.
- [x] Finish the full AI, WA, docs, Docker, and MCP verification gates.

Verification: 15 focused OS tests, 307 full AI tests, full Ruff, 11 WA tests,
WA lint/build, Astro check/build with 21 pages, healthy Docker services, and a
runtime registry/schema smoke check.

Next OS-kernel work should add typed promotion adapters for note, knowledge,
goal, and roadmap without moving domain behavior into the interface layer.

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

## Batch P2-03 — Concept graph and evidence-backed mastery

Completed: 2026-07-29

- [x] Persist concepts scoped to a roadmap with stable derived identity.
- [x] Link concepts to prerequisite concepts, milestones, tasks, and study sessions.
- [x] Reject self-dependencies, cross-roadmap links, and prerequisite cycles.
- [x] Seed new roadmaps and idempotently backfill existing local roadmaps.
- [x] Persist evidence with idempotency key and payload mismatch protection.
- [x] Update mastery deterministically and unlock the next ready concept.
- [x] Record study-session mastery as concept evidence in the same transaction.
- [x] Include weak concepts in today planning, weekly review, and Personal Context.
- [x] Expose define, evidence, and concept-map tools through the registry and MCP.
- [x] Route `/concepts <roadmap-id>` to the shared read tool.

Next P2 work: richer quizzes, deadline-aware planning, and retrieval evaluation
datasets.

Verification: 23 focused concept/study/parity tests, 354 full AI tests, full
Ruff, Astro check/build with 21 pages, and replay-safe migration coverage.

## Batch P2-04 — Active recall and bounded spaced repetition

Completed: 2026-07-29

- [x] Persist immutable recall cards and replay-safe attempts with payload hashes.
- [x] Scope every card to an existing roadmap concept.
- [x] Derive explicit, deterministic keyword evidence instead of asking an LLM
  to grade recall.
- [x] Keep self-reported confidence separate from answer quality.
- [x] Apply bounded SM-2 scheduling with lapse tracking and a minimum ease factor.
- [x] Hide expected answers until the owner submits an attempt.
- [x] Update the recall schedule, concept evidence, mastery, and lifecycle event
  atomically.
- [x] Prioritize an active study session first and due recall before starting a
  new session.
- [x] Include due recall in the shared attention queue and Personal Context.
- [x] Include recall coverage and lapses in the weekly learning review.
- [x] Expose create, due, and submit behavior through the central registry,
  dynamic MCP, LangGraph, and deterministic WhatsApp commands.
- [x] Preserve caller-supplied idempotency keys through the MCP schema while
  continuing to inject trusted owner identity at the server boundary.
- [x] Document the commands, scheduling model, replay guarantees, and local-data
  policy.

Verification: 34 focused recall/concept/study/parity tests, 365 full AI tests,
full Ruff, and Astro check/build with 21 pages.

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

## Batch Academic-01d — QA login and HEBAT upload reliability

Completed: 2026-08-01

- [x] Wait for the QA page’s own reCAPTCHA callback instead of injecting a
  token or changing form fields.
- [x] Add a configurable settle delay before normal QA login submit.
- [x] Remove automation-stealth flags and custom user-agent overrides that made
  the portal reject its own token.
- [x] Default QA to standard headed Chrome for the portal’s anti-bot policy.
- [x] Select Moodle’s visible Add control, set the hidden file input, click
  `Upload this file`, save, and reopen the assignment for verification.
- [x] Execute an approved smoke upload to the oldest selected overdue assignment
  using a clearly labelled non-graded test PDF.

Verification: standard headed Chrome reached the QA menu; the smoke artifact
`Xninetzy_upload_smoke_test.pdf` is visible on HEBAT assignment `36248` with
status `Submitted for grading`, 152 days late.

## Batch Academic-01e — Academic parser and snapshot reliability

Completed: 2026-08-01

- [x] Parse Cyber Campus profile values from table rows, label-for controls, and named form fields.
- [x] Aggregate academic-status rows across repeated tables and tolerate header aliases.
- [x] Deduplicate grade snapshots by owner, period, and content hash across the full history.
- [x] Add regression coverage for a historical hash returning after an intervening change.
- [x] Add KRS watcher intervals in seconds with 30-second pre-window and 10-second in-window polling.
- [x] Backfill legacy Graph V1 rows into GraphRAG V3 canonical SQLite/outbox on startup and route legacy search to V3 when enabled.

Verification: 31 focused academic tests and Ruff passed.

## Batch Academic-01c — Shared academic login contract

Completed: 2026-08-01

- [x] Resolve HEBAT, QA, Cyber Campus, and mahasiswa aliases from the same
  deployment-scoped HEBAT account.
- [x] Enforce the shared account in HEBAT credential login and relogin paths.
- [x] Use the shared resolver for HEBAT startup, diagnostics, QA login, and
  Cyber Campus credential filling.
- [x] Add explicit `ACADEMIC_CREDENTIAL_SOURCE` and `QA_CREDENTIAL_SOURCE`
  defaults to `.env.example`.
- [x] Validate Cyber Campus storage state against a live authenticated route.
- [x] Stop QA retry loops when reCAPTCHA is rejected and return a human
  verification requirement.

Verification: 20 focused academic login tests and Ruff passed. The QA portal
rejected a headless reCAPTCHA token during live diagnosis; this is now surfaced
as a manual browser verification requirement rather than treated as a credential
failure.

## Batch Academic-01a — Cyber Campus login foundation

Completed scope: 2026-07-29

- [x] Reuse HEBAT credential through an in-memory provider.
- [x] Open Cyber Campus in a bounded background Chromium context.
- [x] Fill credentials without exposing them to prompts or tool schemas.
- [x] Send CAPTCHA image only to WhatsApp `ADMIN_JID`.
- [x] Bind CAPTCHA challenge to owner, TTL, and attempt limit.
- [x] Route replied or bare CAPTCHA values directly without invoking the LLM.
- [x] Normalize `/catchpa`, Baileys device suffixes, and cached quoted messages.
- [x] Save successful session through the encrypted local session manager.
- [x] Register the same tools through the central registry and MCP adapter.
- [x] Inventory all live frame navigation with same-origin path sanitization.
- [x] Generate a KRS capability manifest and structure hash from runtime DOM and
  sanitized inline-script targets.
- [x] Verify 29 navigation items, 27 unique safe routes with zero unreachable,
  and four KRS tabs against the live owner session.
- [x] Make `/web-refresh` force a real authenticated refresh.
- [x] Add sanitized schedule/KHS fixtures and deterministic read-only parsers.
- [x] Read 10 live schedule entries from the encrypted owner session.
- [x] Add owner-bound, volatile, single-use grade-token intake through WhatsApp.
- [x] Keep the private token-submit command outside registry, MCP, and LLM tools.
- [ ] Implement bound, expiring, single-use KRS approval before any write action.

## Batch Academic-01b — Schedule and grade-token reads

Completed scope: 2026-07-29

- [x] Parse the live six-column Cyber Campus schedule deterministically.
- [x] Read schedule data only from the encrypted owner session.
- [x] Parse KHS tables into header-bound values without an LLM call.
- [x] Request the KHS token only through fixed WhatsApp `ADMIN_JID`.
- [x] Open the live KHS page first so Cyber Campus triggers its registered
  Telegram delivery; keep Telegram configuration outside Xninetzy.
- [x] Bind challenge to normalized owner, TTL, attempt limit, and single use.
- [x] Route replied token text deterministically through the WA cache fallback.
- [x] Prevent token submission through registry, MCP, or LangGraph tools.
- [x] Keep the prepared KHS browser page alive until token consumption or expiry.
- [x] Select the requested semester and use native same-origin fetch without
  relying on portal jQuery.
- [x] Enforce the live portal order: open, wait, fill token, set semester, fetch.
- [x] Confirm the dropdown remains at its default value until token submission.
- [x] Support student-semester aliases from entry year without an LLM call.
- [x] Normalize successful KHS reads into idempotent per-period local snapshots.
- [x] Compare the two latest distinct snapshots without persisting verified tokens.
- [x] Expose the same grade-change reader through WhatsApp, LangGraph, and MCP.
- [x] Parse and expose minimal profile, academic-status history, and current KRS.
- [x] Keep biodata outside the minimal allowlist out of tool responses and storage.
- [x] Share the three readers through WhatsApp commands, LangGraph, and MCP.
- [x] Verify a live Semester Genap 2025/2026 schedule with 10 entries.
- [x] Complete a live KHS read with a fresh owner token and required field order.
- [ ] Add course-offering and quota models when the KRS period is active.

Verification: 346 full AI tests, 29 focused academic/parity tests, full Ruff,
Astro check/build with 21 pages, healthy real Compose services, and live
read-only smoke checks for the minimal profile, one academic-status row, and 10
current-KRS rows. Private field values were not emitted by the smoke check.

## Batch Runtime-02 — Cross-platform installation

Completed: 2026-07-29

- [x] Replace Linux-only host networking with a bridge network.
- [x] Publish AI and WA ports only on host loopback.
- [x] Add `host.docker.internal` routing for an optional host Ollama runtime.
- [x] Add interactive Linux/macOS/WSL2 and Windows PowerShell installers.
- [x] Generate internal keys locally and keep provider input hidden.
- [x] Document Docker Desktop startup behavior for macOS and Windows.
- [x] Add portfolio and GitHub links to the docs landing page and footer.
- [x] Redact libsignal session objects before third-party console output.

## Batch Runtime-03 — Host coding bridge and shared Agent Skills

Completed: 2026-08-01

- [x] Override container persistence paths so MCP never attempts to create host
  absolute paths inside `/app`.
- [x] Verify `mcp_server` imports in Docker and OpenCode reports `xninetzy
  connected`.
- [x] Route `/code` from the AI container to the host bridge over an
  authenticated loopback gateway.
- [x] Add read-only host execution for ordinary chat failover.
- [x] Add bounded host workspace translation and host CLI path detection.
- [x] Add systemd user installer and verify the bridge is active after startup.
- [x] Remove Codex, Claude Code, and OpenCode npm installation from the AI image.
- [x] Synchronize compatibility `app/xninetzy/skills/*` metadata with the
  canonical registry and Agent Skills catalog.
- [x] Run AI lint and focused runtime/skill suites after final runtime changes.
- [x] Verify Codex, Claude Code, and OpenCode global MCP configs on the target
  host and record the result without exposing credentials.

Current host smoke result: bridge `/health` reports Codex, Claude Code, and OpenCode available; unauthenticated `/v1/run` returns `401`; Docker MCP import prints `IMPORT_OK`; the final Docker image contains no coding CLI; host Codex, Claude Code, and OpenCode all report `xninetzy` connected.

## Batch WA-Approval-01 — Canonical WhatsApp verification

Completed: 2026-07-29

- [x] Send approval to fixed `ADMIN_JID` using Baileys Approve/Reject buttons.
- [x] Fall back to `/approve` and `/reject` text when interactive buttons fail.
- [x] Forward durable image/document content to admin before verification.
- [x] Parse button IDs as commands instead of visible labels.
- [x] Resolve Baileys `@lid` to a phone JID when mapping is available.
- [x] Accept only explicit `OWNER_ALLOWED_JIDS` when mapping is unavailable.
- [x] Keep all approval, CAPTCHA, and verification flows on WhatsApp admin.
- [x] Remove all legacy alternate-channel configuration and documentation contracts.

## Batch WA-Menu-01 — Startup admin command menu

Completed: 2026-07-29

- [x] Trigger menu only after the first successful connection `open`.
- [x] Send five capability cards with 15 deterministic slash-command buttons.
- [x] Keep every card within the three-button Baileys compatibility boundary.
- [x] Deliver only to normalized `ADMIN_JID`, never an LLM-selected target.
- [x] Prevent duplicate delivery during reconnect in the same process.
- [x] Retry on a later reconnect only when button and text delivery both fail.
- [x] Fall back to one complete text menu when interactive buttons fail.
- [x] Add environment configuration and operator documentation.
- [x] Verify Docker delivery against the connected admin account: five cards and
  15 buttons sent once on process startup.

Verification: 20 WA tests, TypeScript lint/build, healthy Compose services, and
runtime `startup_menu_sent` evidence with `messagesSent=5` and `buttonsSent=15`.

## Batch Runtime-01 — Docker and automatic startup

Completed: 2026-07-29

- [x] Install Playwright Chromium before changing `/ms-playwright` permissions.
- [x] Build both AI and WA Docker images successfully.
- [x] Generate missing internal auth keys without printing secrets.
- [x] Run AI and WA engine healthy with authenticated internal API calls.
- [x] Keep both services on `restart: unless-stopped`.
- [x] Enable and verify the Docker systemd service on the current laptop.

### Host MCP bootstrap update — 2026-08-01

The FastAPI entry point now invokes the shared MCP runtime path resolver before settings are evaluated. Mixed host imports of app.main and the stdio MCP server therefore use services/ai/data instead of attempting to create /app/data; the mixed import smoke test reports IMPORT_OK.

## Adaptive Web Intelligence — 2026-08-01

Implemented across the shared registry, LangGraph, MCP, and WhatsApp command path:

- Phase 0: one bounded web_discover workflow can combine public discovery, GraphRAG V3 page/link projection, optional Knowledge ingestion, and optional PixelRAG capture.
- Phase 1: HTTPS public URLs resolve to deterministic public-hash site definitions while HEBAT and Cybercampus presets remain available.
- Phase 2: bounded BFS discovery follows same-host links only, uses GET/HEAD-only routing, denies mutation/sensitive URLs, stops on human verification, and persists replayable discovery JSON.
- Phase 3: adaptive evidence routing is exposed through web_discover; visual capture and knowledge ingestion are explicit flags, and the local PixelRAG health state remains observable without silently installing a server package.

Verification: 33 focused web-analysis/inbox tests and Ruff pass. The full AI run reached 528 passed; the remaining CPU-only failures are caused by the current host virtualenv containing CUDA distributions (triton/nvidia-*), not by web discovery.
