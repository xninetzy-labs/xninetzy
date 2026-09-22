---
name: "cyber-campus"

description: "Safety-first academic operating system for authorized Cyber Campus, university SIS, and comparable student-information portals. Handles authenticated session checks, deterministic navigation, academic-state reads, semester-aware normalization, schedule/grade/KRS inspection, course eligibility, quota and prerequisite analysis, staged KRS planning, approval-bound mutations, immediate preflight revalidation, idempotent writes where supported, post-write reconciliation, submission verification, receipt capture, and auditable evidence collection. Never bypasses CAPTCHA, OTP, MFA, access controls, or hidden portal protections; never invents portal identifiers or undocumented write flows; never claims a consequential academic action succeeded without authoritative portal confirmation."

metadata:
scope: "general"
platform: "Cyber Campus / university SIS"
owner: "xninetzy"
language: "en"
version: "3.0.0"
lifecycle: >
discover -> session-check -> bind-context -> navigate -> read ->
normalize -> freshness-check -> analyze -> dry-run -> hash ->
approve -> revalidate -> stage -> reconcile -> final-approve ->
submit -> confirm -> audit -> learn

triggers:

* inspect grades
* inspect schedule
* inspect academic status
* inspect current KRS
* inspect course offerings
* inspect quota
* inspect prerequisites
* inspect eligibility
* plan KRS
* stage KRS changes
* submit KRS
* verify a previous portal mutation
* verify submission receipt or status

use_when:

* the user requests authenticated academic-portal interaction
* current portal state is required for an academic decision
* the user needs a KRS plan grounded in current offerings
* the user asks whether an academic mutation actually occurred

do_not_use_when:

* retrieving or studying HEBAT/Moodle course materials
* generic public web analysis
* UACC/UnairSatu SSO-specific handling
* unrelated university administration outside academic SIS scope

references:
lifecycle:
file: "references/lifecycle.md"
use_when:
- lifecycle execution
- session/context state
- stop conditions
- read/write transitions

krs_staging:
file: "references/krs-staging.md"
use_when:
- KRS planning
- dry-run
- approval
- action hash
- staging
- submission

policies:
file: "references/policies.md"
use_when:
- schemas
- freshness
- security
- audit
- completion contract
---------------------

# Cyber Campus Academic OS

Reusable safety-first operating system for interacting with:

```text
Cyber Campus
University SIS
Academic Portal
Student Information System
```

The system supports both:

```text
READ
```

and carefully controlled:

```text
PLAN
STAGE
SUBMIT
VERIFY
```

operations.

Core principle:

> **Read the authoritative portal state first. Normalize it with explicit academic context. Plan before mutating. Bind approval to the exact intended action. Revalidate immediately before execution. Verify the portal's resulting state.**

Second principle:

> **A proposed academic action is never equivalent to an executed academic action.**

Third principle:

> **No portal confirmation, no success claim.**
---


# 1. Domain State Separation

Never collapse these states into one object.

```text
IDENTITY STATE
    ↓
SESSION STATE
    ↓
PORTAL CONTEXT
    ↓
ACADEMIC READ STATE
    ↓
PLANNING STATE
    ↓
APPROVAL STATE
    ↓
EXECUTION STATE
    ↓
VERIFICATION STATE
    ↓
AUDIT STATE
```

## Identity State

Who is authenticated.

## Session State

Whether the authenticated session is currently valid.

## Portal Context

Which:

```text
institution
semester
page
module
record type
```

is currently being inspected.

## Academic Read State

What the portal currently reports.

## Planning State

What the learner proposes to do.

## Approval State

Whether the learner explicitly approved that exact action.

## Execution State

What the system actually attempted.

## Verification State

What the portal confirms afterward.

## Audit State

What evidence and state transitions were recorded.

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

# 4. Session Binding

Every protected interaction receives:

```yaml
session:
  session_id:
  authenticated:
  identity_context:
  portal:
  created_at:
  last_verified_at:
  expires_at:
  scope:
```

Before protected reads:

```text
session valid?
identity correct?
portal correct?
```

Before writes:

```text
session valid?
identity correct?
portal correct?
academic period correct?
```

If any is unknown:

```text
STOP
```

---

