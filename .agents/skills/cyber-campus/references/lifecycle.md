# Cyber Campus — Full Lifecycle

This reference expands the Cyber Campus lifecycle into an operational state machine.

Read this reference when:

```text
the core SKILL.md is insufficient
multiple portal states must be coordinated
a protected academic read is required
a KRS mutation is being prepared
a staged write is being executed
submission state must be verified
a workflow resumes after interruption
an unexpected portal state occurs
```

The lifecycle is:

```text
01 DISCOVER
02 SESSION-CHECK
03 BIND-CONTEXT
04 NAVIGATE
05 READ
06 NORMALIZE
07 FRESHNESS-CHECK
08 ANALYZE
09 DRY-RUN
10 HASH
11 APPROVE
12 REVALIDATE
13 STAGE
14 VERIFY
15 FINAL-APPROVE
16 SUBMIT
17 CONFIRM
18 AUDIT
```

The practical mutation workflow is therefore:

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
→ VERIFY
→ FINAL-APPROVE
→ SUBMIT
→ CONFIRM
→ AUDIT
```

`krs-staging.md` provides the deeper mutation protocol for the KRS-specific stages.

---

# 1. Core Authority Model

## 1.1 Portal is authoritative for current academic state

For current state, prefer:

```text
current verified portal state
    >
current official portal message/state
    >
current official academic metadata
    >
previous verified portal state
    >
stored memory
    >
previous conversation
    >
cached data
    >
generic assumption
```

Current portal state is authoritative for:

```text
academic period
academic status
current KRS
registered courses
class groups
schedule
offerings
quota
prerequisites
eligibility
grades
registration window
submission status
portal deadlines
```

Do not silently override current portal data with memory.

---

# 2. Adapter Boundary

The portal adapter owns the technical mechanics of interacting with the portal.

The model owns:

```text
academic intent
interpretation
planning
analysis
```

The adapter owns:

```text
navigation
typed reads
supported typed writes
session interaction
portal-specific mechanics
```

Never invent:

```text
selectors
JavaScript
hidden endpoints
form field ordering
undocumented request bodies
portal identifiers
authentication internals
grade tokens
CAPTCHA answers
OTP values
```

If the adapter does not support an operation:

```text
UNSUPPORTED_OPERATION
```

and stop.

Do not improvise.

---

# 3. Lifecycle State Machine

Possible states:

```text
DISCOVERED
SESSION_VALID
CONTEXT_BOUND
READING
NORMALIZED
FRESH
ANALYZED
DRY_RUN_READY
APPROVAL_PENDING
APPROVED
REVALIDATING
STAGING
STAGED
STAGE_VERIFIED
FINAL_APPROVAL_PENDING
FINAL_APPROVED
SUBMITTING
SUBMITTED
CONFIRMED
AUDITED
```

Failure states:

```text
UNAUTHENTICATED
SESSION_EXPIRED
CHALLENGE_REQUIRED
BLOCKED
STALE
INVALIDATED
CONFLICTED
PARTIALLY_APPLIED
UNKNOWN
FAILED
UNSUPPORTED
```

No transition may skip a required gate.

---

# 4. Lifecycle Transition Rule

A transition is valid only when its preconditions are satisfied.

Conceptually:

```text
STATE
+
PRECONDITIONS
+
CURRENT EVIDENCE
    ↓
NEXT STATE
```

If preconditions are not satisfied:

```text
STOP
```

Do not force the transition.

---

# 5. Step 01 — DISCOVER

Determine:

```text
portal
institution
requested operation
target academic record
target period
read vs write
```

Example:

```text
User:
"Check my KRS."

