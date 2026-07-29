# Cyber Campus KRS, Grades, and Telegram Plan

Status: Planning only — no portal write, KRS submit, grade watcher, Telegram
polling, or new credential handling is implemented by this document.

Last updated: 2026-07-29

## Objective

Extend the single-owner Xninetzy OS with a Cyber Campus adapter that can read
academic state, prepare KRS plans, and eventually execute gated KRS changes.
HEBAT remains the Moodle adapter. Cyber Campus remains a separate academic
adapter. Both expose shared tools through the central registry so WhatsApp,
LangGraph, Codex, Claude Code, and OpenCode see the same state and policies.

The safety model is:

`read freely -> prepare deterministically -> bind approval -> revalidate -> apply -> bind final approval -> revalidate -> submit -> verify -> audit`

## Decisions

1. Extend `app/xninetzy/os/academic/mahasiswa_portal`; do not create a second
   overlapping `unair` domain.
2. Reuse `HEBAT_USERNAME` and `HEBAT_PASSWORD` through an in-memory campus
   credential provider. Do not add or persist duplicate Cyber Campus username
   or password fields.
3. Credential reuse is a configured attempt, not an assumption that both sites
   have identical authentication flows. CAPTCHA, OTP, SSO challenges, and first
   login remain manual. A validated session is stored through the existing
   encrypted local session manager.
4. A Telegram Bot Token authenticates only a notification/approval bot. It does
   not authenticate Cyber Campus and is not required to read grades.
5. Keep inbound Telegram polling in a future `services/telegram-engine`, not in
   the stdio MCP server.
6. Keep selectors and browser actions deterministic and audited. LLMs choose a
   registered tool, never arbitrary selectors or JavaScript.
7. KRS uses two approvals: apply selections, then final submit.
8. Read-only grade checks may be scheduled. A notification is emitted only when
   a persisted snapshot comparison detects a real change.

## Current repository state

- `mahasiswa_portal/tools.py` exposes read-only portal status, schedule, and KRS
  watcher status.
- `web_analysis` already provides an encrypted session manager, snapshot store,
  site definition for `mahasiswa.unair.ac.id`, bounded browser crawl, and local
  runtime directory.
- HEBAT credentials already live in deployment environment settings and are not
  part of MCP schemas or SQLite.
- HITL approvals currently lack expiry, action hash, resource binding, approval
  phase, and single-use consumption. This must be upgraded before any KRS write.
- The central registry automatically provides interface parity through MCP.
- All `services/ai/data/**` runtime artifacts are ignored by Git.

## Capability and approval matrix

| Adapter | Capability | Policy |
|---|---|---|
| HEBAT | login, courses, activities, materials, deadlines | read without approval |
| HEBAT | upload or final submission | existing confirmation/HITL; never silent |
| Cyber Campus | profile, academic status, grades, schedule, offerings, quota | read without approval |
| Cyber Campus | build and validate a KRS plan | draft without portal mutation |
| Cyber Campus | add, remove, or change selected classes | first bound approval |
| Cyber Campus | final KRS submission | second bound approval |
| Telegram | status and owner notification | owner destination only |
| Telegram | approve or reject | owner chat allowlist plus AI API authentication |

Payment, password changes, profile mutation, and unrelated administrative
actions remain out of scope.

## Target architecture

```text
WhatsApp / Telegram / Codex / Claude / OpenCode / LangGraph
                         |
                         v
                 central tool registry
                         |
          +--------------+---------------+
          |                              |
          v                              v
  HEBAT Moodle adapter          Cyber Campus adapter
                                         |
                  +----------------------+------------------+
                  |                      |                  |
              read models          KRS workflow       grade watcher
                  |                      |                  |
                  +---------- shared SQLite/audit ----------+
                                         |
                                Telegram owner notifier
```

Planned module layout:

```text
services/ai/app/xninetzy/os/academic/mahasiswa_portal/
├── client.py
├── models.py
├── parser.py
├── policy.py
├── credential_provider.py
├── browser_actions.py
├── repository.py
├── grades_service.py
├── krs_service.py
├── workflow.py
└── tools.py

services/ai/app/xninetzy/interfaces/telegram/
├── client.py
└── tools.py

services/telegram-engine/
└── inbound owner-only polling bridge
```

## Credential and session contract

