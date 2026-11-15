# cyber-campus — §50–56

Contents: 50. Cross-Session Continuity; 51. Audit Trail; 52. Audit Integrity; 53. Read Contract; 54. Write Contract; 55. KRS Decision Matrix; 56. Risk Classification

## 50. Cross-Session Continuity

A resumed workflow must retain:

```text
session_id
period
current KRS snapshot
plan
action hash
approval state
staged state
verification state
```

But revalidation is mandatory before:

```text
stage
submit
```

A previous approval does not survive material state changes.

---

## 51. Audit Trail

Audit events:

```text
SESSION_VERIFIED
PORTAL_CONTEXT_BOUND
READ_COMPLETED
PLAN_CREATED
DRY_RUN_COMPLETED
ACTION_HASH_CREATED
APPROVAL_RECEIVED
PRECHECK_COMPLETED
STAGE_STARTED
STAGE_VERIFIED
FINAL_APPROVAL_RECEIVED
SUBMISSION_STARTED
SUBMISSION_RESULT
VERIFICATION_COMPLETED
SESSION_CLOSED
```

Each event should contain:

```yaml
audit:
  event_id:
  timestamp:
  session_id:
  action:
  portal_context:
  period:
  status:
  evidence_refs:
```

Never include secrets.

---

## 52. Audit Integrity

Where supported, use:

```text
previous_event_hash
current_event_hash
```

or equivalent tamper-evident chaining.

Do not fabricate immutable storage guarantees.

---

## 53. Read Contract

Reads do not require mutation approval.

Every read returns:

```text
period/page
structured result
freshness
session status
uncertainty
source/evidence
```

---

## 54. Write Contract

Writes require:

```text
current state
approved plan
action hash
fresh revalidation
narrow mutation
post-write verification
audit
```

---

## 55. KRS Decision Matrix

Before staging:

```yaml
krs_decision:
  current:
    credits:
    courses:

  proposed:
    credits:
    courses:

  checks:
    prerequisites:
    eligibility:
    quota:
    schedule:
    credit_limit:
    registration_window:
    current_state_match:

  status:
    READY
    BLOCKED
    UNCERTAIN
```

---

## 56. Risk Classification

```text
SAFE
  read-only academic inspection

ATTENTION
  planning with incomplete evidence

AT_RISK
  stale quota/session/context

BLOCKED
  authorization failure
  state mismatch
  unresolved uncertainty
  unsupported portal operation
```

---