# 5. Session Freshness

Classify:

```text
LIVE
FRESH
STALE
EXPIRED
UNKNOWN
```

Suggested semantics:

```text
LIVE
  verified immediately before operation

FRESH
  recently verified and no invalidation signal

STALE
  may no longer represent current portal state

EXPIRED
  session no longer valid

UNKNOWN
  validity cannot be established
```

Never treat:

```text
STALE
```

as:

```text
LIVE
```

---

# 6. Session Invalidation Signals

Invalidate session assumptions when:

```text
login page appears
unauthorized response
session timeout
portal switches account
portal switches institution
portal redirects to SSO
unexpected authentication prompt
permission context changes
academic period changes unexpectedly
```

After invalidation:

```text
re-check session
re-bind portal context
```

---

# 7. Portal Context Binding

Every read should record:

```yaml
portal_context:
  institution:
  portal_host:
  page:
  page_identity:
  academic_period:
  record_type:
  retrieved_at:
```

Example:

```text
institution:
  Universitas ...

academic_period:
  2026/2027 Ganjil

record_type:
  KRS
```

A grade with no identifiable academic period should be:

```text
PARTIAL
```

rather than silently assigned to the current semester.

---

# 8. Semester Identity

Treat semester as a first-class key.

```text
student
+
academic_year
+
semester
+
record_type
```

Example:

```text
2026/2027
Ganjil
Grades
```

is different from:

```text
2025/2026
Genap
Grades
```

Never merge them without explicit evidence.

---

# 9. Navigation

Navigation must be deterministic.

Before reading a page verify:

```text
current host
current authenticated identity
current page identity
current academic period
current module
```

Do not assume:

```text
known URL
```

means:

```text
intended academic page
```

---

# 10. Read Workflow

Canonical read:

```text
SESSION
  ↓
PORTAL CONTEXT
  ↓
NAVIGATE
  ↓
VERIFY PAGE
  ↓
READ
  ↓
NORMALIZE
  ↓
FRESHNESS
  ↓
RETURN
```

Reads include:

```text
profile
academic status
grades
schedule
course offerings
prerequisites
quota
eligibility
current KRS
submission state
```

---

# 11. Academic Read Identity

Every result should identify:

```text
portal
academic period
record type
retrieval time
source page
```

Example:

```yaml
grades:
  portal: cyber-campus
  period: "2026/2027 Ganjil"
  source_page: grades
  retrieved_at: ...
```

---

# 12. Normalization

Convert raw portal data into typed records.

## Course

```yaml
course:
  code:
  name:
  credits:
  class:
  lecturer:
  schedule:
  room:
  quota:
  enrolled:
  remaining:
  prerequisites:
  eligibility:
```

Do not invent unavailable fields.

Use:

```text
null
unknown
not_exposed
```

when appropriate.

---

# 13. Grade Model

```yaml
grade:
  course_code:
  course_name:
  credits:
  letter:
  numeric:
  quality_points:
  period:
  status:
```

Preserve distinctions between:

```text
not_taken
registered
graded
incomplete
withheld
not_published
```

Do not calculate GPA using guessed values.

---

# 14. Schedule Model

```yaml
schedule:
  course_code:
  class:
  day:
  start:
  end:
  room:
  instructor:
  period:
```

Normalize time explicitly.

Check:

```text
same day
overlapping intervals
adjacent classes
room conflicts
```

Do not declare a conflict when time information is incomplete.

---

# 15. KRS Model

```yaml
krs:
  period:
  status:
  courses:
    - course_code:
      class:
      credits:
      status:
  total_credits:
  submitted:
  submitted_at:
  receipt:
```

Possible status:

```text
DRAFT
STAGED
SUBMITTED
APPROVED
LOCKED
UNKNOWN
```

---

# 16. Course Offering Model

```yaml
offering:
  course_code:
  class:
  credits:
  quota:
  enrolled:
  remaining:
  schedule:
  lecturer:
  prerequisites:
  eligibility:
  registration_window:
  source:
```

Quota is time-sensitive.

Therefore:

```text
offering.quota.freshness
```

must be available when used for KRS decisions.

---

# 17. Quota Analysis

Never say:

```text
"quota is available"
```

without current evidence.

