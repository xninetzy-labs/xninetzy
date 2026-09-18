# Define Goal — Lifecycle, Conflict, and Completion

This reference defines the lifecycle, reconciliation rules, refinement semantics,
quality gates, tool boundary, and completion contract for goal definition.

Read it when:

```text id="g4t7q1"
creating a goal
refining an existing goal
inspecting active goals
detecting duplicate goals
handling goal conflicts
detecting goal drift
auditing goal quality
deciding whether a goal is valid
determining goal completion
```

This file governs the **goal-definition lifecycle**.

It does not govern long-running execution, task management, progress tracking, or
project orchestration.

---

# 1. Canonical Lifecycle

Goal definition follows:

```text id="a7h6m3"
DETECT
   ↓
INSPECT
   ↓
FORMULATE
   ↓
QUANTIFY
   ↓
BOUND
   ↓
VALIDATE
   ↓
RECONCILE
   ↓
VERSION
   ↓
CREATE / REFINE
```

After creation:

```text id="4jz8s2"
GOAL
   ↓
DOWNSTREAM EXECUTION SYSTEM
```

The execution system owns planning and progress.

---

# 2. Goal State Model

Canonical lifecycle:

```text id="e4u6k9"
DRAFT
  ↓
VALIDATED
  ↓
ACTIVE
  ↓
COMPLETED
```

Alternative states:

```text id="w2m3c7"
PAUSED
BLOCKED
CANCELLED
SUPERSEDED
CONFLICTING
```

Additional terminal diagnostic state:

```text id="p8f1s4"
INVALIDATED
```

when the goal can no longer be pursued under its current contract because a
material assumption, target, constraint, or external condition changed.

---

# 3. State Semantics

## DRAFT

Goal contract exists but has not passed the required quality gate.

## VALIDATED

Goal contract is sufficiently precise and internally coherent.

## ACTIVE

Goal is accepted as the current objective for downstream execution.

## COMPLETED

All blocking success criteria have been verified with sufficient evidence.

## PAUSED

Goal remains valid but execution is intentionally suspended.

## BLOCKED

Goal remains valid but a required dependency, authority, resource, or condition
prevents execution.

## CONFLICTING

Goal materially conflicts with another active objective or hard constraint.

## CANCELLED

Goal was intentionally terminated without requiring successful completion.

## SUPERSEDED

A newer goal version or objective replaced the current one.

## INVALIDATED

The original goal can no longer be safely treated as valid because material
conditions changed.

---

# 4. State Transition Rules

Allowed transitions:

```text id="n7c2w4"
DRAFT
  → VALIDATED
  → CANCELLED

VALIDATED
  → ACTIVE
  → BLOCKED
  → CONFLICTING
  → SUPERSEDED
  → CANCELLED

ACTIVE
  → COMPLETED
  → PAUSED
  → BLOCKED
  → CONFLICTING
  → INVALIDATED
  → SUPERSEDED
  → CANCELLED

PAUSED
  → ACTIVE
  → CANCELLED
  → SUPERSEDED
  → INVALIDATED

BLOCKED
  → ACTIVE
  → CANCELLED
  → SUPERSEDED
  → INVALIDATED

CONFLICTING
  → ACTIVE
  → SUPERSEDED
  → CANCELLED

INVALIDATED
  → REFINE
  → SUPERSEDED
  → CANCELLED
```

Do not create arbitrary transitions that bypass validation.

---

# 5. Completion State

A goal may transition to:

```text id="r8q2m0"
COMPLETED
```

only when:

```text id="f3c8a1"
all blocking success criteria pass
+
required evidence exists
+
evidence matches the intended target
+
evidence is sufficiently fresh
+
scope remained within bounds
+
no material unresolved contradiction remains
```

The fact that work was performed is not sufficient.

---

# 6. Goal Creation Rules

Before `goal_create`:

```text id="2f7k5w"
1. determine whether a persistent goal is actually needed
2. inspect active goal state
3. formulate the desired outcome
4. identify the target
5. define evidence
6. define success criteria
7. quantify when meaningful
8. bound scope
9. expose material assumptions
10. define stop conditions
11. reconcile conflicts
12. validate the goal
13. assign goal identity/version
```

