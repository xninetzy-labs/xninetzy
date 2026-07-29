# Cyber Campus, KRS, Grades, and WhatsApp Verification Plan

Status: partial implementation
Last updated: 2026-07-29

## Goal

Extend the shared Xninetzy OS with Cyber Campus reads, grade monitoring, and a
safe KRS workflow. Domain behavior remains shared by WhatsApp, LangGraph, Codex,
Claude Code, and OpenCode through the central registry and `xninetzy` MCP.

## Channel boundary

- WhatsApp `ADMIN_JID` is the only channel for CAPTCHA, grade-token intake,
  confirmation, approval, verification media, and operator action requests.
- Grade tokens are accepted only by a deterministic WhatsApp command/reply flow,
  never passed to an LLM, and kept only in bounded volatile memory.
- CAPTCHA and OTP remain manual human-in-the-loop challenges.
- Cyber Campus reuses `HEBAT_USERNAME` and `HEBAT_PASSWORD` in memory. Secrets do
  not enter prompts, MCP schemas, SQLite, snapshots, logs, or audit payloads.

## Current implementation

- [x] HEBAT-backed credential provider and bounded Chromium login coordinator.
- [x] Owner-bound CAPTCHA challenge with TTL, attempt limit, and WhatsApp image delivery.
- [x] Encrypted Cyber Campus session persistence.
- [x] Authenticated GET/HEAD-only navigation audit.
- [x] Runtime KRS capability manifest with stable structure hash.
- [x] Canonical WhatsApp approval notifier and media forwarding.
- [x] Legacy alternate-channel configuration and documentation removed.
- [x] Deterministic schedule and generic KHS table parsers with sanitized fixtures.
- [x] Owner-bound WhatsApp grade-token handoff to the deterministic reader.
- [ ] Profile, offering, current-KRS, and grade-change snapshot models.
- [ ] Bound, expiring, single-use KRS approval model.
- [ ] KRS planner and gated portal mutation workflow.

## Target flow

```text
WhatsApp admin / MCP / LangGraph
              |
              v
      central tool registry
              |
              v
     Cyber Campus adapter
        |             |
        v             v
  read models     KRS workflow
        |             |
        +------ WhatsApp ADMIN_JID approval

WhatsApp ADMIN_JID -> volatile grade-token intake -> grade reader
```

## Approval matrix

| Capability | Policy |
|---|---|
| Profile, grades, schedule, offerings, quota | read-only |
| Build and validate KRS plan | draft without mutation |
| Add/remove/change selected classes | first bound WhatsApp approval |
| Final KRS submission | separate current WhatsApp approval |
| CAPTCHA/OTP | manual owner response through WhatsApp |
| Grade token | owner-only WhatsApp input, volatile and single-use |

Payment, password changes, profile mutation, CAPTCHA solving, and unrelated
administrative actions remain out of scope.

## Bound KRS approval

Every approval binds the plan ID, immutable version, owner, phase, normalized
actions, total credits, portal snapshot hash, action hash, expiry, and consumed
state. A changed class, quota, schedule, prerequisite, credit total, plan
version, or portal snapshot invalidates the approval.

```text
draft
  -> awaiting_write_approval
  -> applying
  -> awaiting_final_approval
  -> submitting
  -> completed
```

Apply never performs final submit. Every state can move to `expired` or `failed`.

## Grade-token contract

The flow starts from WhatsApp admin with `/nilai`. Xninetzy sends a verification
request to the fixed `ADMIN_JID` after opening the KHS page. Cyber Campus itself
sends the token to the Telegram account registered on the portal; Xninetzy has
no Telegram bot configuration or inbound Telegram engine. The owner relays that
official token by replying to WhatsApp or using a bound command. The router
verifies the sender before the token reaches the grade reader.

The token has a short TTL and attempt limit, is consumed after one read attempt,
and is never persisted or exposed through MCP. Invalid, expired, replayed, or
cross-owner input fails closed.

```dotenv
CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS=180
CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS=3
```

## Remaining phases

### Academic-01b — Read-only portal models

- [x] Discover and classify live academic navigation without retaining visible values.
- [x] Add sanitized schedule/KHS HTML fixtures and deterministic parsers.
- [x] Implement live schedule and token-gated KHS reads.
- [x] Trigger the portal-owned token delivery before the WhatsApp handoff.
- [x] Bind the selected semester and prepared browser page to the token challenge.
- [x] Submit the KHS display request with native same-origin fetch without jQuery.
- [ ] Implement profile, offerings, current KRS, and grade snapshots.
- [ ] Persist normalized grade snapshots and calculate real changes.
- [ ] Add interface-parity and session-expiry tests.

### Academic-02 — Approval hardening

- [ ] Add resource/action hash, phase, TTL, version, and single-use consumption.
- [ ] Make state transitions transactional and replay-safe.
- [ ] Test stale snapshots, expiry, quota changes, and cross-owner denial.

### Academic-03 — KRS planning

- [ ] Implement conflict, prerequisite, credit, capacity, and personal-rule checks.
- [ ] Persist immutable versioned plans and alternatives.
- [ ] Format redacted summaries for WhatsApp and MCP.

### Academic-04 — Gated KRS actions

- [ ] Apply selections after first current WhatsApp approval.
- [ ] Verify applied state and request a distinct final approval.
- [ ] Submit only with a unique locator and receipt evidence.
- [ ] Add replay, restart, partial-failure, and compensation tests.

### GradeToken-01 — WhatsApp owner intake

- [x] Add owner-bound volatile challenge coordinator.
- [x] Route reply and explicit command without an LLM call.
- [x] Hand the token directly to the deterministic grade reader.
- [x] Preserve `/nilai <period>` through deterministic command routing.
- [x] Delay dropdown assignment until after the token field is filled.
- [x] Keep the portal dropdown at its default value while waiting for the token.
- [x] Map `/nilai semester N` from the configured or UNAIR-derived entry year.
- [x] Add cross-owner, replay, expiry, redaction, and parser tests.
- [x] Exclude the private submit command from registry/MCP/LLM tools.

## Acceptance gates

- No portal write begins before Academic-01b and Academic-02 pass.
- No secret appears in schemas, SQLite, logs, snapshots, audit, Git, or prompts.
- Expired, changed, rejected, or consumed approvals cannot be replayed.
- CAPTCHA/OTP and grade-token input use only the WhatsApp owner channel.
- All confirmation targets resolve to `ADMIN_JID`.
- AI, WA, docs, secret scan, Compose, and interface-parity tests pass.