Distinguish:

```text
OPEN
FULL
UNKNOWN
CLOSED
WINDOW_NOT_OPEN
WINDOW_CLOSED
```

For numeric quota:

```text
remaining = quota - enrolled
```

only when both values are current and compatible.

---

# 18. Prerequisite Analysis

Represent:

```text
course
  ↓
required prerequisite
  ↓
student academic record
```

Classify:

```text
SATISFIED
NOT_SATISFIED
IN_PROGRESS
WAIVED
UNKNOWN
```

Do not infer prerequisite satisfaction from course names alone.

---

# 19. Eligibility

Eligibility may depend on:

```text
semester
program
cohort
completed credits
prerequisites
academic status
registration window
quota
faculty rules
special restrictions
```

Each factor should be separately evaluated.

---

# 20. Credit Constraints

Check:

```text
minimum credits
maximum credits
program limit
semester limit
special overload rules
```

Output:

```yaml
credit_check:
  current:
  proposed:
  minimum:
  maximum:
  status:
```

Do not assume a universal credit ceiling.

Use current portal rules where exposed.

---

# 21. Schedule Conflict Detection

For proposed KRS:

```text
course A
  09:00-11:00

course B
  10:00-12:00
```

=> conflict.

Represent:

```yaml
conflict:
  course_a:
  course_b:
  day:
  overlap_start:
  overlap_end:
  severity:
```

Do not infer conflicts when:

```text
day unknown
time unknown
timezone ambiguous
```

---

# 22. Registration Window

Before KRS planning verify:

```text
registration_open
registration_close
current_time
portal_time
```

Classify:

```text
OPEN
NOT_YET_OPEN
CLOSED
UNKNOWN
```

Never use a historical deadline as current state.

---

# 23. Planning State

Planning state must be separate from portal state.

Example:

```yaml
plan:
  period: "2026/2027 Ganjil"
  additions:
    - course_code: IF101
      class: A
  removals:
    - course_code: IF204
  total_credits_after:
  conflicts:
  quota_risks:
  prerequisite_failures:
  eligibility_failures:
```

A plan is not yet an action.

---

# 24. Dry Run

A KRS dry run must calculate:

```text
selected courses
removed courses
final credit count
schedule conflicts
quota risks
prerequisite failures
eligibility failures
registration window
existing KRS state
unknown conditions
```

No portal mutation.

Output:

```text
DRY_RUN_READY
DRY_RUN_BLOCKED
DRY_RUN_UNCERTAIN
```

---

# 25. Action Hash

Before approval generate a deterministic action hash.

Conceptually:

```text
sha256(
  portal
  +
period
  +
current_krs_hash
  +
additions
  +
removals
  +
selected_classes
)
```

Include:

```text
normalized course identifiers
class identifiers
action type
academic period
```

Do not hash mutable prose.

Store:

```yaml
approval_binding:
  action_hash:
  generated_at:
  plan_version:
```

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

# 27. Approval Expiration

Approval is not permanent.

Invalidate approval if:

```text
current KRS changes
offering changes
quota changes materially
prerequisite state changes
eligibility changes
registration window changes
session changes
portal context changes
action hash changes
```

Then:

```text
return to DRY_RUN
```

---

# 28. Pre-Execution Revalidation

Immediately before staging:

```text
1. session
2. identity
3. portal
4. academic period
5. current KRS
6. offerings
7. quota
8. prerequisites
9. eligibility
10. registration window
11. action hash
```

All relevant preconditions must still hold.

---

# 29. Optimistic Concurrency

Treat current KRS as mutable state.

Before write:

```text
approved_state_hash
```

must match:

```text
current_state_hash
```

If:

```text
approved_state_hash != current_state_hash
```

then:

```text
CONCURRENT_STATE_CHANGE
```

Stop.

Do not overwrite the newer portal state.

---

# 30. Stage

If the portal supports staging:

```text
APPROVED PLAN
   ↓
STAGE NARROW CHANGE
   ↓
READ BACK
   ↓
COMPARE
```

Staging must contain only the approved delta.

---

# 31. Stage Reconciliation

After staging read:

```text
expected
vs
observed
```

Compare:

```text
courses
classes
credits
status
```

