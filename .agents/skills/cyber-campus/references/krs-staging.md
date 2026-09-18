# Cyber Campus — KRS Staging

This reference defines the controlled workflow for preparing, approving, staging,
submitting, and verifying KRS changes.

Read this reference whenever the workflow can modify:

```text
KRS
course selection
class group selection
course removal
course replacement
course registration
KRS staging
KRS final submission
```

Core principle:

> **Plan against verified state, bind approval to an immutable plan identity, revalidate immediately before mutation, reconcile every staged result, and never infer submission success from transport success.**

Second principle:

> **A write request is an attempt. The portal's resulting state is the truth.**

---

# 1. State Machine

KRS state must be modeled explicitly.

```text
PLANNING
   ↓
DRY_RUN_READY
   ↓
APPROVAL_PENDING
   ↓
APPROVED
   ↓
REVALIDATING
   ↓
STAGING
   ↓
STAGED
   ↓
STAGE_VERIFIED
   ↓
FINAL_APPROVAL_PENDING
   ↓
FINAL_APPROVED
   ↓
SUBMITTING
   ↓
SUBMITTED
   ↓
CONFIRMED
```

Failure states:

```text
BLOCKED
INVALIDATED
PARTIALLY_APPLIED
UNKNOWN
FAILED
```

A state transition must never be implied from a previous state.

Example:

```text
STAGED
```

does not imply:

```text
SUBMITTED
```

and:

```text
SUBMITTED
```

does not automatically imply:

```text
CONFIRMED
```

---

# 2. Separation of Concerns

Keep these objects separate:

```text
CURRENT_PORTAL_STATE
PLAN
APPROVAL
STAGED_STATE
SUBMISSION
VERIFICATION
AUDIT
```

Do not mutate the plan merely because the portal changed.

Create a new plan/version when the intended action changes.

---

# 3. Planning vs Execution

KRS planning is read-only.

### Planning

May:

```text
read current KRS
read offerings
read quota
read prerequisites
read eligibility
read schedule
calculate credits
detect conflicts
construct a plan
calculate hashes
```

Must not:

```text
select course
remove course
save KRS
submit KRS
```

### Execution

May only begin after the appropriate approval gate has passed.

---

# 4. Required Planning Inputs

A valid plan should be based on:

```text
current KRS
available offerings
student eligibility
prerequisites
quota
credit constraints
schedule constraints
registration window
portal rules
desired courses
```

Any required input that cannot be verified becomes:

```text
UNKNOWN
```

Do not silently substitute memory.

---

# 5. Current KRS Snapshot

Before constructing the plan, create a canonical snapshot:

```yaml
snapshot:
  portal:
  academic_period:
  krs_status:
  courses:
    - course_code:
      class_group:
      credits:
      status:
  total_credits:
  retrieved_at:
  source:
  snapshot_hash:
```

The snapshot hash identifies the state against which the plan was created.

---

# 6. Snapshot Identity

A snapshot should include:

```text
portal identity
academic period
KRS status
selected course identifiers
selected class identifiers
credits
materially relevant registration state
```

Do not include unnecessary personal information in the hash input.

The hash is an integrity identifier, not a substitute for portal evidence.

---

# 7. Course Selection Model

Represent every proposed selection explicitly.

```yaml
selection:
  course_code:
  course_name:
  class_group:
  credits:
  action:
    ADD
    REMOVE
    KEEP
    REPLACE
```

Example:

```yaml
selection:
  course_code: IF101
  class_group: A
  credits: 3
  action: ADD
```

Do not represent:

```text
"take databases"
```

as a final executable action.

The executable plan must contain stable course/class identifiers.

---

# 8. Plan Identity

Every KRS plan receives:

```yaml
plan:
  plan_id:
  plan_version:
  academic_period:
  current_snapshot_hash:
  selected_classes:
  actions:
  total_credits:
  constraints:
  risks:
  uncertainties:
  created_at:
  planner_version:
```