The proposed default is:

```dotenv
CYBER_CAMPUS_ENABLED=false
CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat
CYBER_CAMPUS_BASE_URL=https://mahasiswa.unair.ac.id
```

`CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat` resolves credentials from the existing
`HEBAT_USERNAME` and `HEBAT_PASSWORD` settings only at login time. The values
must never be copied into SQLite, KRS plans, snapshots, logs, prompts, Telegram,
MCP config, or audit payloads.

If direct credential login is rejected or an interactive challenge appears,
the adapter stops and asks for a manual local login. The resulting browser state
is encrypted by `WEB_ANALYSIS_ENCRYPTION_KEY`. The adapter never solves CAPTCHA
or OTP.

Proposed Telegram deployment settings:

```dotenv
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_OWNER_CHAT_ID=
TELEGRAM_GRADE_NOTIFICATION_ENABLED=false
TELEGRAM_APPROVAL_ENABLED=false
TELEGRAM_POLLING_ENABLED=false
TELEGRAM_POLLING_TIMEOUT_SECONDS=30
```

The bot token stays deployment-scoped. Tools never accept a destination chat ID;
they can send only to `TELEGRAM_OWNER_CHAT_ID`.

## Persistent model

Planned tables:

- `campus_krs_plans`: owner plan, semester, snapshot hash, action hash, total
  credits, status, expiry, version, and timestamps;
- `campus_krs_selections`: normalized add/remove/change-class actions;
- `campus_krs_conflicts`: schedule, prerequisite, capacity, and policy findings;
- `campus_grade_snapshots`: normalized grade snapshot hash and capture time;
- `campus_grade_changes`: before/after values and notification state;
- `campus_portal_audit`: redacted event, plan, approval, evidence, and result;
- upgraded `approval_requests`: resource ID, action hash, phase, expiry,
  consumed-at timestamp, and immutable payload hash.

Runtime evidence remains local under ignored paths:

```text
services/ai/data/web-analysis/mahasiswa/
services/ai/data/campus/audit/
services/ai/data/campus/screenshots/
services/ai/data/campus/snapshots/
services/ai/data/campus/krs-plans/
```

Screenshots must be bounded, access-restricted, and redacted when they contain
student identifiers or sensitive academic information.

## Bound approval contract

An approval must bind all of the following:

- plan ID and immutable version;
- local owner/student identifier represented by a non-secret stable ID;
- phase: `apply_selections` or `final_submit`;
- normalized selections and removals;
- total credits;
- portal snapshot hash;
- action hash;
- issue and expiry times;
- approval owner and single-use consumption state.

Canonical JSON uses sorted keys, compact separators, and UTF-8 before SHA-256.
Any changed class, quota, schedule, prerequisite, credit count, plan version, or
portal snapshot invalidates the approval.

The state machine is:

```text
draft
  -> awaiting_write_approval
  -> applying
  -> awaiting_final_approval
  -> submitting
  -> completed
```

Every state may move to `expired` or `failed`. A completed, rejected, expired,
or consumed approval cannot be replayed.

## Deterministic KRS execution

`prepare` is read-only and must:

1. capture profile, prior grades, offerings, current KRS, rules, and snapshot;
2. normalize schedules and prerequisites;
3. detect conflicts, credit limits, capacity issues, and missing evidence;
4. produce alternatives without changing the portal;
5. persist the plan and request a bound write approval.

`apply` must:

1. validate approval owner, phase, hash, version, and TTL;
2. reopen the page and compare the fresh snapshot;
3. stop on ambiguous selectors, changed quota, changed rules, or stale session;
4. apply only the normalized actions in the approved plan;
5. reread the portal and compare every selection;
6. capture before/after evidence;
7. request a new final approval without submitting.

`submit` repeats all validation and presses the final control only when its
unique locator and confirmation evidence are present. Missing confirmation is a
failure, never a presumed success.

## Planned shared tools

Read and planning:

- `campus_session_status`
- `campus_read_profile`
- `campus_read_academic_status`
- `campus_check_grades`
- `campus_check_grade_changes`
- `campus_read_course_offerings`
- `campus_read_current_krs`
- `campus_krs_prepare`
- `campus_krs_status`

Gated mutation:

- `campus_krs_apply`
- `campus_krs_request_final_approval`
- `campus_krs_submit`