Outcomes:

```text
MATCH
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

If mismatch:

```text
STOP
```

No final submission.

---

# 32. Final Approval

Final submission requires another explicit approval.

Reason:

```text
staged state
```

may differ from:

```text
original plan
```

Approval must reference:

```text
staged_state_hash
action_hash
current period
current KRS
```

---

# 33. Submit

Submit exactly once for the approved state unless the portal reports a clearly
retryable transport failure and the operation is proven idempotent.

Prefer:

```text
submit
↓
receive receipt/status
↓
verify
```

Do not blindly retry unknown submission outcomes.

---

# 34. Idempotency

For any KRS mutation determine whether the portal provides:

```text
request ID
submission ID
transaction ID
idempotency key
```

If present, preserve it.

If submission outcome is unknown:

```text
DO NOT SUBMIT AGAIN
```

until current portal state is verified.

This prevents duplicate or conflicting submissions.

---

# 35. Verification

After submission:

```text
1. return to KRS/status page
2. verify current state
3. verify period
4. verify courses
5. verify status
6. verify timestamp/receipt where available
```

Possible outcomes:

```text
NOT_CHANGED
PARTIALLY_APPLIED
FULLY_APPLIED
SUBMITTED
VERIFIED
UNKNOWN
```

---

# 36. Submission Confirmation

Strong confirmation evidence may include:

```text
portal status
submission timestamp
transaction/reference number
confirmation message
current KRS read-back
downloadable receipt
```

Prefer multiple independent portal signals.

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

# 38. Unknown Outcome

If the write request times out or the connection fails after transmission:

```text
SUBMISSION_OUTCOME_UNKNOWN
```

Then:

```text
READ CURRENT PORTAL STATE
```

Do not automatically retry.

---

# 39. Partial Application

If some changes were applied:

```text
PARTIALLY_APPLIED
```

Report:

```text
applied changes
not applied changes
observed portal state
remaining discrepancy
```

Do not automatically "fix" the discrepancy without a new approved plan.

---

# 40. Rollback

Rollback is only allowed when:

```text
portal supports safe reverse operation
```

and:

```text
new rollback approval exists
```

Do not invent rollback endpoints.

If the portal lacks rollback:

```text
manual corrective plan required
```

---

# 41. Existing Submission Protection

Before write:

```text
existing submission?
submission timestamp?
current status?
modifiable?
```

If already submitted:

```text
do not overwrite silently
```

Require an explicit new workflow for:

```text
edit
replace
resubmit
cancel
```

---

# 42. Evidence Model

Each important academic state gets provenance:

```yaml
evidence:
  source: portal_page
  portal:
  page:
  period:
  record_type:
  retrieved_at:
  freshness:
  value:
```

Distinguish:

```text
CURRENT_PORTAL
HISTORICAL_PORTAL
MEMORY
INFERENCE
```

---

# 43. Minimal Evidence

Do not retain more personal academic data than needed.

For example, to verify quota:

```text
course_code
class
quota
enrolled
remaining
retrieved_at
```

may be sufficient.

Do not unnecessarily retain:

```text
full student profile
full transcript
other unrelated personal records
```

---

# 44. Sensitive Data

Never log:

```text
password
OTP
MFA secret
session cookie
access token
refresh token
CSRF token
SSO credential
browser storage secret
```

Redact before:

```text
audit
error output
debug output
memory
reports
```

---

# 45. Academic Privacy

Treat as sensitive:

```text
student identifier
grades
academic standing
personal schedule
registration history
disciplinary data
advising information
```

Only expose the minimum required for the current task.

---

# 46. Portal Errors

Normalize errors:

```text
SESSION_EXPIRED
UNAUTHORIZED
FORBIDDEN
PAGE_NOT_FOUND
ACADEMIC_PERIOD_UNAVAILABLE
QUOTA_CHANGED
PREREQUISITE_CHANGED
ELIGIBILITY_CHANGED
REGISTRATION_WINDOW_CLOSED
KRS_STATE_CHANGED
SUBMISSION_UNKNOWN
PORTAL_ERROR
NETWORK_ERROR
```

Do not turn generic portal failure into:

```text
success
```

---

# 47. Navigation Failure

If deterministic navigation fails:

```text
NAVIGATION_UNCERTAIN
```

Do not guess:

```text
selector
form field
URL
button
endpoint
```

---

# 48. Unsupported Portal Behavior

When the portal's write behavior is undocumented or unclear:

```text
READ_ONLY_FALLBACK
```

Do not invent:

```text
POST route
field order
hidden endpoint
JavaScript function
request body
```

---

# 49. Evidence Conflict

If:

```text
current portal
```

says one thing and:

```text
memory / historical state
```

says another:

```text
current portal wins
```

If:

```text
two current portal pages
```

contradict:

```text
CONFLICTED_STATE
```

Do not execute consequential action until reconciled.

---

# 50. Cross-Session Continuity

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

# 51. Audit Trail

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

# 52. Audit Integrity

Where supported, use:

```text
previous_event_hash
current_event_hash
```

or equivalent tamper-evident chaining.

Do not fabricate immutable storage guarantees.

---

# 53. Read Contract

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

# 54. Write Contract

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

# 55. KRS Decision Matrix

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

# 56. Risk Classification

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

# 59. Reference Loading

When this skill is invoked:

```text
IF lifecycle execution is required
    -> read references/lifecycle.md