`plan_id` identifies the logical plan.

`plan_version` identifies a specific immutable version of that plan.

---

# 9. Plan Immutability

Once a plan enters:

```text
APPROVAL_PENDING
```

the approved content must be immutable.

Changing:

```text
course
class
credit
action
academic period
constraint
```

creates a new:

```text
plan_version
```

and invalidates the previous approval.

Never mutate an approved plan in place.

---

# 10. Dry-Run Pipeline

Required:

```text
CURRENT KRS
     +
OFFERINGS
     +
PREREQUISITES
     +
ELIGIBILITY
     +
QUOTA
     +
SCHEDULE
     +
CREDIT CONSTRAINTS
     +
REGISTRATION WINDOW
     ↓
DRY-RUN PLAN
```

No portal mutation is allowed.

---

# 11. Dry-Run Output

Minimum:

```yaml
dry_run:
  plan_id:
  academic_period:
  additions:
  removals:
  retained:
  total_credits_before:
  total_credits_after:
  conflicts:
  prerequisite_failures:
  eligibility_failures:
  quota_risks:
  credit_constraint:
  registration_window:
  unresolved:
  status:
```

Status:

```text
READY
BLOCKED
UNCERTAIN
```

---

# 12. Credit Calculation

Calculate from verified course credits.

```text
Course A = 3
Course B = 3
Course C = 2
Course D = 4

Total = 12
```

Do not use:

```text
number_of_courses
```

as a substitute for:

```text
total_credits
```

If any selected course has unknown credits:

```text
total_credits = UNKNOWN
```

unless the missing value can be reliably resolved.

---

# 13. Credit Constraint Evaluation

Compare:

```text
current credits
+
planned additions
-
planned removals
=
proposed credits
```

against current verified constraints.

Represent:

```yaml
credit_constraint:
  minimum:
  maximum:
  proposed:
  status:
    PASS
    FAIL
    UNKNOWN
```

Never assume a universal maximum.

---

# 14. Schedule Model

Every selected class should expose:

```text
day
start_time
end_time
```

when available.

For same-day classes:

```text
start_A < end_B
AND
start_B < end_A
```

means overlap.

---

# 15. Schedule Conflict Classification

```yaml
conflict:
  course_a:
  class_a:
  course_b:
  class_b:
  day:
  overlap_start:
  overlap_end:
  status:
    DEFINITE
    POSSIBLE
    UNKNOWN
```

Do not silently select one course over another.

A definite conflict blocks the plan unless the portal explicitly permits the overlap.

---

# 16. Time Normalization

Before comparing schedules normalize:

```text
day
timezone
start
end
```

Handle:

```text
24-hour clock
12-hour clock
localized day names
timezone differences
```

If the portal's timezone is unknown:

```text
timezone = UNKNOWN
```

Do not infer it from the operator's local timezone.

---

# 17. Prerequisite Check

For each selected course:

```text
selected course
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

A failed prerequisite should include:

```text
course
required prerequisite
observed student status
source
```

---

# 18. Eligibility Check

Determine current eligibility from available portal state.

Possible factors:

```text
program
cohort
semester
academic status
completed credits
prerequisites
special restrictions
registration window
quota
faculty rules
```

Each condition should be independently represented.

---

# 19. Quota Check

Record:

```yaml
quota:
  capacity:
  enrolled:
  remaining:
  status:
  retrieved_at:
```

Possible status:

```text
AVAILABLE
FULL
CLOSED
NOT_OPEN
UNKNOWN
```

Quota is volatile.

A quota result should therefore be treated as:

```text
time-sensitive evidence
```

and revalidated before staging.

---

# 20. Registration Window

Record:

```yaml
registration_window:
  opens_at:
  closes_at:
  current_portal_time:
  status:
```

Status:

```text
OPEN
NOT_YET_OPEN
CLOSED
UNKNOWN
```

A plan created while the window is open may become invalid when the window closes.

---

# 21. Current-State Delta

Compute:

```text
current state
    ↓
