# Define Goal — Outcome Anatomy

This reference defines how to construct a concrete, measurable, bounded, and
verifiable goal.

Read it when:

```text id="c4j6q7"
designing a new goal
refining an ambiguous objective
choosing acceptance criteria
selecting validators
deciding whether a metric is meaningful
handling assumptions
controlling scope
defining evidence requirements
adapting goals to a specific domain
```

This file defines **goal semantics**.

It does not define execution planning.

---

# 1. Outcome-First Rule

A goal describes:

```text id="j0h6cw"
A DESIRED FUTURE STATE
```

not merely:

```text id="13j8y6"
AN ACTIVITY
```

Weak:

```text
Research PostgreSQL.
```

Better:

```text
Produce a comparison of PostgreSQL indexing strategies for the current query
workload and select a strategy using documented criteria and reproducible
benchmark evidence.
```

Weak:

```text
Work on the dashboard.
```

Better:

```text
Deliver the three required dashboard views with working filters and verified
data against the specified dataset.
```

Weak:

```text
Study Docker.
```

Better:

```text
Demonstrate the ability to containerize the target backend, start it from a clean
environment, explain the container configuration, and pass the required
integration tests.
```

The key test is:

> **What will be observably true when the goal is complete that is not true now?**

---

# 2. Activity-to-Outcome Conversion

Convert:

```text id="s7h8zl"
ACTIVITY
   ↓
DESIRED STATE
   ↓
EVIDENCE
   ↓
VALIDATOR
   ↓
ACCEPTANCE THRESHOLD
```

Example:

```text id="s8r3rm"
"Improve API"

        ↓

"Reduce checkout API latency"

        ↓

"Run the existing benchmark"

        ↓

"Measure p95 latency"

        ↓

"p95 < 250 ms across 3 valid runs"
```

Do not stop at the measurement.

A metric without a meaningful acceptance rule is incomplete.

---

# 3. Outcome Sentence

Prefer a goal outcome that follows:

```text
[Target] + [desired state] + [meaningful condition]
```

Examples:

```text id="e43e7x"
The authentication API accepts valid credentials and rejects invalid credentials
according to the defined contract.

The migration produces a fully reconciled dataset with zero unresolved critical
records.

The report satisfies all mandatory assignment requirements and passes final
content and visual QA.

The benchmarked endpoint maintains p95 latency below the defined threshold under
the specified workload.
```

Avoid outcome statements containing only:

```text id="9ndw8b"
work
improve
handle
do
research
study
prepare
investigate
optimize
review
```

without a resulting state.

---

# 4. Goal Anatomy

Canonical structure:

```text id="91z2w6"
GOAL
├── Identity
├── Outcome
├── Target
├── Evidence
├── Acceptance Criteria
├── Measurement
├── Scope
├── Out of Scope
├── Constraints
├── Assumptions
├── Dependencies
├── Deadline
└── Stop Conditions
```

Minimum useful form:

```text id="b0tqj1"
Outcome
+
Target
+
Evidence
+
Acceptance Criterion
+
Scope
+
Stop Condition
```

---

# 5. Target Identification

A goal needs a target that can be observed.

Possible target types:

```text id="4qg6na"
repository
service
module
API
database
dataset
model
document
artifact
environment
workflow
learning capability
research question
project milestone
decision
```

Weak:

```text
Improve the system.
```

Better:

```text
Reduce error rate for POST /checkout in the staging API.
```

When target identity matters operationally, bind:

```yaml id="46v7u8"
target:
  type:
  identifier:
  environment:
  version:
```

Do not use a vague target when a concrete target is available.

---

# 6. Evidence

Evidence answers:

```text id="txp6fz"
"What can be observed that proves the outcome exists?"
```

Useful evidence:

```text id="9yxzco"
automated test result
benchmark result
build artifact
generated file
database reconciliation report
deployment health state
evaluation result
external authoritative record
reviewed deliverable
observable runtime behavior
```

Weak evidence:

```text id="3wb6g1"
"It looks correct."
"I think it works."
"The agent completed the steps."
"It should be done."
```

Confidence is not a substitute for proof.

---