Resolved intent:
read current KRS
```

For ambiguous requests:

```text
"What are my grades?"
```

discover:

```text
available academic periods
```

and select the intended period only when reliably determined.

---

# 6. Step 02 — SESSION-CHECK

Session states:

```text
UNKNOWN
UNAUTHENTICATED
AUTHENTICATED
EXPIRED
CHALLENGE_REQUIRED
BLOCKED
UNAVAILABLE
```

Before protected access:

```text
inspect session
↓
verify authenticated state
↓
verify identity
↓
continue
```

A previously authenticated browser session must not be assumed valid forever.

---

# 7. Login / Verification Boundary

When authentication is required:

```text
1. check existing session
2. initiate supported login flow
3. preserve portal sequence
4. wait for human verification when required
5. verify resulting authenticated state
```

Human verification includes:

```text
CAPTCHA
OTP
MFA
security challenge
```

The system must not:

```text
solve
infer
predict
bypass
automate
```

challenge responses.

It may report:

```text
verification required
verification completed
verification unavailable
```

without revealing the secret.

---

# 8. Session Binding

After successful authentication, bind:

```yaml
session_context:
  session_id:
  portal:
  identity:
  authenticated_at:
  last_verified_at:
  expires_at:
```

Never expose:

```text
cookies
tokens
passwords
browser storage
authorization headers
```

---

# 9. Step 03 — BIND-CONTEXT

Bind:

```text
institution
portal host
academic period
page
module
record type
identity
```

Example:

```yaml
portal_context:
  institution: "University"
  period: "2026/2027 Ganjil"
  page: "KRS"
  record_type: "current_registration"
```

A record without context is incomplete.

---

# 10. Step 04 — NAVIGATE

Use deterministic typed navigation.

At each navigation boundary verify:

```text
current host
current identity
current page
current module
current academic period
```

Do not assume a familiar route means the intended record.

---

# 11. Navigation Verification

A page is accepted only when enough identity evidence exists.

Possible signals:

```text
page title
section heading
academic period
record type
portal-provided identifier
navigation state
```

If page identity is ambiguous:

```text
NAVIGATION_UNCERTAIN
```

Stop before reading sensitive information.

---

# 12. Step 05 — READ

Read using typed adapter methods.

Examples:

```text
read_profile
read_academic_status
read_grades
read_schedule
read_offerings
read_prerequisites
read_eligibility
read_quota
read_krs
read_submission_status
```

Each reader returns:

```yaml
read_result:
  portal:
  period:
  record_type:
  values:
  source:
  retrieved_at:
  freshness:
```

---

# 13. Read Isolation

Do not retrieve unrelated academic information.

If the user asks:

```text
"Is IF101 still available?"
```

do not automatically retrieve:

```text
full transcript
full student profile
all semester grades
```

unless required.

Use minimum necessary data.

---

# 14. Step 06 — NORMALIZE

Convert raw portal output into stable typed records.

Supported types:

```text
StudentStatus
AcademicPeriod
GradeRecord
ScheduleEntry
CourseOffering
Prerequisite
Eligibility
Quota
KRSSelection
SubmissionState
```

---

# 15. Null Semantics

Never replace missing data with guesses.

Use explicit states:

```text
null
unknown
not_exposed
not_applicable
unavailable
```

Example:

```yaml
quota_remaining: null
quota_status: UNKNOWN
```

is preferable to:

```yaml
quota_remaining: 0
```

when the portal did not expose the value.

---

# 16. Grade Model

```yaml
grade:
  course_code:
  course_name:
  credits:
  grade:
  grade_points:
  semester:
  status:
```

Possible status:

```text
GRADED
INCOMPLETE
NOT_PUBLISHED
WITHHELD
NOT_TAKEN
UNKNOWN
```

Never calculate unsupported numeric values from letter grades unless the grading
scale is verified.

---

# 17. Schedule Model

```yaml
schedule:
  course_code:
  course_name:
  class_group:
  day:
  start_time:
  end_time:
  room:
  lecturer:
  semester:
```

Normalize:

```text
day
time
timezone
```

before comparison.

---

# 18. Course Offering Model

```yaml
offering:
  course_code:
  course_name:
  credits:
  class_group:
  lecturer:
  schedule:
  quota_total:
  quota_used:
  quota_remaining:
  prerequisites:
  eligibility:
  registration_status:
  period:
  retrieved_at:
```

The offering must be bound to an academic period.

---

# 19. KRS State Model

```yaml
krs:
  period:
  status:
  courses:
    - course_code:
      class_group:
      credits:
      status:
  total_credits:
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

# 20. Step 07 — FRESHNESS-CHECK

Every time-sensitive record receives:

```text
FRESH
STALE
UNKNOWN
UNAVAILABLE
```

Additional internal classification may be:

```text
LIVE
```

when the record was just verified.

---

# 21. Freshness Rules

Treat as especially volatile:

```text
quota
registration window
class availability
current KRS
submission status
seat availability
schedule changes
```

Refresh before consequential decisions when:

```text
enrollment may have changed
another session may have changed KRS
window status may have changed
offering may have changed
quota may have changed
```

---

# 22. Freshness Invalidation

Invalidate cached state when:

```text
session changes
academic period changes
KRS changes
registration window changes
offering changes
quota changes
portal reports a newer state
```

Do not continue using invalidated state.

---

# 23. Step 08 — ANALYZE

Analysis must consume normalized, context-bound state.

Typical checks:

```text
prerequisites
eligibility
credits
quota
schedule conflicts
registration window
academic restrictions
current KRS impact
```

Each result should contain:

```yaml
check:
  status:
  evidence:
  source:
  retrieved_at:
```

---

# 24. Prerequisite Analysis

Use:

```text
current portal rule
+
verified curriculum data
+
current academic record
```

Classify:

```text
SATISFIED
NOT_SATISFIED
IN_PROGRESS
WAIVED
UNKNOWN
```

Do not infer prerequisites from:

```text
course order
course names
historical assumptions
```

---

# 25. Eligibility Analysis

Evaluate each known constraint independently:

```text
program
cohort
academic status
completed credits
prerequisites
registration period
special restrictions
quota
```

Output:

```text
ELIGIBLE
INELIGIBLE
UNKNOWN
```

Do not collapse an unknown factor into eligible.

---

# 26. Quota Analysis

Use:

```text
quota_total
quota_used
quota_remaining
availability_state
snapshot_time
```

Availability:

```text
AVAILABLE
LIMITED
FULL
CLOSED
UNKNOWN
```

Quota is not permanent evidence.

---

# 27. Schedule Analysis

Group classes by day.

Detect:

```text
start_A < end_B
AND
start_B < end_A
```

when same-day intervals are known.

Adjacent:

```text
09:00–10:40
10:40–12:20
```

is not an overlap.

Classify uncertain times as:

```text
POSSIBLE_CONFLICT
```

not:

```text
DEFINITE_CONFLICT
```

---

# 28. Credit Analysis

Compute:

```text
sum(verified course credits)
```

Then compare with:

```text
minimum verified credit constraint
maximum verified credit constraint
```

If any selected credit value is unknown:

```text
TOTAL_CREDITS = UNKNOWN
```

unless the value can be reliably resolved.

---

# 29. Registration Window

Determine:

```text
window_open
window_close
portal_current_time
status
```

Possible:

```text
OPEN
NOT_YET_OPEN
CLOSED
UNKNOWN
```

Do not use device time as a substitute for portal time when the portal exposes its own clock.

---

# 30. Step 09 — DRY-RUN

Planning must remain mutation-free.

Input:

```text
current KRS
+
offerings
+
constraints
+
desired changes
```

Output:

```yaml
dry_run:
  plan_id:
  period:
  additions:
  removals:
  replacements:
  retained:
  credits_before:
  credits_after:
  conflicts:
  quota_risks:
  prerequisite_failures:
  eligibility_failures:
  window_status:
  unresolved:
  status:
```

Possible:

```text
READY
BLOCKED
UNCERTAIN
```

---

# 31. Dry-Run Safety Rule

During dry-run:

```text
NO SELECT
NO REMOVE
NO SAVE
NO SUBMIT
```

The adapter must expose read-only planning operations separately from mutation
operations.

---

# 32. Step 10 — HASH

Once the plan is ready, bind it to current state.

Create:

```text
plan_id
plan_version
snapshot_hash
action_hash
```