IF KRS planning/staging/submission is required
    -> read references/krs-staging.md

IF schema/freshness/security/audit rules are required
    -> read references/policies.md

IF multiple areas apply
    -> read all applicable references
```

Precedence:

```text
current authoritative portal state
    >
this skill
    >
reference files
    >
historical memory
    >
generic assumptions
```

When `xninetzy-academic-safety`, `xninetzy-uacc`, or another specialized skill
establishes a stricter safety requirement, the stricter requirement applies.

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

# 61. Golden KRS Workflow

```text
SESSION CHECK
    ↓
BIND ACADEMIC PERIOD
    ↓
READ CURRENT KRS
    ↓
READ OFFERINGS
    ↓
READ QUOTA
    ↓
READ PREREQUISITES
    ↓
READ ELIGIBILITY
    ↓
CHECK SCHEDULE
    ↓
CHECK CREDIT LIMIT
    ↓
DRY RUN
    ↓
ACTION HASH
    ↓
EXPLICIT APPROVAL
    ↓
IMMEDIATE REVALIDATION
    ↓
CURRENT-STATE HASH CHECK
    ↓
STAGE
    ↓
READ BACK
    ↓
STAGED-STATE RECONCILIATION
    ↓
FINAL EXPLICIT APPROVAL
    ↓
SUBMIT ONCE
    ↓
PORTAL VERIFICATION
    ↓
AUDIT
```

---

# 62. Golden Read Workflow

```text
SESSION CHECK
    ↓
PORTAL CONTEXT
    ↓
ACADEMIC PERIOD
    ↓
PAGE VERIFICATION
    ↓
READ
    ↓
NORMALIZE
    ↓
FRESHNESS
    ↓
RETURN STRUCTURED RESULT
```

---

# 63. Golden Verification Workflow

```text
CLAIMED MUTATION
    ↓
READ CURRENT PORTAL
    ↓
CHECK PERIOD
    ↓
CHECK RECORD
    ↓
CHECK STATUS
    ↓
CHECK RECEIPT
    ↓
COMPARE AGAINST APPROVED PLAN
    ↓
CLASSIFY RESULT
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

# 65. Final Principle

The Cyber Campus skill should function as:

```text
academic-state reader
+
context binder
+
planning engine
+
approval controller
+
safe mutation coordinator
+
portal verification system
+
audit layer
```

not as:

```text
blind browser automation
```

The authoritative lifecycle is:

```text
DISCOVER
→ SESSION-CHECK
→ BIND-CONTEXT
→ NAVIGATE
→ READ
→ NORMALIZE
→ FRESHNESS-CHECK
→ ANALYZE
→ DRY-RUN
→ HASH
→ APPROVE
→ REVALIDATE
→ STAGE
→ RECONCILE
→ FINAL-APPROVE
→ SUBMIT
→ CONFIRM
→ AUDIT
```

The ultimate invariant is:

> **No mutation without a fresh approved plan, no submission without revalidation, and no success claim without authoritative portal confirmation.**

---