Telegram:

- `telegram_status`
- `telegram_send_owner_message`

These names are registered once in the central registry. No client-specific
catalogue is maintained.

## Telegram engine contract

The future engine uses either long polling or webhook, never both. Initial local
deployment uses long polling. It must:

1. accept updates only from the configured owner chat ID;
2. keep update offsets durably so restarts do not replay approvals;
3. accept only an allowlisted command grammar such as `/approve <id>` and
   `/reject <id>`;
4. forward a normalized private-chat request to authenticated `/api/chat`;
5. never log bot token, incoming secrets, or full update payloads;
6. rate-limit invalid requests and expose health/failure status.

Telegram notification delivery needs its own idempotency key and persisted
delivery state. Grade notifications are emitted only after a successful snapshot
commit and never include credentials, cookies, or hidden portal payloads.

## Implementation phases

### Academic-01 — Read-only foundation

- [ ] Add normalized Cyber Campus models and repository.
- [ ] Add the HEBAT-backed credential provider with no secret persistence.
- [ ] Validate encrypted manual-login fallback and deterministic selectors.
- [ ] Implement profile, status, grades, offerings, current KRS, and schedule reads.
- [ ] Add snapshot comparison and read-only grade-change tools.
- [ ] Add parser fixtures with sanitized offline HTML.

### Academic-02 — Approval hardening

- [ ] Add action/resource hash, phase, TTL, version, and single-use consumption.
- [ ] Make approval state transitions transactional and replay-safe.
- [ ] Add stale snapshot, expired approval, changed quota, and cross-owner tests.
- [ ] Preserve backward compatibility for roadmap and HEBAT approvals.

### Academic-03 — KRS planning

- [ ] Build a deterministic conflict/prerequisite/credit/capacity planner.
- [ ] Apply personal rules without exposing them to portal pages.
- [ ] Persist immutable versioned plans and alternatives.
- [ ] Format a WhatsApp/MCP plan summary without student identifiers.

### Academic-04 — Gated KRS actions

- [ ] Implement audited add/remove/change-class actions.
- [ ] Require first approval and fresh snapshot validation.
- [ ] Verify applied selections and request a separate final approval.
- [ ] Implement final submission with unique locator and receipt verification.
- [ ] Add restart, replay, partial failure, and compensation tests.

### Telegram-01 — Owner notification

- [ ] Add an owner-only Telegram client and registry tools.
- [ ] Add grade-change formatting and idempotent delivery state.
- [ ] Add `.env.example`, secret redaction, mocked Bot API tests, and docs.

### Telegram-02 — Inbound approval bridge

- [ ] Create `services/telegram-engine` with durable polling offsets.
- [ ] Enforce owner chat ID and AI bearer authentication.
- [ ] Route only allowlisted approval/status commands.
- [ ] Add duplicate update, non-owner, timeout, and restart tests.

## Acceptance gates

No portal mutation work begins until Academic-01 and Academic-02 pass.

- Read tools work from WhatsApp, LangGraph, and dynamic MCP with identical data.
- No secret appears in tool schemas, SQLite, logs, snapshots, audit, or Git.
- Repeated prepare/apply/submit requests do not duplicate side effects.
- An expired or changed plan cannot consume an approval.
- Apply never performs final submit.
- Final submit requires a separate current approval.
- Portal changes after approval stop execution and require a new plan.
- Ambiguous locators, CAPTCHA, OTP, or missing receipt fail closed.
- Grade notifications are sent only for persisted changes and at most once.
- Telegram non-owner updates never reach `/api/chat`.
- Evidence and audit paths remain local and ignored by Git.
- AI, Telegram engine, docs, secret scan, and Compose tests pass.

## Documentation deliverables

Implementation must update `.env.example`, root README, Astro pages for Cyber
Campus and Telegram, MCP tool examples, security model, troubleshooting, backup
scope, and the implementation progress tracker. Documentation must distinguish
planned, available, and disabled capabilities so it never implies that KRS
submission is active before the code and safety gates exist.

## External references supplied for implementation review

- Telegram bot tutorial: <https://core.telegram.org/bots/tutorial>
- Telegram Bot API: <https://core.telegram.org/bots/api>
- MCP debugging: <https://modelcontextprotocol.io/docs/tools/debugging>