Create only after the contract passes the quality gate.

---

# 7. One Goal, One Objective Contract

A persistent goal should represent one coherent outcome.

Avoid embedding:

```text id="0x5q8n"
full roadmap
task checklist
decision log
progress history
execution snapshot
tool trace
browser state
```

inside the goal.

Prefer:

```text id="p7m2h1"
one outcome
+
one target
+
one acceptance contract
```

A goal may contain multiple criteria, but those criteria should jointly define the
same outcome.

---

# 8. Concise Goal Representation

Preferred creation form:

```text id="r4k6p8"
[Outcome] for [target] by [deadline/constraint], verified by [evidence/validator],
bounded to [scope], stopping if [material ambiguity/blocker].
```

Example:

```text id="q8c3w1"
Reduce checkout API p95 latency below 250 ms for the documented slow path,
verified by the existing checkout test suite and benchmark across three valid
runs, limited to the checkout service and its tests, and stop if the target
requires changing shared infrastructure.
```

The stored objective should remain concise even when the internal contract is
structured.

---

# 9. Tool Boundary

This skill is responsible for:

```text id="j9s1d4"
goal definition
goal refinement
goal validation
goal reconciliation
goal deduplication
goal conflict detection
goal state interpretation
goal creation/update
```

This skill is not responsible for:

```text id="z5h8k2"
long-running execution
task ledgers
project management
progress snapshots
execution checkpoints
detailed implementation plans
deployment orchestration
resume artifacts
decision logs
```

Those belong to specialized downstream systems.

---

# 10. Tool Capability Rule

Only persist fields supported by the available goal system.

Do not fabricate:

```text id="q5x7s9"
database columns
goal IDs
status fields
deadline fields
validator fields
history fields
```

that the actual tool does not support.

When richer internal metadata is needed, keep it in the appropriate companion
system rather than pretending it belongs to the goal tool.

---

# 11. Standard Goal Object

Conceptual representation:

```yaml id="s3m8v2"
goal:
  objective:
  target:
  outcome:
  evidence:
  success_criteria:
  scope:
  out_of_scope:
  constraints:
  deadline:
  stop_condition:
  status:
```

Optional fields may include:

```yaml id="k7q1p6"
  assumptions:
  dependencies:
  version:
  provenance:
```

Only persist what the underlying system supports.

---

# 12. Phase 01 — DETECT

Classify the incoming request:

```text id="x8m5r4"
GOAL
TASK
PLAN
QUESTION
CAPTURE
DECISION
LEARNING_OBJECTIVE
```

Examples:

```text id="h2n6q9"
"Fix login"
→ potentially goal or task

"How should we fix login?"
→ planning / diagnosis

"Make login reliable for valid and invalid credentials."
→ goal

"Run the login integration tests."
→ task
```

Do not create a goal when the user simply requests execution of a clearly defined
task.

---

# 13. Phase 02 — INSPECT

Inspect current goal state before creation.

Determine:

```text id="v7f3s5"
NO_MATCH
EXACT_MATCH
POSSIBLE_DUPLICATE
REFINEMENT_CANDIDATE
MATERIAL_CONFLICT
SUPERSEDABLE
```

Relevant states:

```text id="m1q9x8"
ACTIVE
PAUSED
BLOCKED
CONFLICTING
COMPLETED
```

Historical completed goals may help continuity but do not become active again
automatically.

---

# 14. Exact Match

An existing goal is an exact match when:

```text id="c5w8k2"
same logical outcome
same target
same acceptance contract
same meaningful scope
```

Action:

```text id="z4n6p1"
REUSE
```

Do not create a duplicate.

---

# 15. Possible Duplicate

When goals appear semantically similar but evidence is insufficient to establish
equivalence:

```text id="b7s2m5"
POSSIBLE_DUPLICATE
```

Compare:

```text id="y6d9f3"
outcome
target
validator
scope
deadline
constraints
```

Do not merge merely because titles are similar.

---

# 16. Refinement Candidate

