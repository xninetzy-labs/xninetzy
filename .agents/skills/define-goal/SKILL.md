

name: "define-goal"

description: "Goal-definition control plane for converting intentions, requests, projects, learning objectives, research questions, and operational needs into concrete, bounded, measurable, evidence-verifiable outcomes. Use before significant work when success, acceptance, scope, or stopping conditions are unclear."

metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "3.0.0"
  priority: "P1"

lifecycle: "detect -> inspect -> formulate -> measure -> bound -> validate -> reconcile -> version -> create/refine"

required_tools:
- goal_inspect
- goal_create
- goa---
_update

optional_tools:
- repo_search
- repo_symbol
- repo_diff
- memory_search
- memory_goal_store
- context_retrieve
- observability_query
- hitl_request_approval
- lightning_record_action

trigger_conditions:
- user explicitly asks to define or create a goal
- user asks to set an objective
- user asks what done should mean
- user asks to turn an intention into a measurable target
- success criteria are required before significant work begins
- an existing goal needs refinement
- scope or acceptance criteria have become ambiguous
- a project has activity but no explicit outcome contract

prerequisites:
- user intent is available
- target domain or affected object is identifiable or safely inferable

routing:
  execution: "xninetzy-assignment-orchestrator"
  learning: "it-learning"
  coaching: "xninetzy-learning-coach"
  research: "xninetzy-deep-research"
  personal: "life-management"
  continuity: "xninetzy-memory"
---------------------------

# Define Goal OS

This skill defines **what success means before significant work begins**.

Its purpose is to convert an intention into a goal that a human or agent can pursue
without guessing:

```text
what should become true
where it should become true
how success is observed
what threshold is sufficient
what remains outside scope
what constraints apply
what should stop the work
```

The central principle is:

> **Outcome > activity. Evidence > confidence. Bounded scope > vague ambition.**

A goal is a contract for the desired future state.

It is not a task list.

It is not an execution plan.

It is not a motivational statement.
---

# 1. Goal Model

Canonical goal structure:

```text
GOAL
├── Identity
├── Outcome
├── Target
├── Evidence
├── Acceptance Criteria
├── Measurement
├── Scope
├── Boundary
├── Constraints
├── Assumptions
├── Dependencies
├── Deadline
├── Stop Conditions
└── Status
```

Minimum viable goal:

```text
Outcome
+
Target
+
Evidence
+
Success Criterion
+
Scope
+
Stop Condition
```

A goal that cannot express these elements should be refined before substantial
execution.

---

# 2. Goal vs Other Work Objects

Keep these concepts separate:

```text
GOAL
What state should become true?

PLAN
How will we reach that state?

TASK
What action needs to be performed?

MILESTONE
What intermediate state should exist?

LEARNING OBJECTIVE
What capability should be demonstrated?

DECISION
What choice must be made under constraints?

```

Example:

```text
Goal:
The API returns p95 latency below 300 ms under the defined workload.

Plan:
Profile → identify bottleneck → optimize query → benchmark.

Task:
Add the missing database index.

Milestone:
The query execution plan no longer performs a full table scan.

Learning objective:
Understand query planning and index selection.
```

Do not convert every goal into a checklist.

---

# 3. Lifecycle

Canonical lifecycle:

```text
DETECT
  ↓
INSPECT
  ↓
FORMULATE
  ↓
MEASURE
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

After creation, goals enter a separate execution lifecycle managed by other
skills.

---

# 4. Goal States

Use:

```text
NONE
DRAFT
ACTIVE
PAUSED
BLOCKED
CONFLICTING
COMPLETED
SUPERSEDED
ABANDONED
```

Definitions:

```text
NONE
No applicable goal exists.

DRAFT
Goal is being formulated but has not passed validation.

ACTIVE
Goal is valid and currently relevant.

PAUSED
Goal remains valid but execution is intentionally suspended.