Use deterministic canonical serialization.

---

# 33. Snapshot Hash

Represents:

```text
relevant verified current portal state
```

Conceptually:

```text
HASH(
  portal
  + period
  + current KRS
  + relevant state
)
```

It is an integrity mechanism.

It is not academic evidence.

---

# 34. Action Hash

Represents:

```text
exact intended mutation
```

Conceptually:

```text
HASH(
  period
  + snapshot_hash
  + ordered action set
)
```

Include stable:

```text
course identifiers
class identifiers
action type
```

Exclude:

```text
credentials
cookies
temporary UI values
irrelevant presentation text
```

---

# 35. Plan Immutability

Once approval is requested:

```text
plan_version = immutable
```

Changing:

```text
course
class
action
period
constraint
```

creates:

```text
new plan_version
new action_hash
```

and invalidates prior approval.

---

# 36. Step 11 — APPROVE

Approval binds to:

```yaml
approval:
  plan_id:
  plan_version:
  period:
  snapshot_hash:
  action_hash:
  actions:
  approved_at:
  expires_at:
```

The user must approve the specific plan.

---

# 37. Approval Presentation

Show:

```text
Portal:
Academic Period:

Plan:
Plan Version:

Current KRS:
...

Add:
...

Remove:
...

Replace:
...

Credits Before:
Credits After:

Schedule Conflicts:
...

Prerequisite Issues:
...

Eligibility:
...

Quota Risks:
...

Action Hash:
...

Consequence:
...

Approval Required:
```

No ambiguous approval such as:

```text
"Proceed?"
```

without action details.

---

# 38. Approval Semantics

Approval means:

```text
approve this exact plan
```

not:

```text
approve whatever is currently on the portal
```

Do not reinterpret approval after state changes.

---

# 39. Step 12 — REVALIDATE

Immediately before every consequential mutation:

```text
session
identity
portal
period
current KRS
offerings
quota
prerequisites
eligibility
registration window
snapshot hash
action hash
```

must be checked.

---

# 40. State Drift

If a material difference exists:

```text
approved state
    !=
current state
```

then:

```text
approval = INVALID
```

Stop.

Return to:

```text
READ
→ NORMALIZE
→ ANALYZE
→ DRY-RUN
```

when a new plan is required.

---

# 41. Material Drift

Material examples:

```text
KRS changed
course disappeared
class changed
quota materially changed
eligibility changed
prerequisite changed
window closed
period changed
session identity changed
```

Non-material differences may be ignored only when portal semantics are known.

When uncertain:

```text
treat as material
```

---

# 42. Step 13 — STAGE

If supported:

```text
APPROVED
    ↓
REVALIDATE
    ↓
STAGE
```

The write must contain only the approved delta.

Do not submit the entire KRS unless that is the explicitly supported and approved
portal operation.

---

# 43. Narrow Mutation Principle

Prefer:

```text
ADD IF101-A
```

over:

```text
replace complete KRS payload
```

when the portal supports a narrow operation.

Minimize:

```text
fields
records
state transitions
```

to reduce unintended mutation.

---

# 44. Step 14 — VERIFY

After staging:

```text
read staged/current KRS
↓
normalize
↓
compare
```

Verify:

```text
every approved addition exists
every approved removal is absent
class groups match
credits match
no unexpected selections
no approved selection disappeared
period matches
portal reports expected state
```

---

# 45. Reconciliation Result

```text
MATCH
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

`MATCH` allows transition to final approval.

`PARTIAL_MATCH` and `MISMATCH` stop final submission.

---

# 46. Unexpected Mutation

If an unapproved change appears:

```text
UNEXPECTED_MUTATION
```

stop.

Do not automatically revert.

Do not automatically submit.

Create a new read/reconciliation state.

---

# 47. Step 15 — FINAL-APPROVE

Final submission requires a separate approval.

Bind:

```yaml
final_approval:
  plan_id:
  plan_version:
  action_hash:
  staged_snapshot_hash:
  approved_at:
  expires_at:
```

Final approval must refer to the verified staged state, not merely the original
planning state.

---

# 48. Final Approval Presentation

Show:

```text
Verified Staged KRS:
Academic Period:
Courses:
Class Groups:
Total Credits:

Original Plan:
...

Differences:
None / ...

Staged Snapshot Hash:
...

Submission Consequence:
...

Final Approval Required:
```

---

# 49. Step 16 — SUBMIT

Immediately before submission:

```text
session valid
identity valid
period valid
staged KRS valid
final approval valid
staged hash matches
```

Then:

```text
submit once
```

Do not modify the plan between final approval and submission.

---

# 50. Submission Idempotency

Use portal-provided:

```text
submission ID
transaction ID
request ID
idempotency key
```

where available.

If submission outcome is unknown:

```text
DO NOT RETRY BLINDLY
```

Read the portal first.

---

# 51. Timeout Semantics

Important case:

```text
submit request
↓
network timeout
```

State becomes:

```text
SUBMISSION_UNKNOWN
```

not:

```text
FAILED
```

until the portal state has been read.

---

# 52. Step 17 — CONFIRM

After submission:

```text
read portal
↓
verify period
↓
verify KRS
↓
verify status
↓
verify receipt/reference
```

Possible final states:

```text
NOT_CHANGED
PARTIALLY_APPLIED
SUBMITTED
CONFIRMED
UNKNOWN
```

---

# 53. Confirmation Evidence

Strong evidence may include:

```text
final KRS state
submission status
official confirmation page
receipt/reference
server-generated timestamp
portal status message
```

Do not treat:

```text
button click
browser navigation
HTTP 200
```

alone as proof of successful academic submission.

---

# 54. Step 18 — AUDIT

Record the minimum required:

```yaml
audit:
  plan_id:
  plan_version:
  action_hash:
  snapshot_hash:
  staged_snapshot_hash:
  approval_id:
  execution_phase:
  result:
  timestamp:
  evidence_refs:
```

Do not store:

```text
password
OTP
MFA secret
session cookie
authentication token
browser state
```

---

# 55. Evidence Provenance

Every consequential conclusion should preserve:

```text
portal
page
period
record type
retrieval time
evidence reference
freshness
```

Example:

```yaml
evidence:
  source: portal
  page: KRS
  period: "2026/2027 Ganjil"
  retrieved_at: "..."
  freshness: FRESH
```

---

# 56. Screenshot Evidence

When permitted and necessary, screenshots may document:

```text
KRS state
staged state
confirmation
receipt
```

Screenshots must be:

```text
minimal
relevant
secret-free
period-identifiable
```

A screenshot proves only what is visibly established.

---

# 57. Cross-Session Resume

A resumable workflow should preserve:

```text
session_id
plan_id
plan_version
period
snapshot_hash
action_hash
approval state
staging state
verification state
```

Before any mutation after resume:

```text
revalidate everything relevant
```

A previous approval does not survive material portal changes.

---

# 58. Checkpoint Model

Checkpoint:

```yaml
checkpoint:
  lifecycle_state:
  session_id:
  plan_id:
  plan_version:
  period:
  snapshot_hash:
  action_hash:
  staged_snapshot_hash:
  approval_state:
  timestamp:
```

Use checkpoints to resume safely.

Do not resume an expired approval or stale state.

---

# 59. Failure Handling

## Session expires

```text
SESSION_EXPIRED
→ stop
→ authenticate through supported flow
→ re-bind context
→ re-read state
```

## CAPTCHA/OTP/MFA required

```text
CHALLENGE_REQUIRED
→ stop automation
→ allow supported human verification
→ continue only after typed verification state
```

## Selector/page ambiguous

```text
NAVIGATION_UNCERTAIN
→ stop
```

## Quota changed

```text
STATE_INVALIDATED
→ invalidate affected plan
```

## KRS changed

```text
CONCURRENT_STATE_CHANGE
→ invalidate approval
```

## Stage differs from plan

```text
STAGE_MISMATCH
→ stop
```

## Submission confirmation missing

```text
SUBMISSION_UNKNOWN
→ read portal
→ do not blindly retry
```

---

# 60. Partial Success

A mutation may partially apply.

Workflow:

```text
attempt
 ↓