# 7. Evidence Hierarchy

Prefer:

```text id="n7px5m"
1. automated validator
2. reproducible command/result
3. observable artifact
4. independent comparison
5. structured manual review
6. self-report / confidence
```

For consequential goals, completion should normally rely on levels 1–4.

Level 6 may provide useful context but should not independently establish
completion.

---

# 8. Evidence Strength vs Confidence

Keep these separate.

```text id="9yj1pw"
EVIDENCE STRENGTH
How directly does the evidence establish the claim?

CONFIDENCE
How confident is the evaluator in the interpretation?
```

Example:

```text id="qoq9tu"
Automated integration test:
HIGH evidence strength

Agent interpretation of a complex benchmark:
MEDIUM confidence
```

High confidence does not automatically imply high evidence strength.

---

# 9. Evidence Provenance

Goal evidence should be attributable.

Recommended:

```yaml id="l0h3p8"
evidence:
  source:
  target:
  environment:
  version:
  observed_at:
  method:
  result:
  reference:
```

A benchmark without:

```text id="t2wz84"
environment
workload
version
measurement method
```

may not be reproducible.

---

# 10. Evidence Freshness

Evidence can become stale.

Examples:

```text id="vq1m9f"
test result from an older commit
deployment health from a previous release
benchmark from a changed environment
dataset validation from before migration
```

For every completion-critical evidence item, consider:

```text id="8zjy0f"
target version
environment
observed_at
freshness
```

Completion should use sufficiently current evidence.

---

# 11. Acceptance Criteria

Acceptance criteria define the exact transition:

```text id="u4ywj1"
NOT DONE
    ↓
DONE
```

Each criterion should contain:

```yaml id="gywq0k"
criterion:
  criterion_id:
  description:
  validator:
  expected_result:
  threshold:
  evidence_required:
  blocking:
```

Prefer criteria that another evaluator could independently verify.

---

# 12. Criterion Types

Useful criterion classes:

```text id="8z2ia0"
BOOLEAN
THRESHOLD
RANGE
COUNT
RATE
COMPLETENESS
CONSISTENCY
BEHAVIOR
ARTIFACT
COMPARISON
REVIEW
```

Examples:

```text
BOOLEAN:
build succeeds.

THRESHOLD:
p95 latency < 250 ms.

COUNT:
all 12 required files exist.

RATE:
>= 99% records reconcile successfully.

COMPLETENESS:
all required report sections exist.

BEHAVIOR:
invalid credentials are rejected.

ARTIFACT:
final PDF exists at the required location.
```

Use the simplest criterion type that reliably expresses success.

---

# 13. Binary Validation

When a meaningful numeric metric does not exist, prefer a binary validator.

Examples:

```text id="6u6p6c"
Build succeeds from a clean environment.

The required test suite passes.

The document contains every required section.

The prototype URL opens successfully.

The migration produces zero unresolved critical reconciliation errors.

The design satisfies all explicitly stated acceptance criteria.
```

A truthful binary validator is better than a fabricated score.

---

# 14. Quantification

Use numbers when they represent meaningful success.

Useful dimensions:

```text id="1x4jz4"
TESTING
PERFORMANCE
QUALITY
DATA / MIGRATION
RESEARCH
DELIVERABLES
OPERATIONS
LEARNING
```

Examples:

```text
Testing:
0 required test failures.

Performance:
p95 < 250 ms.

Quality:
error rate < 1%.

Migration:
100% required records reconciled.

Research:
3 candidate approaches evaluated against predefined criteria.

Deliverables:
4 required files present.

Learning:
3 independent transfer tasks solved correctly.
```

Do not use arbitrary metrics merely because numbers appear objective.

---

# 15. Metric Anti-Gaming Rule

A metric is valid only when it corresponds to the actual outcome.

Bad:

```text id="6t4qu2"
Goal:
Improve code quality.

Metric:
number of commits.
```

Bad:

```text id="c1h6ui"
Goal:
Improve documentation.

Metric:
number of words.
```

Bad:

```text id="dq5t9j"
Goal:
Improve model quality.

Metric:
training accuracy only.
```