planned state
```

as an explicit delta.

Example:

```yaml
delta:
  add:
    - IF101-A
  remove:
    - IF204-B
  keep:
    - IF220-C
```

The mutation engine should consume the delta, not reconstruct it from prose.

---

# 22. Action Types

Allowed KRS actions should be explicit:

```text
ADD
REMOVE
REPLACE
KEEP
```

Avoid ambiguous:

```text
MODIFY
SYNC
UPDATE_ALL
FIX
AUTO
```

unless the portal itself defines such an operation.

---

# 23. Replace Semantics

A replacement must be modeled as:

```text
REMOVE old class
+
ADD new class
```

unless the portal exposes a native atomic replacement action.

Do not assume:

```text
replace
```

is atomic.

---

# 24. Canonical Plan Representation

Before hashing, serialize the plan deterministically.

Canonical ordering:

```text
academic_period
↓
action types
↓
course_code
↓
class_group
↓
stable identifiers
```

Normalize:

```text
whitespace
case where semantically irrelevant
ordering
null representation
```

Never hash raw UI prose.

---

# 25. Snapshot Hash

Example conceptual input:

```text
HASH(
  portal
  + academic_period
  + normalized current KRS
)
```

Output:

```text
snapshot_hash
```

The hash allows detection of state drift.

It does not replace portal verification.

---

# 26. Action Hash

Example conceptual input:

```text
HASH(
  academic_period
  + current_snapshot_hash
  + normalized action_set
  + relevant verified constraints
)
```

Output:

```text
action_hash
```

Include:

```text
ADD
REMOVE
REPLACE
course
class
```

and other values that materially change the action.

Do not include:

```text
temporary UI state
irrelevant display text
sensitive credentials
```

---

# 27. Plan Hash vs Action Hash

Keep them separate.

```text
plan_hash
```

identifies the complete planned object.

```text
action_hash
```

identifies the executable mutation set.

A plan may contain explanatory metadata without changing the action hash.

---

# 28. Approval Binding

Approval must bind:

```yaml
approval:
  approval_id:
  plan_id:
  plan_version:
  academic_period:
  snapshot_hash:
  action_hash:
  approved_actions:
  approved_at:
  expires_at:
  approval_status:
```

Approval is valid only for this exact binding.

---

# 29. First Approval Gate

Show the operator:

```text
Target:
Academic Period:
Current KRS:
Plan ID:
Plan Version:

Add:
Remove:
Replace:

Credits Before:
Credits After:

Schedule Conflicts:
Prerequisite Issues:
Eligibility Issues:
Quota Risks:

Current Snapshot Hash:
Action Hash:

Consequence:
Approval Required:
```

Approval must be explicit.

---

# 30. Approval Expiration

Approval should have a bounded validity window.

Invalidate it when:

```text
approval expires
session expires
academic period changes
current KRS changes
offering changes materially
quota becomes invalid
prerequisite changes
eligibility changes
registration window changes
action hash changes
snapshot hash changes
```

---

# 31. Revalidation

Immediately before staging:

```text
1. session
2. identity
3. portal
4. academic period
5. current KRS
6. selected offerings
7. prerequisites
8. eligibility
9. quota
10. registration window
11. snapshot hash
12. action hash
```

All material preconditions must still match.

---

# 32. Optimistic Concurrency

Use:

```text
approved_snapshot_hash
```

against:

```text
current_snapshot_hash
```

If:

```text
approved != current
```

then:

```text
CONCURRENT_STATE_CHANGE
```

Invalidate approval.

Do not overwrite the portal's newer state.

---

# 33. Material vs Non-Material Changes

Not every difference must invalidate a plan.

### Material

```text
KRS course change
class group change
credit change
quota loss
eligibility change
prerequisite change
registration window
academic period
session identity
```

### Potentially non-material

```text
display ordering
cosmetic label
non-semantic formatting
```

Only use the non-material category when the portal semantics are known.

When uncertain:

```text
treat as material
```

---

# 34. Staging

If the portal supports a draft/staged KRS:

```text
APPROVED
   ↓