portal response
 ↓
read actual state
 ↓
compare
 ↓
classify
```

Possible:

```text
NOT_CHANGED
PARTIALLY_APPLIED
FULLY_APPLIED
SUBMITTED
UNKNOWN
```

Never infer state from the local adapter exception alone.

---

# 61. Recovery After Partial Success

Do not retry the original plan.

Instead:

```text
CURRENT ACTUAL STATE
       ↓
NEW SNAPSHOT
       ↓
NEW PLAN
       ↓
NEW ACTION HASH
       ↓
NEW APPROVAL
```

This prevents duplicate or conflicting mutations.

---

# 62. Recovery After Unknown Submission

```text
SUBMISSION_UNKNOWN
        ↓
READ CURRENT PORTAL
        ↓
is final state present?
   ┌────┴────┐
  yes       no
   ↓         ↓
CONFIRMED   determine whether
            safe new action exists
            ↓
          NEW PLAN
```

Never automatically submit again merely because the network timed out.

---

# 63. Recommendation State

Academic planning may produce:

```text
RECOMMENDED
```

KRS execution produces:

```text
PLANNED
APPROVED
STAGED
STAGE_VERIFIED
FINAL_APPROVED
SUBMITTED
CONFIRMED
```

Never say:

```text
"registered"
```

when the state is only:

```text
recommended
planned
approved
staged
```

---

# 64. Academic Learning Integration

When requested, Cyber Campus may provide verified academic context to the Learning
OS.

Flow:

```text
Cyber Campus
    ↓
Current Academic State
    ↓
Course / Prerequisite Constraints
    ↓
Learning OS
    ↓
Concept Map
    ↓
Study Roadmap
```

Example:

```text
Course:
Database Systems

Verified academic context:
currently registered

Potential learning concepts:
SQL
Normalization
Transactions
Indexing
```

Learning recommendations remain separate from portal mutation state.

---

# 65. Graph Integration

When graph storage exists, allowed evidence-backed relations include:

```text
Student
  └── enrolled_in ──> Course

Course
  └── requires ──> Course

Course
  └── supports ──> Concept

KRS Plan
  └── selects ──> Class

Class
  └── belongs_to ──> Course
```

Each relationship must retain:

```text
source
timestamp
evidence
confidence
```

Do not infer academic relationships from similarity alone.

---

# 66. Privacy Model

Treat as sensitive:

```text
student identity
grades
academic status
schedule
KRS
registration history
advising information
institutional restrictions
```

Use minimum necessary data.

For quota checking:

```text
course
class
quota
remaining
timestamp
```

may be sufficient.

Do not persist the complete academic profile unnecessarily.

---

# 67. Security Model

Never expose:

```text
passwords
session cookies
access tokens
refresh tokens
OTP
MFA secrets
CAPTCHA values
CSRF tokens
browser storage
hidden private portal HTML
```

Do not put these into:

```text
memory
audit
reports
screenshots
Lightning traces
debug logs
```

---

# 68. Truth Classification

For every important statement classify internally:

```text
CURRENT_PORTAL
PREVIOUS_PORTAL
MEMORY
INFERENCE
UNKNOWN
```

Example:

```text
CURRENT_PORTAL:
IF101 has 3 remaining seats.

MEMORY:
IF101 previously had 20 seats.