An existing goal is a refinement candidate when the underlying objective remains
the same but the contract needs improvement.

Examples:

```text id="n8m4c7"
activity-based wording
vague validator
missing scope
missing target
new evidence standard
deadline clarification
materially improved acceptance criteria
```

Action:

```text id="p1q6v8"
REFINE
```

---

# 17. Goal Conflict

Compare:

```text id="c4z7m1"
outcome
target
scope
deadline
hard constraints
resource requirements
dependencies
authority
```

Compatibility flow:

```text id="d8n2q5"
ACTIVE GOAL
     ↓
COMPARE
     ↓
COMPATIBLE?
  ┌────┴────┐
 YES        NO
  ↓          ↓
REUSE       SURFACE CONFLICT
             ↓
      resolve / separate / supersede
```

Never silently replace an active goal.

---

# 18. Material Conflict

A conflict is material when both objectives cannot reasonably remain true within
the same constraints.

Examples:

```text id="r5v8k2"
Goal A:
change the database schema.

Goal B:
do not change the database schema.
```

Or:

```text id="p9x3c6"
Goal A:
ship by Friday.

Goal B:
require a validation phase that necessarily extends beyond Friday.
```

The system should surface the conflict rather than choose silently.

---

# 19. Conflict Record

When supported:

```yaml id="q2w6n8"
conflict:
  conflict_id:
  goal_id:
  conflicting_goal_id:
  type:
  description:
  affected_constraints:
  materiality:
  status:
```

Possible status:

```text id="t5h1p4"
UNRESOLVED
RESOLVED
SEPARATED
SUPERSEDED
BLOCKED
```

Do not silently overwrite the conflicting objective.

---

# 20. Conflict Resolution Boundary

When conflict involves consequential priority:

```text id="a7m4c9"
technical evidence
≠
authority to choose priority
```

The system may explain:

```text id="q8v5s2"
which constraints conflict
what each goal requires
what trade-off exists
```

but should not silently assume authority to select the winner when that authority
has not been established.

---

# 21. Phase 03 — FORMULATE

Construct:

```text id="y5k7m3"
Outcome
Target
Evidence
Success Criteria
Scope
Out of Scope
Constraints
Assumptions
Dependencies
Deadline
Stop Conditions
```

The contract should be sufficient for another system to plan against.

---

# 22. Phase 04 — QUANTIFY

Ask:

```text id="j1q6v9"
Is there a meaningful measurement?
```

If yes:

```text id="f3r8w2"
metric
+
threshold
+
measurement method
```

If no:

```text id="x9m2k5"
use binary or artifact-based validation
```

Do not manufacture precision.

---

# 23. Quantification Quality

A metric should:

```text id="n4c7p2"
measure the intended outcome
be reproducible
have a meaningful threshold
identify the measurement context
avoid easy gaming
```

Reject metrics that merely correlate superficially with the desired result.

---

# 24. Phase 05 — BOUND

Define relevant limits:

```text id="s8d1q7"
target
repository
environment
files
module
dataset
platform
time
tools
blast radius
```

Use only boundaries that matter.

The purpose is:

```text id="w3p9m6"
prevent silent scope expansion
```

not to add unnecessary bureaucracy.

---

# 25. Stop Condition Contract

A valid stop condition should tell the execution system when continuation requires
reassessment.

Examples:

```text id="e2k6r5"
target environment unclear
required evidence unavailable
material scope expansion required
hard constraint conflict discovered
destructive action becomes necessary
assumption is contradicted
validator cannot be reproduced
materially different outcomes require user choice
authorization boundary would be crossed
```

---

# 26. Phase 06 — VALIDATE

Run the complete quality gate:

```text id="m7v5c1"
CONCRETE_OUTCOME
EVIDENCE
THRESHOLD
SCOPE
REPRODUCIBILITY
STOP
CONSISTENCY
CONFLICT
```

A critical failure returns:

```text id="h4q8n2"
REFINE
```

or:

```text id="x5r3m7"
BLOCKED
```

rather than creating an invalid goal.

---

# 27. Concrete Outcome Test