REVALIDATE
   ↓
STAGE DELTA
   ↓
READ STAGED STATE
```

The staging operation must be:

```text
narrow
specific
bounded
auditable
```

---

# 35. Narrow Mutation Rule

Only send the approved change set.

Do not send:

```text
all courses
all form fields
all browser state
```

when only:

```text
ADD IF101-A
```

is required.

Minimize mutation surface.

---

# 36. Staged State Snapshot

After staging create:

```yaml
staged_state:
  period:
  status:
  courses:
  total_credits:
  retrieved_at:
  source:
  staged_snapshot_hash:
```

Compare against:

```text
approved plan
```

---

# 37. Staged Reconciliation

Verify:

```text
every approved addition exists
every approved removal is absent
every class group matches
credits match
no unexpected courses appeared
no approved course disappeared
```

Classify:

```text
MATCH
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

---

# 38. Unexpected Mutation

If the portal shows an unapproved change:

```text
UNEXPECTED_MUTATION
```

Stop.

Do not continue to final submission.

Report:

```text
approved state
observed state
difference
possible cause
```

Do not attempt automatic correction.

---

# 39. Staging Approval vs Submission Approval

They are distinct:

```text
APPROVE STAGING
```

does not imply:

```text
APPROVE SUBMISSION
```

After staging verification require a new explicit approval for final submission.

---

# 40. Final Approval

Display:

```text
Verified Staged KRS:
Academic Period:
Courses:
Class Groups:
Total Credits:

Differences from Original Plan:
None / ...

Submission Consequence:
...

Staged Snapshot Hash:
...

Final Approval Required:
```

Final approval binds to:

```text
staged_snapshot_hash
action_hash
plan_id
plan_version
```

---

# 41. Final Preflight

Immediately before submission verify again:

```text
session
identity
academic period
staged KRS
current portal state
submission eligibility
registration window
final approval
staged snapshot hash
```

If any relevant state changes:

```text
INVALIDATE FINAL APPROVAL
```

---

# 42. Submission

Submit exactly the approved staged state.

Do not alter:

```text
courses
classes
credits
```

between final approval and submission.

---

# 43. Idempotency

Determine whether the portal provides:

```text
submission ID
transaction ID
request ID
idempotency key
```

Preserve it where available.

If submission outcome is uncertain:

```text
DO NOT BLINDLY RETRY
```

First verify current portal state.

---

# 44. Timeout After Submission

This case is critical:

```text
request sent
↓
network timeout
```

does **not** imply:

```text
submission failed
```

The correct state is:

```text
SUBMISSION_UNKNOWN
```

Then:

```text
READ CURRENT PORTAL STATE
```

before any retry.

---

# 45. Submission Verification

Verify through authoritative portal evidence.

Preferred signals:

```text
submission status
confirmation page
receipt/reference number
timestamp
final KRS
official confirmation message
```

Minimum verification should establish:

```text
period
status
selected courses
```

where the portal exposes them.

---

# 46. Confirmation Strength

Classify evidence:

```text
WEAK
  client-side acknowledgement only

MODERATE
  server response with transaction/reference

STRONG
  portal status + read-back state

VERY_STRONG
  portal status + receipt/reference + read-back state
```

Do not claim:

```text
confirmed
```

from weak evidence alone.

---

# 47. Success State

Only report:

```text
CONFIRMED
```

when the portal's authoritative state matches the intended final result.

Example:

```text
"The portal confirms KRS submission for 2026/2027 Ganjil."
```

not:

```text
"The submit button returned successfully."
```

---

# 48. Partial Success

If some mutations apply:

```yaml
result:
  status: PARTIALLY_APPLIED
  applied:
  not_applied:
  unexpected:
  current_state:
```