The validator must measure the intended outcome rather than an easy-to-optimize
proxy that can be improved without achieving the goal.

---

# 16. Metric Definition

For quantitative criteria, define:

```yaml id="r8v8i4"
metric:
  name:
  direction:
  threshold:
  unit:
  measurement_method:
  workload:
  population:
  environment:
  baseline:
  valid_run_count:
```

Example:

```yaml id="b1qfza"
metric:
  name: p95_latency
  direction: "<"
  threshold: 250
  unit: ms
  measurement_method: existing_checkout_benchmark
  workload: documented_checkout_workload
  environment: staging
  valid_run_count: 3
```

---

# 17. Thresholds

Useful threshold forms:

```text id="h4ie9w"
<
<=
>
>=
=
between
zero
all
none
exactly N
at least N
at most N
```

Examples:

```text
p95 < 250 ms
coverage >= 80%
unresolved critical defects = 0
required files = 6
records reconciled = 100%
```

Avoid unjustified decimals.

---

# 18. Baselines

When measuring improvement, capture the baseline.

```text id="3r21di"
BASELINE
   ↓
TARGET
   ↓
MEASURED RESULT
```

Example:

```text id="j0w4gt"
Baseline p95:
420 ms

Target:
<250 ms

Measured:
238 ms
```

Do not claim improvement without a trustworthy baseline.

---

# 19. Consecutive-Run Requirements

For noisy measurements, require repeated valid observations.

Example:

```text id="1p0a4j"
p95 latency must remain below 250 ms
for 3 valid benchmark runs.
```

This is stronger than:

```text id="7x7hpu"
one benchmark returned 240 ms
```

The number of runs must reflect the real variability of the measurement.

Do not invent repetition requirements without reason.

---

# 20. Environment Binding

A result is meaningful only relative to its environment when environment affects
the outcome.

Examples:

```yaml id="k9f8py"
environment:
  type: staging
  runtime:
  dependency_lock:
  dataset:
  workload:
```

Do not use:

```text id="w5h0l1"
local benchmark
```

as proof of:

```text id="4t9yjj"
production performance
```

unless the environments are known to be sufficiently equivalent.

---

# 21. Reproducibility

A strong validator should ideally contain:

```text id="j48k8f"
COMMAND
+
EXPECTED RESULT
+
TARGET
+
ENVIRONMENT
```

Example:

```text id="a51c5o"
Run:
npm run test:checkout

Expected:
all checkout tests pass.
```

Performance:

```text id="x4xj8v"
Run the existing checkout benchmark three times under the documented staging
workload.

Expected:
each valid run reports p95 < 250 ms.
```

---

# 22. Scope Control

Bound goals using meaningful dimensions:

```text id="9fnv3w"
repository
service
module
files
environment
dataset
project phase
deadline
examples/cases
target platform
allowed tools
maximum blast radius
```

Example:

```text
Modify only:
authentication module and its tests.

Exclude:
shared database schema
unrelated dependency upgrades
UI redesign
```

The purpose is to prevent accidental expansion, not to produce unnecessary
administrative detail.

---

# 23. Out-of-Scope Definition

Use exclusions when they reduce likely ambiguity.

Good:

```text id="v7r6du"
In scope:
API validation
authentication middleware
affected tests

Out of scope:
UI redesign
database migration
unrelated dependencies
```

For a trivial goal, explicit exclusions may add unnecessary noise.

Use them proportionally.

---

# 24. Blast Radius

Technical goals may define:

```text id="v4j5np"
maximum files changed
maximum services affected
maximum data affected
allowed environments
allowed API surface
```

Example:

```text
Change only the checkout service and its tests.
Do not alter shared authentication or database schemas.
```

A goal does not authorize changes outside its defined scope.

---

# 25. Stop Conditions

A stop condition says when work should stop rather than continue indefinitely.

Use when:

```text id="fgu5uj"
required information is missing
acceptance criteria conflict
target environment is unclear
scope would need to expand
destructive action becomes necessary
assumptions are contradicted
evidence cannot be reproduced
required dependency is unavailable
materially different outcomes require user choice
security or authorization boundary would be crossed
```

A goal without a meaningful stop boundary can become an unbounded task.