Ask:

```text id="y7p2c8"
Can someone state what will be true afterward?
```

Pass:

```text id="t1m9q5"
"POST /checkout responds according to the required contract."
```

Fail:

```text id="d6s8v3"
"Improve checkout."
```

---

# 28. Evidence Test

Ask:

```text id="q3w7k1"
What observation proves the outcome?
```

Pass:

```text id="e8p4m6"
integration test result
```

Fail:

```text id="s2n9r5"
agent confidence
```

---

# 29. Threshold Test

Ask:

```text id="c6y1v8"
Is the success boundary objectively recognizable?
```

Valid:

```text id="k4f7q2"
all required tests pass
```

Valid:

```text id="z8m3p6"
p95 < 250 ms
```

Invalid:

```text id="r5d9n1"
performance is good
```

---

# 30. Scope Test

Ask:

```text id="w2x6s8"
Can the target and boundary be identified without guessing?
```

If not:

```text id="b7q4m9"
REFINE
```

---

# 31. Reproducibility Test

Ask:

```text id="n1k5c7"
Can the validator be executed or independently inspected again?
```

Prefer:

```text id="m8v2q6"
command
+
expected result
+
environment
```

when practical.

---

# 32. Stop Test

Ask:

```text id="r9s3d5"
Does the system know when to stop rather than continue under changed conditions?
```

If no:

```text id="h6p1x4"
add stop condition
```

---

# 33. Consistency Test

Check:

```text id="v3k8m2"
outcome vs criterion
target vs scope
constraint vs required change
deadline vs dependency
validator vs evidence
```

A logically inconsistent goal cannot pass validation simply because each field
looks individually reasonable.

---

# 34. Phase 07 — RECONCILE

Reconcile the new goal against:

```text id="j6q2w9"
active goals
project state
hard constraints
dependencies
existing commitments
recently completed goals
```

Possible results:

```text id="p4m8c1"
REUSE
REFINE
CREATE
CONFLICT
SUPERSEDE
BLOCK
```

---

# 35. Phase 08 — VERSION

Goal identity should separate:

```text id="c7n3m5"
logical objective
```

from:

```text id="w8q1x6"
contract version
```

Example:

```yaml id="a2f9r4"
goal_id: checkout_latency
version: 3
```

Material changes create a new version.

---

# 36. Material Version Changes

New version required for changes to:

```text id="s5k8v2"
outcome
target
acceptance threshold
validator
scope
deadline
hard constraint
```

Do not silently rewrite the meaning of an existing goal.

---

# 37. Non-Material Changes

A version change is not necessarily required for:

```text id="m3q7p1"
stylistic wording cleanup
formatting
ordering of equivalent fields
minor clarification that does not change semantic meaning
```

Do not create needless versions merely to alter presentation.

---

# 38. Refine Semantics

Refinement should preserve the logical intent whenever possible.

Example:

```text id="q1d8m4"
Before:
Improve API performance.

After:
Reduce checkout API p95 latency below 250 ms under the defined benchmark workload.
```

The underlying objective may remain the same while the contract becomes verifiable.

---

# 39. Refinement Failure

Do not force refinement when the new objective is materially different.

Example:

```text id="v7c2k5"
Existing:
Reduce checkout latency.

Requested:
Migrate checkout to another database.
```

This may be a task or a separate engineering goal rather than a refinement.

Determine the actual outcome before changing the goal.

---

# 40. Goal Drift

Goal drift occurs when downstream work changes:

```text id="h9m4q3"
outcome
target
scope
validator
deadline
```

without corresponding goal revision.

Detection:

```text id="k2w8s6"
GOAL CONTRACT
      ↓
compare
      ↓
CURRENT PLAN / WORK
      ↓
material difference?
```

If yes:

```text id="f6p3n8"
GOAL_DRIFT
```

and return for reconciliation.

---

# 41. Scope Expansion

When the work requires out-of-scope changes:

```text id="x4v7m1"
STOP
 ↓
describe scope delta
 ↓
reconcile goal
 ↓
new version or new goal
```

Do not silently include the additional work.