Do not retry the original complete plan.

Create a new plan from the actual state.

---

# 49. Failure Matrix

| Situation                                | Action                        |
| ---------------------------------------- | ----------------------------- |
| session expired before staging           | stop + session recheck        |
| KRS changed after approval               | invalidate approval           |
| quota changed                            | invalidate affected selection |
| prerequisite changed                     | invalidate affected selection |
| registration window closed               | stop                          |
| stage failed before request confirmation | re-read portal                |
| stage outcome unknown                    | re-read portal                |
| stage partially applied                  | classify actual state         |
| staged state mismatch                    | stop                          |
| final approval expired                   | stop                          |
| submission timeout                       | verify before retry           |
| submission outcome unknown               | do not retry blindly          |
| receipt unavailable                      | verify portal state           |
| final state mismatch                     | classify unknown/partial      |

---

# 50. Never Retry Blindly

Never do:

```text
submit
↓ timeout
↓
submit again
```

Instead:

```text
submit
↓
unknown
↓
read portal
↓
determine actual state
↓
create new plan if necessary
```

This is essential because a timeout can occur after the portal has already accepted
the request.

---

# 51. Screenshot Evidence

Screenshots may be captured when permitted and useful.

Useful targets:

```text
final KRS
staged KRS
confirmation page
receipt
important state transition
```

A screenshot should clearly identify:

```text
portal
academic period
relevant state
```

Avoid unnecessary:

```text
student identifiers
session information
credentials
private unrelated records
```

A screenshot is evidence only for what it visibly establishes.

---

# 52. Portal Page Evidence

For every consequential state capture:

```yaml
page_evidence:
  page:
  period:
  visible_status:
  retrieved_at:
  screenshot_ref:
  source_ref:
```

Do not claim a screenshot proves hidden data that is not visible.

---

# 53. Receipt Handling

If the portal provides a receipt:

```yaml
receipt:
  reference:
  status:
  period:
  timestamp:
  source:
```

Do not store unnecessary personal information.

Never place secret session data in receipt metadata.

---

# 54. Audit Record

Minimum audit:

```yaml
audit:
  plan_id:
  plan_version:
  action_hash:
  snapshot_hash:
  staged_snapshot_hash:
  approval_id:
  execution_phase:
  timestamp:
  result:
  evidence_refs:
```

Record:

```text
PLAN_CREATED
DRY_RUN_COMPLETED
APPROVAL_RECEIVED
REVALIDATION_COMPLETED
STAGE_STARTED
STAGE_VERIFIED
FINAL_APPROVAL_RECEIVED
SUBMISSION_STARTED
SUBMISSION_RESULT
CONFIRMATION_COMPLETED
```

---

# 55. Sensitive Data Protection

Never log:

```text
password
OTP
MFA secret
session cookie
access token
refresh token
CSRF token
raw browser storage
```

Academic data should be minimized.

Do not place full transcripts or unrelated personal records into the KRS audit record
when only course-selection evidence is needed.

---

# 56. Recommendation Boundary

Keep these states distinct:

```text
RECOMMENDED
PLANNED
APPROVED
STAGED
STAGE_VERIFIED
FINAL_APPROVED
SUBMITTED
CONFIRMED
```

Examples:

```text
RECOMMENDED:
"The course fits the stated constraints."

PLANNED:
"The course is included in Plan KRS-123."

APPROVED:
"The user approved Plan KRS-123."

STAGED:
"The portal accepted the selection into staged state."

SUBMITTED:
"The portal reports a submission action."

CONFIRMED:
"The final portal state matches the intended submission."
```

Never collapse them.

---

# 57. New Plan After State Drift

If the portal changes materially:

```text
old_plan
   ↓
INVALIDATED
   ↓
read current state
   ↓
new snapshot
   ↓
new plan_version
   ↓
new action_hash
   ↓
new approval
```

Do not mutate the old approved plan to make it fit the new portal state.

---