BLOCKED
Goal is valid but a known dependency prevents progress.

CONFLICTING
Goal materially conflicts with another active objective or constraint.

COMPLETED
Defined success evidence has been verified.

SUPERSEDED
A newer version replaced the goal.

ABANDONED
Goal was intentionally discontinued.
```

Never mark a goal `COMPLETED` merely because work was performed.

---

# 5. Goal Identity

Every persistent goal should have:

```yaml
goal:
  goal_id:
  version:
  title:
  outcome:
  status:
  created_at:
  updated_at:
```

`goal_id` identifies the logical objective.

`version` identifies a specific contract.

Material changes create a new version.

---

# 6. Material Goal Changes

The following normally require a new version:

```text
outcome changes
target changes
acceptance threshold changes
scope materially changes
deadline materially changes
validator changes
critical constraint changes
```

Do not silently mutate a goal's historical meaning.

Example:

```text
v1:
API p95 < 300 ms

v2:
API p95 < 150 ms
```

This is a materially different success contract.

---

# 7. Version Semantics

Conceptually:

```text
goal_id = logical objective
goal_version = immutable contract revision
```

Example:

```yaml
goal_id: goal_api_latency
version: 3
```

Previous versions should remain distinguishable in audit/history.

---

# 8. Phase 01 — DETECT

Determine whether the user is expressing:

```text
goal
task
plan
question
capture
decision
learning objective
```

Activity-oriented language often hides a desired outcome.

Examples:

```text
"Improve the dashboard."
"Study Python."
"Fix the API."
"Prepare for the exam."
"Work on the project."
```

Convert activity into an outcome hypothesis:

```text
"What would be observably different when this is successful?"
```

Do not invent a specific outcome when multiple materially different interpretations
exist.

---

# 9. Activity-to-Outcome Transformation

Prefer:

```text
"study SQL"
```

→

```text
"Demonstrate the ability to write and explain SELECT queries, joins, aggregation,
and transactions on the defined assessment."
```

Prefer:

```text
"improve security"
```

→

```text
"Reduce the defined set of high-confidence unresolved security findings to zero
for the target scope."
```

Prefer:

```text
"fix the login"
```

→

```text
"Authenticated users can complete the intended login flow and receive the expected
session state under the defined test scenarios."
```

The wording must remain tied to observable evidence.

---

# 10. Phase 02 — INSPECT

Before creating a persistent goal:

```text
goal_inspect
```

should identify relevant:

```text
active goals
paused goals
conflicting goals
recently completed goals
superseded goals
target/resource bindings
```

Determine:

```text
NO_MATCH
EXISTING_MATCH
MATERIAL_CONFLICT
POSSIBLE_DUPLICATE
```

---

# 11. Goal Deduplication

Prefer refining an existing goal when:

```text
same logical outcome
same target
same broad scope
same timeframe
```

Create a separate goal when:

```text
different outcome
different target
independent acceptance criteria
independent ownership
independent deadline
```

Never create duplicate goals merely because the wording differs.

---

# 12. Conflict Detection

Possible conflicts:

```text
goal vs goal
goal vs system constraint
goal vs deadline
goal vs resource limit
goal vs security policy
goal vs approved scope
goal vs current project state
```

Example:

```text
Goal A:
reduce API latency

Goal B:
avoid changing database schema

If the evidence indicates the required optimization needs a schema change,
the goals are potentially conflicting.
```

Do not silently resolve the conflict.

---

# 13. Conflict Record

```yaml
conflict:
  conflict_id:
  goal_id:
  other_goal_id:
  type:
  description:
  affected_constraint:
  materiality:
  resolution_status:
```

Possible:

```text
UNRESOLVED
RESOLVED_BY_SCOPE_CHANGE
RESOLVED_BY_PRIORITY
RESOLVED_BY_DEADLINE_CHANGE
SUPERSEDED
BLOCKED
```

Only the owner or authorized decision-maker should resolve consequential priority
conflicts when authority is not already defined.

---

# 14. Phase 03 — FORMULATE

Construct the goal from explicit components:

```yaml
goal_contract:
  outcome:
  target:
  evidence:
  success_criteria:
  scope:
  out_of_scope:
  constraints:
  assumptions:
  dependencies:
  deadline:
  stop_conditions:
```

The contract should be concise enough to execute against but precise enough to
audit.

---

# 15. Outcome

The outcome describes the desired future state.

Weak:

```text
"Work on the authentication system."
```

Strong:

```text
"Users with valid credentials can complete authentication and receive a valid
application session."
```

An outcome should describe **what is true**, not merely what someone does.

---

# 16. Target

Identify what the goal changes or evaluates.

Possible targets:

```text
repository
service
module
API
database
document
dataset
model
learning capability
project phase
environment
decision
workflow
personal commitment
```

Example:

```yaml
target:
  type: repository
  identifier: project-x
  environment: staging
```

Avoid vague targets such as:

```text
"the system"
"the project"
"everything"
```

unless the system/project is itself the intentionally bounded target.

---

# 17. Evidence

Evidence must answer:

```text
"What would we observe that proves the outcome exists?"
```

Evidence may be:

```text
test result
benchmark
measurement
artifact
diff
dataset statistic
deployment state
evaluation score
completed deliverable
verified system behavior
external authoritative record
```

Do not treat:

```text
"I believe it works"
```

as evidence.

---

# 18. Evidence Hierarchy

Prefer:

```text
DIRECT VERIFICATION
    >
REPRODUCIBLE MEASUREMENT
    >
DERIVED METRIC
    >
SUPPORTED OBSERVATION
    >
SELF-REPORT
    >
ASSUMPTION
```

The required evidence strength depends on consequence.

For consequential goals, prefer direct or reproducible verification.

---

# 19. Acceptance Criteria

Acceptance criteria define the boundary between:

```text
NOT DONE
```

and:

```text
DONE
```

Use measurable conditions where meaningful.

Examples:

```text
all required tests pass
p95 latency < 300 ms
coverage >= defined threshold
100% of required files generated
dataset contains >= N verified samples
all requested sections exist
model reaches >= defined validation metric
```

Binary criteria are preferred when practical.

---

# 20. Measurement Policy

Use numbers only when the measurement has real meaning.

Good:

```text
p95 < 300 ms
```

Bad:

```text
quality = 93.7%
```

when no validated quality measure exists.

Do not manufacture precision to make a goal appear measurable.

Use:

```text
PASS
FAIL
UNKNOWN
```

when a binary validator is more appropriate.

---

# 21. Threshold Design

For each quantitative criterion define:

```yaml
metric:
  name:
  direction:
  threshold:
  unit:
  measurement_method:
  population:
  environment:
  baseline:
```

Example:

```yaml
metric:
  name: p95_latency
  direction: "<"
  threshold: 300
  unit: ms
  measurement_method: benchmark_suite
  environment: staging
```

Without a measurement method, a number may not be reproducible.

---

# 22. Baseline

When meaningful, capture the baseline:

```text
CURRENT
TARGET
DELTA
```

Example:

```text
Current p95:
420 ms

Target:
<300 ms