---

# 42. Goal Invalidation

Invalidate the current goal when material conditions make the existing contract
unsafe or meaningless.

Examples:

```text id="d8q2n5"
target removed
required API deprecated
dataset unavailable
deadline fundamentally changed
constraint changed
validator no longer measures the intended outcome
assumption proven false
```

The goal becomes:

```text id="p7r1c4"
INVALIDATED
```

and must be refined, superseded, or cancelled.

---

# 43. Goal vs Current Reality

The goal describes desired future state.

Current reality must remain external evidence.

Do not rewrite the goal merely because:

```text id="w6m3q9"
implementation accidentally achieved it
```

Instead verify:

```text id="j8k4p2"
current state
vs
goal criteria
```

and then mark completion when evidence is sufficient.

---

# 44. Completion Audit

Before setting:

```text id="t5c8n1"
COMPLETED
```

verify:

```text id="q7m2v4"
goal version matches the evaluated work
target matches the evidence
all blocking criteria pass
evidence is sufficient
evidence is fresh enough
scope remained valid
no material conflict remains
```

---

# 45. Completion Contract

When goal definition is complete, return:

```text id="s6p9k3"
GOAL
        final objective

TARGET / SCOPE
        affected target and boundary

EVIDENCE
        verification method

SUCCESS CRITERION
        exact threshold or binary condition

GOAL STATE
        created / reused / refined / blocked / not_created

NEXT ACTION
        one safe bounded continuation
```

The goal-definition operation itself does not imply that the goal has been
completed.

---

# 46. Requires Clarification

When the contract cannot yet be validated:

```text id="f2v8m5"
Goal status: REQUIRES_CLARIFICATION
```

Use this when ambiguity materially affects:

```text id="c9q1w7"
target
outcome
validator
environment
scope
deadline
acceptance threshold
```

Do not manufacture a measurable goal from insufficient information.

---

# 47. No-Goal Result

Do not create a goal when:

```text id="m8k2r6"
the request is a simple task
the user is asking for ordinary execution
the objective is not persistent
no useful success contract exists
the action belongs to another lifecycle
```

Return:

```text id="y4p7s1"
GOAL_NOT_REQUIRED
```

when supported by the goal system.

---

# 48. Goal State vs Execution State

Never confuse:

```text id="h5q8n2"
ACTIVE GOAL
```

with:

```text id="d7m3c9"
WORK IN PROGRESS
```

A goal can be active while no execution has started.

Likewise:

```text id="v6x1p4"
COMPLETED GOAL
```

means the acceptance contract passed.

It does not necessarily describe the detailed execution history.

---

# 49. Goal Tool Minimalism

The goal tool should store the smallest representation necessary to preserve:

```text id="n2k7w5"
objective
target
acceptance
scope
status
```

Do not convert the goal database into:

```text id="c4p8m1"
project management database
execution ledger
observability store
decision system
memory archive
```

Specialized systems should remain specialized.

---

# 50. Evidence Boundary

The goal defines required evidence.

The execution/validation system produces the evidence.

Therefore:

```text id="s7m3q9"
GOAL
→ defines what must be proven

VALIDATOR
→ performs the proof

EVIDENCE
→ records the observation

COMPLETION
→ evaluates whether proof is sufficient
```

Do not make the goal itself claim success.

---

# 51. Next Action Boundary

`next_action` must contain at most one primary bounded continuation.

Examples:

```text id="p6r2v8"
REQUEST_CLARIFICATION
REFINE_GOAL
REQUEST_APPROVAL
START_PLANNING
RUN_VALIDATOR
RECONCILE_CONFLICT
STOP
```

The goal skill should not return a long sequence of implementation tasks.

---

# 52. Completion State Examples

## Successful definition

```text id="a8q4m2"
Goal State:
ACTIVE

Success:
all required integration tests pass.

Evidence:
repository test output.

Next Action:
start execution planning.
```

## Ambiguous definition

```text id="n5w7c1"
Goal State:
REQUIRES_CLARIFICATION

Reason:
"Improve performance" does not identify the metric or target endpoint.

Next Action:
define the target metric.
```

