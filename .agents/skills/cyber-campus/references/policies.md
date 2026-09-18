# Cyber Campus — Policies, Schemas, and Audit

This reference defines the canonical typed contracts for Cyber Campus.

Read this reference when:

```text
implementing portal readers
implementing portal writers
normalizing academic data
implementing freshness checks
building KRS plans
binding approvals
recording consequential actions
generating completion results
auditing execution
validating lifecycle transitions
```

This file defines **policy and data contracts**.

Operational lifecycle behavior belongs to:

```text
../SKILL.md
./lifecycle.md
./krs-staging.md
```

---

# 1. Contract Principles

The following invariants are mandatory:

```text
CURRENT PORTAL STATE
    ≠
STORED MEMORY

RECOMMENDATION
    ≠
PLAN

PLAN
    ≠
APPROVAL

APPROVAL
    ≠
EXECUTION

EXECUTION
    ≠
VERIFICATION

SUBMISSION
    ≠
CONFIRMATION
```

The system must preserve these distinctions throughout the workflow.

The final authoritative result is:

```text
VERIFIED CURRENT PORTAL STATE
```

not:

```text
local intent
local state
browser state
HTTP success
adapter completion
submission request
```

---

# 2. Standard Read Contract

Every normal academic read should produce the relevant subset of:

```yaml
read_response:
  academic_context:
    institution:
    portal:
    academic_period:
    page:
    record_type:

  session:
    status:
    identity_bound:

  data:
    records: []

  constraints:
    applicable: []

  freshness:
    status:
    retrieved_at:
    observed_at:
    source:

  conflicts: []

  uncertainty: []

  evidence:
    refs: []

  next_action:
    type:
    reason:
```

Human-readable rendering:

```text
Academic Period:
Page / Domain:
Record Type:

Session:
Freshness:

Requested Data:
Relevant Constraints:

Conflicts:
Uncertainty:

Evidence:

Next Action:
```

Only include fields relevant to the request.

---

# 3. Standard KRS Plan Contract

A KRS plan must contain enough information to reconstruct the intended mutation.

```yaml
krs_plan:
  plan_id:
  plan_version:

  portal:
  academic_period:

  current_state:
    snapshot_hash:
    total_credits:
    selections: []

  intended_actions:
    additions: []
    removals: []
    replacements: []
    retained: []

  analysis:
    prerequisite_status:
    quota_status:
    schedule_conflicts:
    eligibility:
    credit_constraint:
    registration_window:
    unresolved: []

  integrity:
    snapshot_hash:
    action_hash:

  approval:
    status:
    approval_id:
    approved_at:
    expires_at:

  execution:
    state:

  verification:
    state:
    evidence_refs: []
```

---

# 4. Canonical KRS Action Model

Each action must be explicit.

```yaml
krs_action:
  action_id:
  action_type:
  course_code:
  class_group:
  credits:
  source:
```

Allowed action types:

```text
ADD
REMOVE
KEEP
REPLACE
```

`REPLACE` is logically treated as:

```text
REMOVE old selection
+
ADD new selection
```

unless the portal exposes a verified atomic replacement operation.

Never interpret:

```text
CHANGE
UPDATE
MODIFY
```

as an execution primitive unless explicitly supported by the adapter.

---

# 5. Academic Record Schemas

## 5.1 Academic Period

```yaml
academic_period:
  period_id:
  label:
  academic_year:
  term:
  status:
  source:
  retrieved_at:
```

The period identifier must come from verified portal or official institutional
data where available.

---

## 5.2 Academic Status

```yaml
academic_status:
  status:
  status_code:
  effective_from:
  effective_until:
  source:
  retrieved_at:
```

Allowed interpretation states:

```text
ACTIVE
REGISTERED
ON_LEAVE
GRADUATED
ACADEMIC_HOLD
ADMINISTRATIVE_RESTRICTION
OTHER
UNKNOWN
```

Use the portal's exact terminology whenever possible.

Do not infer institutional consequences that the portal does not explicitly report.

---

## 5.3 Grade Record

```yaml
grade_record:
  course_code:
  course_name:
  credits:
  grade:
  grade_points:
  semester:
  status:
  source:
  retrieved_at:
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

A missing grade must not be converted into a failing grade or zero.

---

## 5.4 Schedule Entry

```yaml
schedule_entry:
  course_code:
  course_name:
  class_group:
  day:
  start_time:
  end_time:
  timezone:
  room:
  lecturer:
  semester:
  source:
  retrieved_at:
```

Unknown values remain unknown.

Never manufacture:

```text
room
lecturer
time
day
class group
```

from assumptions.

---

## 5.5 Course Offering

```yaml
course_offering:
  course_code:
  course_name:
  credits:
  class_group:
  lecturer:
  schedule: []

  quota:
    total:
    used:
    remaining:
    availability:
    observed_at:

  prerequisites: []
  eligibility:
  registration_status:

  academic_period:
  source:
  retrieved_at:
```

Availability:

```text
AVAILABLE
LIMITED
FULL
CLOSED
UNKNOWN
```

---

## 5.6 Prerequisite

```yaml
prerequisite:
  requirement_id:
  type:
  course_code:
  minimum_grade:
  evidence_ref:
  status:
```

Status:

```text
SATISFIED
NOT_SATISFIED
IN_PROGRESS
WAIVED
NOT_REQUIRED
UNKNOWN
```

Only verified prerequisite relationships may be used for consequential decisions.

---

## 5.7 Eligibility

```yaml
eligibility:
  status:
  reasons: []
  constraints: []
  evidence_refs: []
```

Allowed result:

```text
ELIGIBLE
INELIGIBLE
UNKNOWN
```

Do not collapse:

```text
UNKNOWN
```

into:

```text
ELIGIBLE
```

---

## 5.8 Quota

```yaml
quota:
  total:
  used:
  remaining:
  availability:
  observed_at:
  source:
```

Quota values are volatile.

A historical quota observation must always remain distinguishable from a current observation.

---

## 5.9 KRS Selection

```yaml
krs_selection:
  course_code:
  course_name:
  class_group:
  credits:
  schedule: []
  status:
  conflict:
  eligibility:
  source:
  retrieved_at:
```

---

# 6. Null and Unknown Policy

Missing data must use explicit semantics.

Allowed values include:

```text
null
UNKNOWN
NOT_EXPOSED
NOT_APPLICABLE
UNAVAILABLE
```

The system must not silently substitute:

```text
0
false
empty string
eligible
available
no conflict
```

when the portal did not establish those values.

This distinction is especially important for:

```text
quota
prerequisites
eligibility
grades
schedule
submission status
```

---

# 7. Provenance Contract

Every consequential academic fact should retain provenance.

```yaml
evidence:
  source_type:
  portal:
  page:
  academic_period:
  record_type:
  retrieved_at:
  observed_at:
  locator:
  evidence_ref:
```

Possible `source_type`:

```text
CURRENT_PORTAL
OFFICIAL_INSTITUTIONAL_DATA
PREVIOUS_PORTAL
MEMORY
USER_PROVIDED
INFERENCE
UNKNOWN
```

Only current verified portal data should be treated as authoritative for current portal state.

---

# 8. Evidence Strength

Evidence should be classified independently from confidence.

```text
DIRECT
DERIVED
INFERRED
UNKNOWN
```

Examples:

```text
DIRECT
portal explicitly reports quota_remaining = 5

DERIVED
credits_after = sum(selected course credits)

INFERRED
schedule appears to belong to the selected class
based on an adapter-level mapping

UNKNOWN
portal does not expose prerequisite details
```

Consequential writes must not rely exclusively on `INFERRED` or `UNKNOWN` evidence.

---

# 9. Freshness Contract

Every time-sensitive read receives:

```text
FRESH
STALE
UNKNOWN
UNAVAILABLE
```

Optional implementation-level state:

```text
LIVE
```

when the value was read during the current operation.

Freshness metadata:

```yaml
freshness:
  status:
  retrieved_at:
  observed_at:
  source:
  ttl:
  expires_at:
```

---

# 10. Freshness Classes

Recommended freshness classes:

```text
VOLATILE
SHORT_LIVED
STABLE
HISTORICAL
```

Typical classification:

```text
quota                  VOLATILE
current KRS            VOLATILE
submission status      VOLATILE
registration window   VOLATILE
offerings              SHORT_LIVED
schedule               SHORT_LIVED
eligibility            SHORT_LIVED
prerequisites          STABLE
published grades       STABLE
historical transcript  HISTORICAL
```

Actual TTL values must be configured by the institution/adapter rather than
hard-coded globally.

---

# 11. Freshness Invalidation

Cached academic state becomes invalid when:

```text
session changes
identity changes
academic period changes
KRS changes
offering changes
quota changes
registration window changes
portal reports a newer state
another write is detected
```

After invalidation:

```text
cached state
→ STALE
```

Never silently continue treating it as current.

---

# 12. Freshness Gate for Consequential Actions

Before a consequential mutation, the following must be current enough for the
operation:

```text
session
identity
academic period
current KRS
selected offering
quota
eligibility
prerequisite constraints
registration window
```

If one required component is:

```text
STALE
UNKNOWN
UNAVAILABLE
```

then:

```text
BLOCK
```

unless the adapter explicitly verifies that the value is irrelevant to the
requested mutation.

---

# 13. Session Contract

```yaml
session:
  status:
  identity:
  portal:
  authenticated_at:
  last_verified_at:
  expires_at:
```

Allowed status:

```text
UNKNOWN
UNAUTHENTICATED
AUTHENTICATED
EXPIRED
CHALLENGE_REQUIRED
BLOCKED
UNAVAILABLE
```

Protected reads require:

```text
AUTHENTICATED
```

Protected writes require:

```text
AUTHENTICATED
+
identity verified
```

Secrets must never be placed in this object.

---

# 14. Read vs Write Contract

## Read

Examples:

```text
grades
schedule
academic status
offerings
prerequisites
eligibility
quota
current KRS
submission status
```

A read operation:

```text
must verify context
must use a typed reader
must preserve provenance
must expose freshness
must not mutate academic state
```

No execution approval is required for ordinary read-only operations.

---

## Write

Examples:

```text
select course
remove course
modify KRS
save KRS
stage KRS
submit KRS
```

A consequential write requires:

```text
read
→ normalize
→ analyze
→ dry-run
→ hash
→ approval
→ revalidate
→ execute
→ verify
```

The exact staging and final-submission protocol is defined in:

```text
./krs-staging.md
```

---

# 15. Write Scope Contract

A writer receives an explicit mutation envelope.

```yaml
write_request:
  plan_id:
  plan_version:
  academic_period:
  snapshot_hash:
  action_hash:
  actions: []
  approval_id:
  execution_phase:
```

The adapter must reject:

```text
missing plan identity
missing approval
wrong academic period
unexpected action
stale snapshot
wrong action hash
broader mutation than approved
```

---

# 16. Approval Contract

Approval is immutable and action-bound.

```yaml
approval:
  approval_id:
  plan_id:
  plan_version:
  academic_period:
  snapshot_hash:
  action_hash:
  action_summary:
  approved_at:
  expires_at:
  status:
```

Allowed status:

```text
NOT_REQUIRED
PENDING
APPROVED
EXPIRED
INVALIDATED
CONSUMED
REVOKED
```

Approval means approval of:

```text
THIS PLAN
+
THIS VERSION
+
THIS SNAPSHOT
+
THESE ACTIONS
```

It must never mean:

```text
"do whatever is currently appropriate"
```

---

# 17. Approval Invalidation

An approval becomes invalid when:

```text
plan changes
plan version changes
academic period changes
snapshot hash changes
action hash changes
approval expires
session identity changes materially
staged state diverges
user revokes approval
```

Invalid approval cannot be reused.

---

# 18. Plan Integrity

Two hashes must remain separate.

```text
snapshot_hash
```

represents the verified state from which the plan was created.

```text
action_hash
```

represents the exact intended mutation.

They answer different questions:

```text
snapshot_hash:
"What state was approved?"

action_hash:
"What exact change was approved?"
```

Changing either invalidates the approval binding.

---

# 19. Audit Event Schema

For consequential actions:

```yaml
audit_event:
  event_id:
  timestamp:

  actor:
  portal:
  academic_period:

  plan:
    plan_id:
    plan_version:
    snapshot_hash:
    action_hash:

  approval:
    approval_id:
    status:

  execution:
    phase:
    action_type:
    result:

  verification:
    status:
    evidence_refs: []

  receipt:
    reference:
    timestamp:

  errors: []