Required improvement:
>120 ms reduction
```

Never assume the baseline is known if it has not been measured.

---

# 23. Scope

Scope answers:

```text
What is included?
```

Examples:

```text
files:
apps/api/**

endpoints:
POST /auth/login

dataset:
training split only

environment:
staging

time:
September 2026 release window
```

Scope should be machine-bindable when possible.

---

# 24. Out of Scope

Explicitly state what is excluded.

Examples:

```text
mobile application
production database migration
unrelated endpoints
UI redesign
historical datasets
```

Out-of-scope boundaries prevent accidental expansion.

---

# 25. Constraints

Possible constraints:

```text
time
budget
technology
API compatibility
security
privacy
compute
dataset availability
institution policy
existing architecture
approval requirements
```

Represent hard and soft constraints separately.

```yaml
constraints:
  hard: []
  soft: []
```

A hard constraint violation should block goal acceptance or require explicit
reconciliation.

---

# 26. Assumptions

Every consequential assumption should be explicit.

```yaml
assumptions:
  - id:
    statement:
    impact:
    validation:
```

Examples:

```text
staging data is representative
benchmark environment is stable
required API is available
existing schema is compatible
```

Unknown critical assumptions become validation dependencies.

---

# 27. Dependencies

A dependency is a condition outside the goal's direct control.

```yaml
dependencies:
  - id:
    description:
    owner:
    status:
    blocking:
```

Possible state:

```text
AVAILABLE
PENDING
BLOCKED
UNKNOWN
```

A blocked hard dependency can move the goal to:

```text
BLOCKED
```

---

# 28. Deadline

A deadline is a temporal boundary, not proof of success.

Represent:

```yaml
deadline:
  due_at:
  timezone:
  hard:
```

Do not define success as:

```text
"finish by Friday"
```

without defining what must actually be true by Friday.

---

# 29. Stop Conditions

A goal must specify when work should stop rather than continue indefinitely.

Examples:

```text
acceptance criteria pass
required evidence unavailable
scope would need to expand
hard dependency remains blocked
security boundary would be weakened
cost exceeds approved limit
deadline expires without enough evidence
target becomes obsolete
goal conflicts materially with a higher-authority constraint
```

A stop condition is a safety boundary.

---

# 30. Phase 04 — MEASURE

Convert vague success into observable validators.

For each criterion define:

```yaml
criterion:
  criterion_id:
  description:
  validator:
  threshold:
  evidence_required:
  blocking:
```

Example:

```yaml
criterion:
  criterion_id: C1
  description: "All authentication integration tests pass."
  validator: "repo_test(auth-integration)"
  threshold: "100% required tests pass"
  evidence_required: "test_result"
  blocking: true
```

---

# 31. Validator Contract

A validator should answer:

```text
PASS
FAIL
UNKNOWN
```

Optionally:

```text
PARTIAL
```

for inherently partial outcomes.

The validator must define what it measures.

Do not use:

```text
"looks good"
"seems finished"
"probably works"
```

as formal validators.

---

# 32. Evidence Freshness

Evidence can become stale.

Examples:

```text
test result from old commit
quota from previous session
benchmark from previous environment
deployment state from previous release
```

Each evidence record should include:

```yaml
evidence:
  source:
  observed_at:
  target:
  environment:
  version:
  freshness:
```

Goal completion may require fresh evidence.

---

# 33. Goal Completion Evidence

A goal is completed only when:

```text
all blocking acceptance criteria pass
+
required evidence exists
+
evidence belongs to the intended target
+
evidence is sufficiently fresh
+
no unresolved material scope drift exists
```

---

# 34. Phase 05 — BOUND

Bind the goal to operational dimensions:

```text
target
scope
environment
time
resources
tools
ownership
blast radius
```

Example:

```yaml
bounds:
  repository: project-x
  environment: staging
  files:
    - apps/api/**
  max_changed_files: 15
  allowed_tools:
    - repo_search
    - repo_test
```

Only include a bound when it is meaningful.

---

# 35. Blast Radius

For engineering goals, optionally define:

```text
maximum affected services
maximum files changed
maximum data affected
allowed environments
allowed API surface
```

A goal should not silently authorize work outside its intended blast radius.

---

# 36. Goal Preconditions

Before accepting the goal:

```yaml
preconditions:
  - condition:
    status:
```

Possible:

```text
SATISFIED
UNSATISFIED
UNKNOWN
```

A critical unsatisfied precondition should block execution planning.

---

# 37. Phase 06 — VALIDATE

Run the goal-quality gate.

Required checks:

```text
OUTCOME_TEST
TARGET_TEST
EVIDENCE_TEST
CRITERION_TEST
SCOPE_TEST
BOUNDARY_TEST
REPRODUCIBILITY_TEST
STOP_TEST
CONFLICT_TEST
```

---

# 38. Outcome Test

Ask:

```text
Can a future observer distinguish success from non-success?
```

If no:

```text
REFINE
```

---

# 39. Evidence Test

Ask:

```text
What specific observation proves success?
```

If unavailable:

```text
add validator
or
classify goal as insufficiently verifiable
```

---

# 40. Criterion Test

Ask:

```text
Can two independent evaluators reach the same PASS/FAIL conclusion?
```

Prefer:

```text
PASS
FAIL
UNKNOWN
```

over subjective interpretation.

---

# 41. Scope Test

Ask:

```text
What exactly is included?
What exactly is excluded?
```

If the answer is unclear, the goal is not ready.

---

# 42. Reproducibility Test

Ask:

```text
Can the success evidence be reproduced or independently checked?
```

For deterministic systems, prefer automated validation.

For subjective domains, define the evaluator and evidence source explicitly.

---

# 43. Stop Test

Ask:

```text
When should the agent stop instead of continuing?
```

If none exists, add one.

---

# 44. Phase 07 — RECONCILE

Compare the proposed goal against:

```text
active goals
current project state
hard constraints
existing commitments
dependencies
approved scope
recently completed work
```

Detect:

```text
DUPLICATE
REFINEMENT
CONFLICT
SUPERSESSION
NEW_GOAL
```

---

# 45. Reconciliation Rule

When an active goal remains aligned:

```text
reuse / refine
```

When materially different:

```text
new version
```

When conflicting:

```text
surface conflict
```

Never silently delete or overwrite another active objective.

---

# 46. Goal Drift

Goal drift occurs when execution gradually changes:

```text
outcome
target
scope
acceptance criteria
deadline
```

without explicit goal revision.

Detect drift from:

```text
current goal version
vs
current task/plan state
```

If material drift occurs:

```text
GOAL_DRIFT
```

and return for reconciliation.

---

# 47. Goal vs Current Reality

A goal can become invalid because the world changed.

Examples:

```text
target removed
feature already exists
dataset unavailable
deadline passed
API deprecated
project cancelled
constraint changed
```

Do not force execution against an obsolete goal.

Possible result:

```text
SUPERSEDED
ABANDONED
REFINE
```

---

# 48. Phase 08 — VERSION

Before persistence:

```text
logical identity
+
contract version
```

must be determined.

Use:

```text
same goal_id
new version
```

when refining the same logical objective.

Use:

```text
new goal_id
```

when the objective is materially independent.

---

# 49. Create vs Refine

## CREATE

Use when:

```text
no equivalent active goal exists
```

## REFINE

Use when:

```text
same logical goal
but clearer outcome / scope / validator / boundary
```

## SUPERSEDE

Use when:

```text
new goal version replaces the previous objective
```

## REJECT / BLOCK

Use when:

```text
critical ambiguity
unresolved conflict
missing validator
unsafe scope
impossible hard constraint
```

---

# 50. Goal Storage Contract

Persistent representation:

```yaml
goal:
  goal_id:
  version:
  title:

  outcome:
  target:

  evidence:
    required: []
    sources: []

  success_criteria: []

  scope:
  out_of_scope:

  constraints:
    hard: []
    soft: []

  assumptions: []
  dependencies: []

  deadline:
  stop_conditions: []

  status:

  provenance:
    source:
    created_at:
    updated_at:
```

Do not store secrets inside goals.

---

# 51. Goal Fingerprint

For duplicate detection and continuity, derive a normalized fingerprint from:

```text
outcome
target
scope
deadline
```

Do not include volatile timestamps or secrets.

The fingerprint is an identity aid.

It is not a proof of semantic equivalence.

---

# 52. Goal Completion Contract

A completed goal should resolve:

```yaml
completion:
  goal_id:
  version:

  status: COMPLETED

  criteria:
    - criterion_id:
      result:
      evidence_refs: []

  evidence:
    - source:
      observed_at:
      target:
      environment:

  unresolved: []

  completed_at:
```

Completion must be evidence-backed.

---

# 53. Partial Completion

Do not force binary completion when the objective is genuinely partial.

Use:

```text
PARTIAL
```

when:

```text
some criteria pass
but blocking criteria remain unresolved
```

However, `PARTIAL` must not be treated as `COMPLETED`.

---

# 54. Unknown Completion

Use:

```text
UNKNOWN
```

when the goal may have succeeded but required evidence cannot establish it.

Examples:

```text
deployment response timed out
benchmark could not run
external authoritative system unavailable
verification environment unavailable
```

Never convert `UNKNOWN` into success because the expected action was performed.

---

# 55. Goal Health

A persistent goal can expose:

```text
ON_TRACK
AT_RISK
BLOCKED
DRIFTING
STALE
COMPLETED
```

These are health states, not success states.

A goal may be:

```text
ON_TRACK
```

without being complete.

---

# 56. Goal Health Inputs

Health may be derived from:

```text
deadline proximity
dependency state
recent progress
scope drift
evidence availability
blocking failures
resource constraints
```

Avoid arbitrary "percentage complete" values unless progress is backed by meaningful
measurement.

---

# 57. Goal Progress

Progress should be represented by completed validated milestones or criteria.

Prefer:

```text
3/5 acceptance criteria verified
```

over:

```text
60% done
```

unless the criteria are intentionally weighted and the weighting is meaningful.

---

# 58. Learning Objective Variant

For learning goals, outcome must describe demonstrated capability.

Weak:

```text
"Study React."
```

Strong:

```text
"Build and explain a React feature that uses state, controlled forms, and async
data loading, validated through the defined exercise."
```

Evidence may include:

```text
working artifact
assessment result
oral explanation
code review
problem-solving performance
```

Exposure time alone is usually not enough evidence of competence.

---

# 59. Research Goal Variant

Research goals should distinguish:

```text
question
population/data
method
evidence standard
deliverable
uncertainty boundary
```

Example:

```yaml
research_goal:
  question:
  evidence_required:
  population:
  method:
  deliverable:
  uncertainty_boundary:
```

Do not define research success as:

```text
"find evidence supporting hypothesis X"
```

when the evidence may disconfirm it.

Prefer:

```text
"determine whether the evidence supports, weakens, or fails to resolve X under
the predefined method."
```

---

# 60. Engineering Goal Variant

For software goals, prefer:

```text
target repository
target component
behavioral outcome
validator
environment
regression requirement
scope boundary
```

Example:

```text
Outcome:
The authentication endpoint returns the intended response for all defined
valid and invalid credential scenarios.

Evidence:
integration test suite.

Threshold:
100% required scenarios pass.

Scope:
POST /auth/login in staging.

Out of scope:
UI redesign.
```

---

# 61. Operational Goal Variant

For operational work:

```text
desired system state
affected environment
metric
threshold
observation window
rollback/stop condition
```

Do not define a goal solely as:

```text
"monitor the service"
```

Prefer:

```text
"Maintain the service below the defined error-rate threshold for the observation
window, with alerting verified."
```

---

# 62. Decision Goal Variant

For decisions, success is not "pick an option."

Instead define:

```text
decision question
decision deadline
criteria
available evidence
constraints
required decision artifact
```

Example:

```text
Goal:
Produce a documented architecture decision for the selected service boundary,
using the predefined criteria and evidence set.
```

The decision itself may remain uncertain.

---

# 63. Consequential Goals

For goals affecting:

```text
production
financial state
academic state
security posture
privacy
external users
irreversible data
```

require stronger:

```text
scope binding
validator
evidence
approval
stop conditions
```

The goal definition skill does not itself grant permission to perform the action.

Authorization belongs to the relevant execution/policy layer.

---

# 64. Safety Boundary

Goal definition must never implicitly create authority.

This:

```text
Goal:
Submit KRS with selected courses.
```

does not imply:

```text
permission to submit
```

Similarly:

```text
Goal:
Deploy to production.
```

does not imply:

```text
production deployment authorization
```

The goal expresses desired outcome, not execution authority.

---

# 65. Assumption Escalation

If a hidden assumption could materially change the goal:

```text
assumption
→ uncertainty
→ validation question
```

Ask one concise question only when the ambiguity can materially change:

```text
outcome
target
validator
scope
deadline
authority
```

Do not ask for information that can be safely inferred.

---

# 66. Clarification Rule

Use a clarification question when:

```text
interpretation A → materially different outcome
interpretation B → materially different outcome
```

Do not ask when:

```text
multiple phrasings
minor formatting
non-material implementation preference
information already present in context
```

Preferred question shape:

```text
"What should count as success: A or B?"
```

Avoid:

```text
"Can you provide more details?"
```

---

# 67. Output Contract

After goal creation/refinement, return:

```yaml
goal_result:
  operation:
  goal_id:
  version:
  status:

  outcome:
  target:

  success_criteria:
    - id:
      criterion:
      validator:

  scope:
  out_of_scope:

  constraints:
  assumptions:
  dependencies:

  deadline:
  stop_conditions:

  conflicts:
  evidence_requirements:

  next_action:
```

The user-facing version should be concise.

---

# 68. Canonical User-Facing Goal

Preferred rendering:

```text
Goal:
[one sentence describing the desired future state]

Target:
[affected object]

Success:
[observable threshold / validator]

Evidence:
[what proves success]

Scope:
[what is included]

Out of scope:
[what is excluded]

Deadline:
[when applicable]

Stop conditions:
[when work must stop]

Status:
[DRAFT / ACTIVE / ...]
```

Avoid turning the response into an execution plan.

---

# 69. Completion Verification

Before marking `COMPLETED`, verify:

```text
goal version matches executed work
target matches evidence
all blocking criteria pass
evidence is sufficiently fresh
scope remained within bounds
no unresolved material contradiction exists
```

Then:

```text
COMPLETED
```

Otherwise:

```text
PARTIAL
UNKNOWN
BLOCKED
```

as appropriate.

---

# 70. Goal Learning

The system may learn:

```text
better goal formulations
better validators
better evidence sources
better ambiguity detection
better duplicate detection
better conflict detection
better domain-specific goal patterns
```

The system must not learn:

```text
broader authority
automatic approvals
security bypasses
unbounded execution rights
silent scope expansion
```

Learning improves goal quality, not authority.

---

# 71. Memory Integration

When memory is available:

```text
memory
→ previous goals
→ recurring objective patterns
→ validated goal templates
→ known validator mappings
```

Memory is advisory.

Current user intent and current system state take precedence over historical goals.

A previous goal does not automatically remain active forever.

---

# 72. Context Integration

The goal should provide downstream skills with a compact context object:

```yaml
goal_context:
  goal_id:
  version:
  outcome:
  target:
  success_criteria:
  scope:
  out_of_scope:
  constraints:
  deadline:
  stop_conditions:
```

Downstream planning and execution skills should consume this object instead of
reconstructing the user's intent from conversation history.

---

# 73. Routing

After goal definition:

```text
complex execution
→ xninetzy-assignment-orchestrator

learning capability
→ it-learning / xninetzy-learning-coach

research
→ xninetzy-deep-research

personal commitment
→ life-management

cross-session continuity
→ xninetzy-memory
```

This skill stops at a validated goal contract.

It must not absorb downstream planning responsibilities.

---

# 74. Reference Map

When available:

```text
references/anatomy.md
→ outcome patterns, evidence hierarchy, validators, domain-specific goal forms

references/lifecycle.md
→ state machine, conflict handling, versioning, refinement, completion

references/validation.md
→ acceptance criteria, metrics, reproducibility, evidence quality
```

Load only the reference needed for the current goal-definition problem.

---

# 75. Anti-Patterns

Never create goals like:

```text
"Work on the backend."
"Improve the app."
"Study more."
"Make it better."
"Finish the project."
"Do security."
"Prepare everything."
"Fix all bugs."
"Optimize performance."
```

unless these are refined into observable outcomes.

Avoid:

```text
activity disguised as outcome
```

```text
measurement without a validator
```

```text
arbitrary numeric precision
```

```text
hidden scope
```

```text
unstated assumptions
```

```text
deadline mistaken for success
```

```text
execution permission inferred from goal definition
```

```text
historical goal silently treated as current
```

```text
completion claimed without evidence
```

---

# 76. Goal Quality Gate

A goal is `VALID` only when:

```text
[✓] outcome is concrete
[✓] target is identifiable
[✓] evidence exists
[✓] success criteria are evaluable
[✓] scope is bounded
[✓] exclusions are explicit where useful
[✓] hard constraints are known
[✓] material assumptions are explicit
[✓] dependencies are identified
[✓] stop conditions exist
[✓] conflicts are reconciled
[✓] completion can be independently recognized
```

If a critical check fails:

```text
REFINE
```

not:

```text
CREATE
```

---

# 77. Golden Workflow — Simple Goal

```text
INTENTION
   ↓
OUTCOME
   ↓
TARGET
   ↓
EVIDENCE
   ↓
SUCCESS CRITERION
   ↓
SCOPE
   ↓
STOP CONDITION
   ↓
VALIDATE
   ↓
CREATE
```

---

# 78. Golden Workflow — Existing Goal

```text
REQUEST
   ↓
INSPECT ACTIVE GOALS
   ↓
MATCH?
 ┌──┴─────────────┐
YES               NO
 ↓                 ↓
REFINE?          FORMULATE
 ↓                 ↓
VALIDATE         VALIDATE
 └──────┬──────────┘
        ↓
RECONCILE
        ↓
VERSION
        ↓
UPDATE / CREATE
```

---

# 79. Golden Workflow — Completion

```text
ACTIVE GOAL
    ↓
EXECUTION
    ↓
VALIDATORS
    ↓
EVIDENCE
    ↓
CRITERIA CHECK
    ↓
SCOPE CHECK
    ↓
FRESHNESS CHECK
    ↓
COMPLETED
```

If evidence is insufficient:

```text
UNKNOWN
```

If blocking criteria fail:

```text
INCOMPLETE / BLOCKED
```

Do not manufacture completion.

---

# 80. Non-Negotiable Operating Rules

The system must:

```text
define outcomes rather than activities
identify the target explicitly
define observable evidence
prefer meaningful measurement
avoid artificial precision
define binary validators where practical
bound scope
define exclusions when ambiguity exists
surface consequential assumptions
identify blocking dependencies
define explicit stop conditions
inspect existing goals before creating duplicates
detect material conflicts
never silently replace active goals
version materially changed goal contracts
preserve historical goal meaning
distinguish goal from plan
distinguish goal from task
distinguish learning objective from exposure
distinguish desired outcome from authority to execute
treat current state as authoritative over stale goal assumptions
require evidence before completion
preserve uncertainty explicitly
prevent silent goal drift
use memory as advisory context
learn goal-quality patterns without expanding authority
route execution to downstream skills
```

---

# 81. Central Principle

> **Before work begins, define the future state precisely enough that the user, agent, validator, and auditor can independently recognize whether the goal has been achieved — without guessing what "done" means.**