---

# 26. Stop vs Failure

Do not confuse:

```text id="a6s5gp"
STOP CONDITION
```

with:

```text id="a0dyx9"
FAILURE
```

Example:

```text
Evidence unavailable
→ STOP / UNKNOWN

Validator fails
→ NOT COMPLETED

Security boundary would be crossed
→ BLOCKED

Scope conflict discovered
→ RECONCILE
```

Stopping protects correctness.

It does not necessarily mean the goal failed.

---

# 27. Assumption Handling

For every assumption ask:

```text id="g1k2ij"
Is it low-impact?
Is it safely inferable?
Could changing it materially change success?
```

Low-impact assumption:

```text
Use the repository's existing test runner.
```

Material assumption:

```text
Assume staging has production-equivalent database performance.
```

Material assumptions must be:

```text id="u8s7gx"
validated
explicitly accepted
or converted into uncertainty
```

Never fabricate evidence to satisfy an assumption.

---

# 28. Clarification Rule

Ask one concise clarification only when different interpretations produce
materially different goals.

Preferred areas:

```text id="e4z5bq"
validator
target
environment
scope
deadline
acceptance threshold
```

Good:

```text
Should success mean the API passes the current integration suite, or that p95
latency is also below 250 ms?
```

Bad:

```text
Can you provide more information?
```

Use existing context whenever it resolves ambiguity safely.

---

# 29. Active Goal Inspection

Before creating a goal, inspect:

```text id="3bqm4s"
NONE
ACTIVE
COMPLETED
PAUSED
BLOCKED
CONFLICTING
```

Determine:

```text id="bph25b"
NEW
REUSE
REFINE
CONFLICT
SUPERSEDE
```

Do not create duplicates simply because wording differs.

---

# 30. Goal Conflict

Compare:

```text id="c6f7ew"
outcome
target
scope
deadline
constraints
resource requirements
```

Flow:

```text id="ed7l5d"
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

# 31. Refinement

Refine when:

```text id="2j9jsn"
outcome is activity-based
validator is vague
scope is unclear
evidence is insufficient
deadline changed
target changed
constraint changed
original goal becomes technically impossible
```

Do not refine solely for stylistic reasons.

Preserve the original intent where possible.

---

# 32. Refinement vs New Goal

Use refinement when:

```text id="9h0qiy"
same underlying outcome
same logical target
```

Use a new goal when:

```text id="q5n0c7"
different outcome
different target
independent acceptance criteria
independent ownership
independent deadline
```

Material refinement should create a new goal version.

---

# 33. Goal Decomposition Boundary

A goal may contain multiple acceptance criteria.

Do not automatically decompose it into tasks.

Example:

```text id="osb4t2"
Goal:
Deliver the authentication milestone.

Acceptance:
login works
protected routes work
token validation works
required tests pass
```

This remains one outcome contract.

Execution planning decides how the result will be achieved.

---

# 34. Goal vs Plan

Goal:

```text id="u0v3yz"
Reduce API p95 latency below 250 ms and verify it across three valid benchmark
runs.
```

Plan:

```text id="7j9m0c"
Profile
→ inspect queries
→ identify bottleneck
→ optimize
→ test
→ benchmark
```

The goal should not contain implementation steps unless they are themselves part
of the acceptance contract.

---

# 35. Goal vs Task

```text id="a3l1z9"
Task:
Run benchmark.