```

---

# 20. Audit Event Types

Recommended event types:

```text
PLAN_CREATED
PLAN_MODIFIED
APPROVAL_REQUESTED
APPROVED
APPROVAL_INVALIDATED
REVALIDATION_STARTED
REVALIDATION_FAILED
STAGING_STARTED
STAGING_COMPLETED
STAGING_RECONCILED
FINAL_APPROVAL_REQUESTED
FINAL_APPROVED
SUBMISSION_STARTED
SUBMISSION_COMPLETED
SUBMISSION_UNKNOWN
VERIFICATION_STARTED
VERIFICATION_COMPLETED
PARTIAL_RESULT
FAILURE
AUDIT_COMPLETED
```

Events should be append-only.

Do not rewrite historical execution events to make an unsuccessful action appear
successful.

---

# 21. Audit Privacy Policy

Never persist:

```text
passwords
session cookies
access tokens
refresh tokens
authorization headers
CAPTCHA answers
OTP values
MFA secrets
CSRF secrets
browser storage
raw private requests
raw hidden portal HTML
```

Do not place secrets into:

```text
audit logs
memory
reports
screenshots
debug traces
checkpoint files
plan hashes
```

Use references or redacted metadata when necessary.

---

# 22. Data Minimization

Persist only information necessary for:

```text
current task
integrity verification
execution recovery
auditability
user-visible explanation
```

Example:

A quota audit may require:

```yaml
quota_evidence:
  course_code:
  class_group:
  remaining:
  observed_at:
  evidence_ref:
```

It does not require the student's complete academic profile.

---

# 23. Recommendation Boundary

Academic reasoning can produce:

```text
RECOMMENDED
```

but this does not mutate the portal.

Formal KRS lifecycle:

```text
RECOMMENDED
    ↓
PLANNED
    ↓
APPROVED
    ↓
STAGED
    ↓
STAGE_VERIFIED
    ↓
FINAL_APPROVED
    ↓
SUBMITTED
    ↓
CONFIRMED
```

These states must never be collapsed.

For example:

```text
RECOMMENDED
```

must never be rendered as:

```text
REGISTERED
```

and:

```text
SUBMITTED
```

must not automatically be rendered as:

```text
CONFIRMED
```

---

# 24. Execution State Contract

Allowed execution states:

```text
NOT_EXECUTED
PLANNING
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
PARTIALLY_APPLIED
UNKNOWN
FAILED
BLOCKED
INVALIDATED
```

`CONFIRMED` is only valid after portal verification.

---

# 25. Verification Contract

Every consequential write must produce a verification result.

```yaml
verification:
  status:
  verified_at:
  portal_state:
  expected_state:
  match:
  differences: []
  evidence_refs: []
```

Allowed status:

```text
MATCH
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

Rules:

```text
MATCH
→ may continue

PARTIAL_MATCH
→ stop

MISMATCH
→ stop

UNKNOWN
→ stop
```

No final submission may proceed from:

```text
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

---

# 26. Submission Contract

```yaml
submission:
  plan_id:
  plan_version:
  action_hash:
  final_approval_id:

  request_id:
  transaction_id:

  submitted_at:
  portal_status:
  result:
```

Possible result:

```text
SUBMITTED
PARTIALLY_APPLIED
NOT_CHANGED
UNKNOWN
FAILED
```

A network timeout after request transmission must initially be classified as:

```text
UNKNOWN
```

until the portal state is re-read.

---

# 27. Confirmation Contract

Confirmation requires evidence from the portal.

```yaml
confirmation:
  status:
  verified_at:
  academic_period:
  current_krs:
  submission_status:
  receipt:
  evidence_refs: []
```

Allowed status:

```text
CONFIRMED
PARTIAL
UNKNOWN
FAILED
```

`CONFIRMED` requires:

```text
verified portal state
+
expected result
+
no unexplained material difference
```

---

# 28. Standard Submission Output

Human-readable rendering:

```text
Academic Period:
Plan ID:

Approved Action:
...

Staged Result:
...

Final Approval:
...

Submission Result:
...

Portal Confirmation:
...

Timestamp:
...

Receipt / Reference:
...

Audit Status:
...
```

---

# 29. Standard Read Output

Human-readable rendering:

```text
Academic Period:
Page / Domain:
Record Type:

Freshness:
Session Status:

Requested Data:
...

Relevant Constraints:
...

Conflicts / Uncertainty:
...

Evidence:
...