Conclusion:
current portal state wins.
```

---

# 69. Stop Conditions

Immediately stop the affected workflow when:

```text
session expired
challenge required
target identity unclear
page identity unclear
semester unclear
record identity unclear
quota materially changed
prerequisite changed
eligibility changed
registration window changed
KRS changed
approval expired
snapshot hash changed
action hash changed
stage mismatch
unexpected portal state
submission result unknown
scope broadened
adapter lacks required operation
```

Safe stop is preferable to speculative continuation.

---

# 70. Never-Do List

Never:

```text
solve CAPTCHA
bypass OTP
bypass MFA
guess selectors
guess hidden endpoints
guess form order
guess field names
guess academic period
guess quota
guess prerequisites
guess eligibility
guess submission result
reuse expired approval
overwrite current KRS silently
retry unknown write blindly
log credentials
log session secrets
merge unrelated semesters
```

---

# 71. Lifecycle Completion States

## READ_COMPLETE

Current requested academic data was retrieved and context-bound.

## PLAN_COMPLETE

A dry-run plan exists with verified constraints and explicit uncertainties.

## STAGE_COMPLETE

The approved KRS delta was staged and reconciled successfully.

## SUBMISSION_COMPLETE

The portal reports a submission event.

## CONFIRMED

The final portal state matches the intended result.

## PARTIAL

Useful state exists but one or more requested conditions remain unresolved.

## UNKNOWN

The actual portal state cannot be established reliably.

## BLOCKED

A required safety, authorization, session, or adapter condition prevents progress.

---

# 72. Completion Contract

Every lifecycle execution should expose:

```yaml
lifecycle_result:
  state:
  session:
  portal_context:
  academic_period:
  read_state:
  plan:
  approval:
  execution:
  verification:
  audit:
  uncertainties:
  evidence_refs:
```

For read-only operations:

```text
period
page
structured result
freshness
session status
evidence
```

For KRS mutation:

```text
plan_id
plan_version
snapshot_hash
action_hash
approval_id
staged_state
staged_snapshot_hash
final_approval
submission_state
confirmation_evidence
```

---

# 73. Golden Read Lifecycle

```text
DISCOVER
 ↓
SESSION-CHECK
 ↓
BIND-CONTEXT
 ↓
NAVIGATE
 ↓
READ
 ↓
NORMALIZE
 ↓
FRESHNESS-CHECK
 ↓
RETURN
```

No mutation.

---

# 74. Golden Planning Lifecycle

```text
READ CURRENT STATE
 ↓
NORMALIZE
 ↓
FRESHNESS
 ↓
ANALYZE
 ↓
DRY-RUN
 ↓
PLAN ID
 ↓
PLAN VERSION
 ↓
SNAPSHOT HASH
 ↓
ACTION HASH
 ↓
APPROVAL
```

No portal mutation before approval.

---

# 75. Golden Staging Lifecycle

```text
APPROVED PLAN
 ↓
REVALIDATE
 ↓
SNAPSHOT MATCH
 ↓
ACTION HASH MATCH
 ↓
STAGE
 ↓
READ BACK
 ↓
RECONCILE
 ↓
STAGE_VERIFIED
```

No final submission yet.

---

# 76. Golden Submission Lifecycle

```text
STAGE_VERIFIED
 ↓
FINAL APPROVAL
 ↓
REVALIDATE
 ↓
SUBMIT
 ↓
READ PORTAL
 ↓
VERIFY STATUS
 ↓
VERIFY FINAL KRS
 ↓
VERIFY RECEIPT
 ↓
CONFIRMED
 ↓
AUDIT
```

---

# 77. Overall Invariant

At every point:

```text
CURRENT STATE
+
INTENDED STATE
+
APPROVAL STATE
+
EXECUTION STATE
+
VERIFICATION STATE
```

must remain distinguishable.

Never collapse them.

---

# 78. Final Principle

The Cyber Campus lifecycle is successful only when the system can answer:

```text
What portal state was observed?

For which academic period?

What was normalized?

What did the user intend?

What exactly was approved?

What state existed immediately before mutation?

What was staged?

Did staged state match the approved plan?

What was finally submitted?

What does the portal currently confirm?

What evidence proves the result?
```

If those questions cannot be answered reliably:

```text
STOP
```

and classify the result as:

```text
PARTIAL
UNKNOWN
INVALIDATED
BLOCKED
```

rather than guessing.

> **The portal's verified current state is the final authority. Intention is not execution. Execution is not submission. Submission is not confirmation.**