Goal:
Reduce p95 latency below 250 ms.
```

A goal may require many tasks.

A task does not become a goal merely because it takes time.

---

# 36. Learning Goals

Learning goals describe **demonstrated capability**, not exposure.

Weak:

```text id="0c2d52"
Learn Docker.
```

Strong:

```text id="9tq0t6"
Demonstrate independent ability to containerize the target backend, explain the
Dockerfile decisions, start it from a clean environment, and pass the required
integration tests.
```

Useful evidence:

```text id="z8h5wa"
working artifact
independent solution
transfer task
assessment
oral explanation
code review
successful troubleshooting
```

Time spent studying is usually evidence of activity, not competence.

---

# 37. Learning Validator Design

A strong learning validator should test transfer.

Prefer:

```text id="x3fcj4"
new but related problem
```

over:

```text id="7eu0d9"
exact memorized example
```

Possible progression:

```text id="ps5t5j"
RECALL
→ EXPLAIN
→ IMPLEMENT
→ DEBUG
→ TRANSFER
```

A capability-oriented goal should usually reach at least implementation or transfer
when practical.

---

# 38. Software Engineering Goal Patterns

## Bug Fix

```text
Reproduce the reported failure, restore the violated behavior with the smallest
safe change, and verify the original regression test plus the affected test scope
passes.
```

Validator:

```text
original reproduction no longer fails
+
regression passes
+
targeted tests pass
```

---

## Testing

```text
Add the required test coverage for the specified behavior and verify that all
defined cases pass with no unrelated regressions.
```

Validator:

```text
test set
+
expected cases
+
pass result
```

---

## Performance

```text
Reduce [metric] below [threshold] for [workload] in [environment], validated over
[N] valid runs.
```

Validator:

```text
metric
+
threshold
+
workload
+
environment
+
valid runs
```

---

## Refactoring

```text
Replace the specified implementation without changing externally required
behavior, validated by the existing contract and regression test suite.
```

Validator:

```text
behavior preserved
+
scope respected
+
tests pass
```

---

## Deployment

```text
Deploy the specified version to the target environment and verify the documented
healthy state without violating the rollback boundary.
```

Validator:

```text
deployment version
+
health checks
+
target environment
+
rollback condition
```

---

# 39. Data / Migration Goal Patterns

Prefer:

```text
Migrate the defined dataset so that all required records are transformed and
reconciled with zero unresolved critical discrepancies.
```

Useful criteria:

```text
records processed
records successfully transformed
records reconciled
critical discrepancies
sampling/validation results
```

Do not define success solely as:

```text
"migration command completed"
```

Command completion is not data correctness.

---

# 40. Data Analytics Goal Patterns

Define:

```text id="3pqx1e"
dataset
metric
calculation definition
validation method
output artifact
```

Example:

```text
Produce the specified KPI dashboard from the defined dataset with validated
metric calculations and all required views.
```

Validator should verify both:

```text id="cv3j8x"
artifact existence
+
metric correctness
```

---

# 41. Machine Learning Goal Patterns

Define:

```text id="r1gl2a"
target metric
evaluation population
evaluation split
baseline
error threshold
reproducibility requirement
```

Example:

```text
Evaluate the model on the predefined validation split and determine whether it
meets the target F1 threshold while remaining reproducible under the documented
evaluation procedure.
```

Avoid:

```text
Train the model until accuracy is high.
```

Training duration is not an outcome.

---

# 42. ML Metric Integrity

Do not define model success using a metric that can hide the actual failure.

Consider:

```text id="i7j3l8"
class imbalance
data leakage
validation contamination
population mismatch
baseline comparison
calibration
false-positive/false-negative tradeoffs
```

When the goal depends on a metric, define:

```text
population
split
measurement procedure
```

without inventing requirements absent from the actual objective.

---

# 43. Research Goal Patterns

Research goals should produce:

```text id="j8u14c"
validated conclusion
comparison
decision
explanation
or clearly bounded uncertainty
```

Weak:

```text
Research vector databases.
```

Strong:

```text
Compare three candidate vector-storage approaches for the defined RAG workload
and evaluate them against retrieval quality, operational complexity, and measured
query latency using authoritative documentation and reproducible benchmark
evidence.
```

A research goal must permit evidence to:

```text id="26t1gj"
support
weaken
or fail to resolve
```

the investigated proposition.

Do not define research success as proving a preferred conclusion.

---

# 44. Research Evidence Standard

Specify:

```text id="fxcr0t"
question
population/scope
alternatives
source standard
method
comparison criteria
completion condition
uncertainty boundary
```

Prefer authoritative sources where the question requires authoritative claims.

Use reproducible benchmark evidence for empirical claims.

---

# 45. Academic Goal Patterns

Academic goals should map to actual course requirements.

Example:

```text id="a4w6mi"
Produce a submission-ready report that satisfies all explicit requirements in the
current assignment brief, uses the required structure and formatting, contains
evidence-backed analysis and references, and passes final content and visual QA.
```

Validator sources:

```text id="5f5bju"
assignment brief
rubric
course instructions
required template
final artifact
visual QA
submission requirements
```

Never invent grading requirements not present in the authoritative course
materials.

---

# 46. Project Goal Patterns

Define a milestone outcome rather than project activity.

Strong:

```text id="4j6w1h"
Deliver the authentication milestone with login, token validation, protected
routes, and automated tests covering the required success and failure cases.
```

Weak:

```text
Work on authentication.
```

A project goal should be stable enough to remain meaningful while implementation
details evolve.

---

# 47. Operations Goal Patterns

Define:

```text id="7w5qgr"
healthy state
metric
threshold
observation window
environment
stop/rollback condition
```

Example:

```text
Maintain the service within the defined error-rate threshold for the observation
window and verify the required health checks.
```

Avoid goals that equate:

```text
monitoring
```

with:

```text
service health
```

Monitoring provides evidence; it is not itself the outcome.

---

# 48. Deliverable Goals

For artifacts, specify:

```text id="9f0rxp"
exact artifact
format
location
required sections
validation
links/references
```

Example:

```text
Produce the required PDF report containing all mandated sections, references,
figures, and formatting requirements, with successful final visual QA.
```

Validator:

```text
artifact exists
+
structure complete
+
content validated
+
visual validation passes
```

---

# 49. Deadline-Aware Goals

Deadline defines:

```text id="hj3u8x"
WHEN
```

Success criterion defines:

```text id="7x9fza"
WHAT
```

Example:

```text
Complete the required report by August 28, 2026, with every mandated section,
reference, and final PDF validation completed before submission.
```

Do not treat:

```text
finished by Friday
```

as sufficient acceptance criteria.

---

# 50. Deadline Semantics

Represent:

```yaml id="h8a3qr"
deadline:
  due_at:
  timezone:
  hard:
```

A missed deadline does not prove the outcome failed.

Similarly, completing early does not prove the outcome succeeded.

The two dimensions must remain separate.

---

# 51. Constraint Semantics

Separate:

```text id="w4b5z1"
HARD CONSTRAINT
```

from:

```text id="d0h8jc"
SOFT PREFERENCE
```

Example:

```yaml
constraints:
  hard:
    - "must remain API-compatible"
  soft:
    - "prefer existing library"
```

A hard constraint violation may block acceptance even when other criteria pass.

---

# 52. Dependency Semantics

Dependencies are external conditions required for success.

Example:

```yaml id="m5i9h7"
dependency:
  description: "staging database available"
  status: PENDING
  blocking: true
```

Do not hide dependency failure inside the goal itself.

The goal can remain valid while its execution is:

```text
BLOCKED
```

---

# 53. Impossible Goals

A technically impossible goal should not be silently converted into an achievable
but different objective.

Examples:

```text id="z8u1bv"
required API does not exist
required dataset is unavailable
deadline is incompatible with explicit constraints
validator cannot measure the desired outcome
target no longer exists
```

Possible action:

```text id="elq31x"
REFINE
RECONCILE
BLOCK
SUPERSEDE
```

Preserve the original intent where possible.

---

# 54. Goal Integrity

A goal should be considered internally inconsistent when:

```text id="z4ilwj"
success criterion contradicts outcome
scope excludes required target
deadline contradicts dependency availability
validator measures a different result
hard constraints make success impossible
two mandatory criteria cannot both pass
```

Example:

```text
Outcome:
change database schema.

Constraint:
database schema must not change.
```

This requires reconciliation, not silent interpretation.

---

# 55. Validation Order

Recommended goal-quality validation:

```text id="z1n2lc"
OUTCOME
 ↓
TARGET
 ↓
EVIDENCE
 ↓
CRITERIA
 ↓
SCOPE
 ↓
CONSTRAINTS
 ↓
ASSUMPTIONS
 ↓
DEPENDENCIES
 ↓
DEADLINE
 ↓
STOP CONDITIONS
 ↓