## Conflict

```text id="v2k9p6"
Goal State:
CONFLICTING

Reason:
new objective requires a schema change while an active constraint prohibits
schema changes.

Next Action:
resolve the conflicting constraint.
```

## Blocked

```text id="q7m3x8"
Goal State:
BLOCKED

Reason:
required validation environment is unavailable.

Next Action:
restore or identify an approved validation environment.
```

---

# 53. Audit Fields

Where supported, retain:

```yaml id="c8p2m7"
goal_audit:
  goal_id:
  version:
  operation:
  previous_state:
  new_state:
  changed_fields:
  reason:
  timestamp:
```

This audit records goal-definition changes.

It should not become an execution log.

---

# 54. History Integrity

Do not rewrite a historical goal to make it appear that:

```text id="k5r1w9"
the original goal was more precise
the original scope was different
the original validator existed
the original deadline was different
```

Historical versions should remain distinguishable.

---

# 55. Goal Quality Gate

A goal passes only when:

```text id="z7m4c2"
[✓] outcome is concrete
[✓] target is identifiable
[✓] evidence is defined
[✓] success criterion is evaluable
[✓] metric is meaningful when used
[✓] scope is bounded
[✓] material exclusions are clear
[✓] hard constraints are coherent
[✓] material assumptions are explicit
[✓] dependencies are understood
[✓] stop condition exists
[✓] validator is reproducible or inspectable
[✓] no unresolved material conflict remains
[✓] completion can be independently recognized
```

Critical failure means:

```text id="h9q3w6"
REFINE
BLOCK
or
REQUIRES_CLARIFICATION
```

not successful creation.

---

# 56. Canonical Goal Creation Workflow

```text id="u4m8q1"
USER INTENTION
      ↓
DETECT
      ↓
INSPECT EXISTING GOALS
      ↓
FORMULATE OUTCOME
      ↓
IDENTIFY TARGET
      ↓
DEFINE EVIDENCE
      ↓
DEFINE SUCCESS
      ↓
QUANTIFY WHEN MEANINGFUL
      ↓
BOUND SCOPE
      ↓
DEFINE STOP CONDITION
      ↓
VALIDATE
      ↓
RECONCILE
      ↓
VERSION
      ↓
CREATE / REFINE
```

---

# 57. Canonical Goal Completion Workflow

```text id="p8c3v7"
ACTIVE GOAL
      ↓
VALIDATION EVIDENCE
      ↓
TARGET MATCH
      ↓
CRITERIA CHECK
      ↓
FRESHNESS CHECK
      ↓
SCOPE CHECK
      ↓
CONFLICT CHECK
      ↓
COMPLETED
```

Failure branches:

```text id="r6m2w4"
evidence missing
→ UNKNOWN

criterion fails
→ INCOMPLETE

scope changed
→ DRIFT / REFINE

dependency blocked
→ BLOCKED

goal obsolete
→ INVALIDATED / SUPERSEDED
```

---

# 58. Operating Rules

The system must:

```text id="m3q8v1"
define outcomes rather than activities
create only when a persistent goal is needed
inspect active goals before creation
reuse exact matches
detect probable duplicates
surface material conflicts
never silently replace an active goal
formulate target and outcome separately
define observable evidence
prefer meaningful quantitative validation
use binary validation when metrics are inappropriate
avoid artificial precision
define measurement context
bound scope
define meaningful exclusions when necessary
make consequential assumptions explicit
identify blocking dependencies
define stop conditions
validate before creation
version material contract changes
preserve historical goal meaning
detect goal drift
invalidate obsolete goals
separate goal state from execution state
separate goal definition from planning
never infer execution authority from a goal
never claim completion without evidence
never convert UNKNOWN into success
keep downstream execution responsibilities outside this skill
```

---

# 59. Central Lifecycle Principle

> **A goal is a validated contract for a desired future state. It should be created only when the outcome, target, evidence, acceptance boundary, scope, and stopping conditions are precise enough for another system to act without guessing — and it should be marked complete only when the defined evidence proves that contract has been satisfied.**
