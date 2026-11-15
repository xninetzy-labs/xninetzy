---
name: cyber-campus
description: 'Safety-first workflow for the owner''s Cyber Campus/SIS session: authorized login, schedule, grade and KRS reads, quota and prerequisite checks, staged KRS plans and approval-gated writes with verification. Use for Cyber Campus portal tasks.'
metadata:
  keywords: academic access analysis auditable authenticated authentication aware bound bypasses captcha capture collection comparable controls course deterministic eligibility evidence handles idempotent immediate information inspection mfa mutations navigation never normalization operating otp planning portals post preflight receipt reconciliation required revalidation semester state student submission supported system university when where write
---


# 2. Core Invariants

1. Never perform protected actions without a valid authenticated session.
2. Never reuse session assumptions across unrelated portal contexts.
3. Every academic record must have an explicit academic period when applicable.
4. Current portal state beats historical memory.
5. A stale read cannot justify a consequential write.
6. Approval must bind to the exact intended action set.
7. Any material precondition change invalidates approval.
8. Stage and final submit are separate transitions.
9. A failed stage must not be represented as a successful submission.
10. A submitted action must be verified through authoritative portal state.
11. No silent overwriting of existing academic selections.
12. No undocumented mutation routes.
13. No invented selectors or field names.
14. No CAPTCHA, OTP, MFA, or access-control bypass.
15. No credentials, session cookies, or tokens in logs.
16. No grade/course data may be silently assigned to another semester.
17. No assumptions about quota, prerequisite, eligibility, or enrollment state when the portal can be checked.
18. Unknown must remain unknown.
19. Current portal state must be revalidated immediately before consequential execution.
20. A mutation must be as narrow as the user's approved intent.
21. A second unrelated mutation must never be bundled into an approved action.
22. Portal confirmation is required before declaring success.
23. If the portal state changes unexpectedly, stop and re-enter planning.
24. If verification evidence is unavailable, final state is `unknown`.

---

# 3. Portal Authority

For current academic state use:

```text
current authenticated portal state
    >
current official portal message/announcement
    >
current official academic metadata
    >
previous verified portal state
    >
stored memory
    >
general assumptions
```

Memory may help explain history.

Memory must not override current portal state.

---

# 26. Approval

Approval must identify:

```text
portal
academic period
current KRS state
courses to add
courses to remove
final credit count
quota risks
conflicts
known uncertainties
action hash
```

Example:

```text
Target:
Cyber Campus

Period:
2026/2027 Ganjil

Action:
Add IF101-A
Remove IF204-B

Final credits:
22

Action hash:
abc123...

Approval:
Required
```

---

# 37. Success Claims

Allowed:

```text
"The portal confirms the KRS is submitted."
```

Not allowed:

```text
"I sent the request, so your KRS is submitted."
```

Allowed:

```text
"The staging state matches the approved plan."
```

Not allowed:

```text
"The staging probably worked."
```

---

# 57. Completion Contract

Every interaction returns the relevant subset of:

```text
Portal
Identity/session state
Academic period
Page/record identity
Structured result
Freshness
Conflicts
Uncertainty
Approval state
Execution state
Verification evidence
Audit reference
Next safe action
```

For KRS mutations additionally:

```text
Current KRS hash
Plan hash
Approval hash
Staged state
Final state
Submission receipt
```

---

# 58. Routing

```text
HEBAT/Moodle material
    -> hebat-academic

Academic multi-step orchestration
    -> xninetzy-assignment-orchestrator

Memory continuity
    -> xninetzy-memory

General academic safety
    -> xninetzy-academic-safety

UACC/UnairSatu SSO
    -> xninetzy-uacc

General portal/web structure
    -> xninetzy-web-analysis

Lightweight Cyber Campus MCP adapter
    -> xninetzy-cyber-campus
```

---

# 60. Operational Decision Tree

```text
REQUEST
  ↓
Is this Cyber Campus/SIS?
  |
  +-- no -> route elsewhere
  |
  v
Need protected data?
  |
  +-- yes -> session check
  |
  v
Need current academic state?
  |
  +-- yes -> navigate + read + freshness
  |
  v
Read-only?
  |
  +-- yes -> return verified state
  |
  v
Planning?
  |
  +-- yes -> dry-run
  |
  v
Mutation?
  |
  +-- yes -> hash + approve + revalidate
  |
  v
Stage?
  |
  +-- yes -> stage + reconcile
  |
  v
Submit?
  |
  +-- yes -> final approve + submit + verify
  |
  v
Audit
```

---

# 64. Never-Do List

Never:

```text
solve CAPTCHA
bypass OTP
bypass MFA
guess selectors
guess hidden APIs
guess field names
guess semester
guess quota
guess eligibility
guess prerequisite satisfaction
guess submission success
reuse stale approval
silently overwrite KRS
retry unknown write outcome blindly
log credentials
log tokens
mix semesters
mix portal identities
```

---

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/01-domain-state-separation.md` — §1: Domain State Separation
- `references/04-11-session-binding.md` — §4–11: Session Binding, Session Freshness, Session Invalidation Signals, Portal Context Binding, Semester Identity, Navigation, Read Workflow, Academic Read Identity
- `references/12-21-normalization.md` — §12–21: Normalization, Grade Model, Schedule Model, KRS Model, Course Offering Model, Quota Analysis, Prerequisite Analysis, Eligibility, Credit Constraints, Schedule Conflict Detection
- `references/22-25-registration-window.md` — §22–25: Registration Window, Planning State, Dry Run, Action Hash
- `references/27-36-approval-expiration.md` — §27–36: Approval Expiration, Pre-Execution Revalidation, Optimistic Concurrency, Stage, Stage Reconciliation, Final Approval, Submit, Idempotency, Verification, Submission Confirmation
- `references/38-49-unknown-outcome.md` — §38–49: Unknown Outcome, Partial Application, Rollback, Existing Submission Protection, Evidence Model, Minimal Evidence, Sensitive Data, Academic Privacy, Portal Errors, Navigation Failure, Unsupported Portal Behavior, Evidence Conflict
- `references/50-56-cross-session-continuity.md` — §50–56: Cross-Session Continuity, Audit Trail, Audit Integrity, Read Contract, Write Contract, KRS Decision Matrix, Risk Classification
- `references/59-reference-loading.md` — §59: Reference Loading
- `references/61-63-golden-krs-workflow.md` — §61–63: Golden KRS Workflow, Golden Read Workflow, Golden Verification Workflow
- `references/65-final-principle.md` — §65: Final Principle