CONFLICTS
```

A later validation step must not silently invalidate an earlier one.

---

# 56. Validator Independence

Where practical, validators should not depend on the exact mechanism used to achieve
the goal.

Example:

Bad:

```text
"Function X was called."
```

when the goal is:

```text
"User receives a valid session."
```

Better:

```text
"User receives a valid session under the required login scenario."
```

This prevents implementation-specific checks from masquerading as outcome
verification.

---

# 57. Validator Robustness

A validator should detect meaningful failure modes, not merely happy-path success.

For software:

```text id="1d1z0b"
success cases
failure cases
boundary cases
regression cases
```

For documents:

```text id="3i8yrt"
required sections
content correctness
format correctness
rendered output
```

For data:

```text id="s9x7fw"
completeness
correctness
consistency
reconciliation
```

For learning:

```text id="4o8w9r"
independent execution
explanation
transfer
```

---

# 58. Completion Integrity

Never mark a goal complete because:

```text id="g8h1m2"
the work looks done
the agent feels confident
a partial artifact exists
a command was issued
a browser action occurred
a deployment was attempted
a report was generated
the user requested completion
```

Completion requires the defined evidence.

Correct outcomes:

```text id="u2x7md"
COMPLETED
PARTIAL
UNKNOWN
BLOCKED
FAILED
```

Choose based on evidence.

---

# 59. Completion Contract

A goal is complete when:

```text id="n6h2rt"
all blocking criteria pass
+
required evidence exists
+
evidence matches the target
+
evidence is sufficiently fresh
+
scope remained within bounds
+
no material contradiction remains
```

Formally:

```text id="m0h7b4"
COMPLETED
=
CRITERIA_PASS
∧
EVIDENCE_SUFFICIENT
∧
TARGET_MATCH
∧
SCOPE_VALID
∧
NO_MATERIAL_CONFLICT
```

---

# 60. Partial Completion

Use:

```text id="p5xv7k"
PARTIAL
```

when some criteria pass but one or more blocking criteria remain unresolved.

Example:

```text
Artifact generated:
PASS

Content QA:
PASS

Visual QA:
UNKNOWN
```

This is not complete.

---

# 61. Unknown Completion

Use:

```text id="w6q6k9"
UNKNOWN
```

when the intended outcome may have occurred but the evidence cannot establish it.

Example:

```text
Deployment request was accepted,
but the health-check endpoint became unavailable before confirmation.
```

Do not convert:

```text
UNKNOWN
```

into:

```text
COMPLETED
```

because the intended action was performed.

---

# 62. Goal Drift

A goal drifts when execution changes:

```text id="5otb7m"
outcome
target
scope
validator
deadline
```

without explicit revision.

Compare:

```text id="n3r8fe"
GOAL VERSION
vs
CURRENT PLAN
vs
CURRENT EXECUTION
```

Material divergence requires:

```text id="h0z3t0"
REFINE
or
NEW VERSION
```

Never silently expand the goal.

---

# 63. Scope Expansion

When execution requires work outside scope:

```text id="6x6km3"
STOP
→
REPORT SCOPE DELTA
→
RECONCILE GOAL
```

Do not silently treat additional work as part of the original goal.

---

# 64. Goal Success vs Effort

High effort does not imply success.

```text id="m4q3i8"
10 hours of debugging
≠
bug fixed

50 sources read
≠
research conclusion established

20 pages written
≠
assignment requirements satisfied

