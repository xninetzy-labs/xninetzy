# Xninetzy UACC — Error Handling, Idempotency, and Monitoring

This reference expands error handling, idempotency, monitoring vs automation, standard UACC status output, and standard analysis output. Read it when handling structured tool errors or producing the closing report.

## Error handling

Handle structured errors explicitly.

Examples:

```text
NOT_FOUND
→ refine page/identifier

AUTH_REQUIRED
→ verify UACC session

CHALLENGE_REQUIRED
→ return to owner CAPTCHA flow

CHALLENGE_EXPIRED
→ invalidate challenge; start fresh login

INVALID_INPUT
→ correct adapter arguments

POLICY_HELD
→ stop and request approval
```

Never retry a stale or expired CAPTCHA challenge.

## Idempotency

For any supported retryable mutation or persistent analysis operation:

* use a stable `idempotency_key` when supported,
* do not duplicate records after retries,
* verify actual state before replaying.

A failed network response does not prove the portal did not change. For future writes, re-read the state before retry.

## Monitoring vs automation

Monitoring is allowed within the configured read-only watchdog boundary. Automation of authentication is not. This distinction is deliberate:

```text
monitor state
✓

notify owner
✓

start browser automatically
✗

answer CAPTCHA automatically
✗

submit unattended action
✗
```

## Standard UACC status output

```text
Portal:
Session:
Session Freshness:
Authentication:
Current Challenge:
Analysis Status:
Last Verified:
Known Pages:
Uncertainty:
Next Action:
```

Do not include secrets.

## Standard analysis output

```text
UACC Scope
Session State
Page Catalog
Verified Structures
Protection / CAPTCHA Behavior
Known Navigation
Current vs Historical State
Graph / Memory Persistence
Open Questions
Next Analysis Action
```

## Completion contract

Every meaningful UACC workflow should return the relevant subset of:

**Portal identity** — UACC / UnairSatu.

**Session status** — current, stale, expired, or unavailable.

**Authentication status** — whether login is complete or human verification is pending.

**Challenge status** — only non-secret challenge state.

**Read/analyze result** — verified structured observations.

**Freshness** — whether the analysis is current enough for the request.

**Persistence status** — Graph/memory/checkpoint state when applicable.

**Approval status** — only relevant for future supported writes.

**Verification evidence** — what was directly observed.

**Next action** — one bounded safe continuation step.

## Operating rules

The system must:

* keep UACC and Cyber Campus strictly separate,
* use only authorized owner-bound credentials,
* keep credentials and tokens out of logs and responses,
* treat CAPTCHA as a mandatory human-verification boundary,
* never solve CAPTCHA automatically,
* never bypass institutional controls,
* invalidate expired challenges,
* use typed deterministic portal adapters,
* prefer read-only analysis,
* persist only minimum durable portal structure,
* distinguish observed data from inference and historical memory,
* revalidate stale portal state,
* require explicit confirmation for any future write,
* re-read and verify after any supported mutation,
* preserve provenance when integrating with Graph RAG and Memory.

The canonical lifecycle is:

**Identify → Isolate → Session Check → Authenticate → Human Verify → Read → Analyze → Persist → Checkpoint → Monitor → Propose/Verify**