# 58. Rollback

Rollback may only be considered if:

```text
portal explicitly supports safe reverse action
```

and:

```text
new rollback plan
+
new approval
```

exist.

Never invent a rollback endpoint.

If rollback is unavailable:

```text
MANUAL_CORRECTION_REQUIRED
```

---

# 59. State Reconciliation After Failure

Whenever a mutation fails or becomes uncertain:

```text
INTENDED STATE
      vs
ACTUAL PORTAL STATE
```

must be compared.

Possible:

```text
NO_CHANGE
PARTIAL_CHANGE
FULL_CHANGE
SUBMITTED
UNKNOWN
```

Never infer actual state from the local tool's exception alone.

---

# 60. Plan Integrity

Plan execution must verify:

```text
plan_id
plan_version
action_hash
current_snapshot_hash
```

before mutation.

If any identifier does not match:

```text
PLAN_INTEGRITY_FAILURE
```

Stop.

---

# 61. Concurrency Protection

Potential concurrent changes include:

```text
another browser tab
mobile portal
advisor/admin action
automatic portal update
quota consumption
another agent/session
```

Any material external change invalidates the stale plan.

Never assume exclusive control unless the portal explicitly provides such a guarantee.

---

# 62. Completion Contract

KRS planning is complete when:

```text
[ ] current KRS read
[ ] academic period bound
[ ] offerings verified
[ ] prerequisites checked
[ ] eligibility checked
[ ] quota checked
[ ] schedule checked
[ ] credit constraints checked
[ ] registration window checked
[ ] dry run generated
[ ] plan ID created
[ ] plan version created
[ ] snapshot hash generated
[ ] action hash generated
[ ] uncertainties recorded
```

KRS staging is complete when:

```text
[ ] approval received
[ ] approval still valid
[ ] session revalidated
[ ] current state revalidated
[ ] snapshot hash matches
[ ] action hash matches
[ ] narrow mutation executed
[ ] staged state read back
[ ] staged state reconciled
```

KRS submission is complete when:

```text
[ ] final approval received
[ ] staged state revalidated
[ ] staged snapshot matches
[ ] submission executed
[ ] submission outcome verified
[ ] final KRS read back
[ ] receipt/status captured where available
[ ] audit record generated
```

---

# 63. Final Golden Workflow

```text
CURRENT KRS
    ↓
CURRENT OFFERINGS
    ↓
PREREQUISITES
    ↓
ELIGIBILITY
    ↓
QUOTA
    ↓
SCHEDULE
    ↓
CREDIT CONSTRAINTS
    ↓
REGISTRATION WINDOW
    ↓
DRY RUN
    ↓
PLAN ID + VERSION
    ↓
SNAPSHOT HASH
    ↓
ACTION HASH
    ↓
EXPLICIT APPROVAL
    ↓
IMMEDIATE REVALIDATION
    ↓
CONCURRENCY CHECK
    ↓
STAGE
    ↓
READ BACK
    ↓
RECONCILE
    ↓
EXPLICIT FINAL APPROVAL
    ↓
FINAL REVALIDATION
    ↓
SUBMIT
    ↓
READ PORTAL STATE
    ↓
VERIFY RECEIPT / STATUS
    ↓
CONFIRMED
    ↓
AUDIT
```

---

# 64. Final Rule

The system must always be able to answer:

```text
What was the portal state before planning?

What exactly was approved?

What exact mutation was authorized?

Did the portal state change during planning?

What was actually staged?

Does staged state match the approved plan?

Was final submission separately approved?

What does the portal currently confirm?

What evidence proves that result?
```

If any of these cannot be established:

```text
do not guess
do not silently retry
do not silently repair
do not claim success
```

Return:

```text
PARTIAL
UNKNOWN
INVALIDATED
or
BLOCKED
```

as appropriate.

> **The authoritative result of a KRS operation is the verified portal state, not the agent's intention, the action hash, the browser result, or the absence of an error.**