Next Action:
...
```

The output must clearly distinguish:

```text
verified fact
derived result
uncertainty
recommended action
```

---

# 30. Standard KRS Plan Output

Human-readable rendering:

```text
Academic Period:
...

Current KRS:
...

Proposed Selections:
...

Total Credits:
...

Prerequisite Status:
...

Quota Status:
...

Schedule Conflicts:
...

Eligibility:
...

Registration Window:
...

Plan ID:
...

Plan Version:
...

Snapshot Hash:
...

Action Hash:
...

Approval Status:
...
```

---

# 31. Completion Contract

Every interaction returns the relevant subset of:

```yaml
completion:
  state:
  academic_context:
  structured_result:
  freshness:
  session:
  conflicts:
  uncertainty:
  approval:
  execution:
  verification:
  evidence:
  next_action:
```

The meaning of the fields is:

```text
academic_context
→ exact portal and academic period

structured_result
→ normalized academic data

freshness
→ whether current-state claims remain usable

session
→ whether the portal identity/session is valid

conflicts
→ detected constraint violations

uncertainty
→ unresolved conditions

approval
→ lifecycle approval state

execution
→ actual mutation state

verification
→ portal-confirmed outcome

evidence
→ provenance supporting consequential claims

next_action
→ one safe bounded continuation when applicable
```

---

# 32. Completion State Contract

Use:

```text
READ_COMPLETE
PLAN_COMPLETE
STAGE_COMPLETE
SUBMISSION_COMPLETE
CONFIRMED
PARTIAL
UNKNOWN
BLOCKED
FAILED
INVALIDATED
```

Definitions:

## READ_COMPLETE

Requested data was read successfully with sufficient context.

## PLAN_COMPLETE

A deterministic plan exists and has passed applicable analysis.

## STAGE_COMPLETE

Approved actions were staged and the staged portal state matched the plan.

## SUBMISSION_COMPLETE

The portal accepted a submission operation.

## CONFIRMED

The final portal state was independently read and matches the intended result.

## PARTIAL

Some requested work completed, but one or more expected conditions remain unresolved.

## UNKNOWN

The actual portal state cannot be reliably established.

## BLOCKED

A required safety, authorization, session, or adapter condition prevents progress.

## FAILED

The operation definitively failed and the portal state is known or safely classified.

## INVALIDATED

Previously valid planning/approval state is no longer valid because material state
changed.

---

# 33. Next Action Contract

`next_action` must be:

```yaml
next_action:
  type:
  reason:
  requires_approval:
```

Examples:

```text
REFRESH_PORTAL
REAUTHENTICATE
COMPLETE_HUMAN_VERIFICATION
REPLAN
REQUEST_APPROVAL
REVALIDATE
RECONCILE
READ_SUBMISSION_STATUS
STOP
```

Only one primary next action should be returned.

Do not return an unbounded action sequence as a "next action".

---

# 34. Read Contract Invariants

A typed reader must:

```text
1. identify portal
2. identify academic period
3. identify record type
4. verify session when protected
5. return structured values
6. preserve unknown values
7. attach provenance
8. attach freshness
9. report uncertainty
10. never mutate state
```

A reader that cannot establish record identity must return:

```text
UNKNOWN
```

rather than guessing.

---

# 35. Write Contract Invariants

A typed writer must:

```text
1. accept an explicit approved plan
2. verify plan identity
3. verify plan version
4. verify academic period
5. verify snapshot hash
6. verify action hash
7. verify current session
8. execute only approved actions
9. avoid broader mutation
10. read back the resulting state
11. return verification evidence
```

A writer must fail closed when any integrity condition fails.

---

# 36. Consequential Action Audit Requirement

The following actions require an audit record:

```text
course selection
course removal
KRS modification
KRS staging
KRS submission
```

Pure reads may be audited according to institutional logging requirements,
but they do not require an approval event.

---

# 37. Cross-Period Isolation

Academic periods are first-class keys.

Never merge:

```text
2025/2026 Ganjil
```

with:

```text
2026/2027 Ganjil
```

unless an explicit analysis operation requires cross-period comparison.

For every record:

```yaml
academic_period:
```

must remain available during normalization, planning, execution, and audit.

---

# 38. Cross-Identity Isolation

A session must be bound to the expected academic identity.

Never reuse academic state across identities.

If session identity becomes ambiguous:

```text
IDENTITY_UNCERTAIN
```

and stop protected processing.

---

# 39. Secret Redaction Policy

Before emitting or persisting logs:

```text
password
token
cookie
authorization header
OTP
CAPTCHA
MFA
CSRF
session identifier with secret material
```

must be removed or redacted.

Example:

```text
Authorization: Bearer [REDACTED]
```

not the real value.

---

# 40. Audit Integrity

Where tamper-evident audit storage is available, each event may include:

```yaml
integrity:
  event_hash:
  previous_event_hash:
```

This is for audit integrity only.

It does not establish academic truth.

Academic truth still comes from verified portal state.

---

# 41. Minimum Audit Record

At minimum, preserve:

```text
plan_id
plan_version
academic_period
action_type
approval_status
snapshot_hash
action_hash
execution_time
portal_result
verification_status
evidence_reference
```

Never omit the action binding for a consequential mutation.

---

# 42. Policy Matrix

| Operation        | Session                    | Freshness    | Approval       | Write | Verification        |
| ---------------- | -------------------------- | ------------ | -------------- | ----- | ------------------- |
| Read grades      | Required                   | Current      | No             | No    | Read evidence       |
| Read schedule    | Required                   | Current      | No             | No    | Read evidence       |
| Read offerings   | Required                   | Current      | No             | No    | Read evidence       |
| Read quota       | Required                   | Very current | No             | No    | Read evidence       |
| Read current KRS | Required                   | Current      | No             | No    | Read evidence       |
| Analyze KRS      | Required for current input | Current      | No             | No    | Analysis evidence   |
| Create KRS plan  | Required for current state | Current      | No             | No    | Plan integrity      |
| Stage KRS        | Required                   | Revalidated  | Yes            | Yes   | Required            |
| Submit KRS       | Required                   | Revalidated  | Final approval | Yes   | Required            |
| Confirm KRS      | Required                   | Current      | No             | No    | Portal confirmation |

---

# 43. Failure Policy

Convert unsafe ambiguity into an explicit state.

```text
ambiguous page
→ UNKNOWN

expired session
→ SESSION_EXPIRED

stale consequential input
→ INVALIDATED

changed approved state
→ INVALIDATED

stage mismatch
→ MISMATCH

uncertain submission
→ UNKNOWN

unsupported adapter operation
→ UNSUPPORTED

missing verification
→ UNKNOWN
```

Never convert an uncertainty into a success state.

---

# 44. Operating Rules

The system must:

```text
check session before protected actions
identify exact academic period
bind every record to source/page/context
use deterministic typed readers
use deterministic typed writers
preserve unknown values explicitly
never invent portal internals
never invent selectors
never solve or bypass CAPTCHA
never bypass OTP/MFA
keep credentials and verification tokens private
read before recommending
analyze before planning
dry-run before writing
bind approval to exact plan
bind approval to exact snapshot
bind approval to exact actions
revalidate after approval
revalidate before every write phase
separate staging from final submission
verify after every consequential action
record auditable evidence without secrets
treat timeout-after-write as UNKNOWN until verified
stop on material state drift
stop when portal state is ambiguous
```

---

# 45. Canonical Truth Rule

For current academic state:

```text
CURRENT VERIFIED PORTAL STATE
        >
historical portal state
        >
memory
        >
inference
```

Memory may help locate or plan a task.

Memory may not silently overwrite current portal truth.

---

# 46. Canonical Mutation Rule

The only valid consequential mutation sequence is:

```text
CURRENT STATE
→
PLAN
→
HASH
→
APPROVAL
→
REVALIDATION
→
STAGE
→
STAGE VERIFICATION
→
FINAL APPROVAL
→
SUBMISSION
→
PORTAL VERIFICATION
→
CONFIRMATION
→
AUDIT
```

Skipping a gate is not an optimization.

It changes the safety semantics of the system.

---

# 47. Central Safety Invariant

The system must always preserve:

```text
INTENT
≠
PLAN
≠
APPROVED PLAN
≠
EXECUTED ACTION
≠
SUBMITTED ACTION
≠
CONFIRMED PORTAL STATE
```

Therefore:

> **A proposed academic action is not an executed academic action, an executed action is not necessarily a submission, and a submission is not successful until the portal confirms the resulting state.**