100 commits
≠
milestone completed
```

The acceptance contract determines success.

---

# 65. Goal Success vs Activity Count

Activity counts may be useful for monitoring but are not automatically outcome
metrics.

Bad:

```text
Read 20 papers.
```

Better:

```text
Evaluate the defined research question using at least the required authoritative
sources and produce a supported conclusion with an explicit uncertainty boundary.
```

If source count matters, include it as one criterion, not the entire goal.

---

# 66. Goal Quality Anti-Patterns

Avoid:

```text id="q8c5zj"
activity-only outcome
metric-only goal
arbitrary precision
proxy metric detached from outcome
hidden target
hidden environment
unstated assumption
unbounded scope
missing validator
missing stop condition
deadline treated as success
implementation detail masquerading as outcome
historical evidence treated as current evidence
confidence treated as proof
execution permission implied by goal definition
```

---

# 67. Domain Quantification Matrix

| Domain               | Useful Measures                                                     | Typical Evidence                             |
| -------------------- | ------------------------------------------------------------------- | -------------------------------------------- |
| Software Engineering | tests, build status, latency, defects, coverage, API behavior       | automated tests, benchmark, diff             |
| Data Analytics       | completeness, KPI correctness, validation errors                    | validation report, dataset checks            |
| Machine Learning     | target metric, baseline delta, error rate, reproducibility          | evaluation run, benchmark                    |
| Infrastructure       | health, uptime, resource limits, deployment state                   | health checks, metrics, deployment state     |
| Learning             | independent performance, transfer, explanation                      | artifact, assessment, transfer task          |
| Academic Work        | rubric criteria, required sections, references, artifact validation | brief/rubric, final artifact, QA             |
| Research             | evidence quality, alternatives evaluated, benchmark results         | authoritative sources, reproducible analysis |
| Deliverables         | file count, structure, format, links, QA                            | artifact inspection                          |

The matrix provides patterns, not mandatory metrics.

---

# 68. Goal Pattern — Simple

```text id="fbhz8s"
Outcome:
[desired future state]

Target:
[object]

Evidence:
[observable proof]

Success:
[validator / threshold]

Scope:
[boundary]

Stop:
[blocking ambiguity or unsafe expansion]
```

---

# 69. Goal Pattern — Quantitative

```text id="9q9e4v"
Outcome:
[desired improvement]

Target:
[target]

Metric:
[metric]

Baseline:
[current measurement]

Threshold:
[target]

Method:
[how measured]

Environment:
[where measured]

Valid Runs:
[N]

Evidence:
[measurement output]
```

---

# 70. Goal Pattern — Deliverable

```text id="zq1h0g"
Outcome:
[deliverable is submission-ready]

Target:
[file / artifact]

Required Content:
[mandatory sections]

Format:
[required format]

Evidence:
[artifact inspection + QA]

Acceptance:
[all mandatory requirements pass]
```

---

# 71. Goal Pattern — Research

```text id="h2m5qn"
Question:
[research question]

Scope:
[population / alternatives / timeframe]

Evidence Standard:
[source and methodological requirements]

Evaluation Criteria:
[comparison dimensions]

Method:
[measurement / analysis method]

Completion:
[decision / conclusion / uncertainty statement]
```

---

# 72. Goal Pattern — Learning

```text id="r8g4cc"
Capability:
[what the learner can independently do]

Target:
[skill/domain]

Evidence:
[artifact / test / transfer task]

Acceptance:
[observable competence threshold]

Environment:
[where demonstrated]
```

---

# 73. Goal Pattern — Technical Change

```text id="1w0fjd"
Outcome:
[target behavior is correct]

Target:
[repository / service / module]

Scope:
[affected boundary]

Acceptance:
[behavioral validator]

Regression:
[previous failure / invariant protected]

Blast Radius:
[maximum acceptable impact]

Stop:
[unsafe scope or missing evidence]
```

---

# 74. Final Anatomy Checklist

Before accepting a goal:

```text id="h6q2f7"
[✓] describes a future state
[✓] identifies the target
[✓] defines observable evidence
[✓] has meaningful acceptance criteria
[✓] uses a real metric when quantification helps
[✓] avoids metric gaming
[✓] defines measurement method
[✓] binds important evidence to environment/version
[✓] bounds scope
[✓] defines exclusions when necessary
[✓] exposes consequential assumptions
[✓] identifies blocking dependencies
[✓] defines stop conditions
[✓] distinguishes goal from plan
[✓] distinguishes goal from task
[✓] distinguishes competence from learning exposure
[✓] permits independent completion verification
```

If a critical item fails:

```text
REFINE
```

rather than silently accepting an underspecified goal.

---

# 75. Central Principle

> **A well-defined goal does not merely say what work should happen. It defines the observable future state, the target it applies to, the evidence that proves it, the threshold that makes it successful, and the boundary beyond which the system must stop instead of guessing.**
