---
name: define-goal
description: Turns vague intentions, requests or projects into bounded, measurable, verifiable outcomes with acceptance and stopping criteria. Use before significant work when success or scope is unclear.
metadata:
  keywords: are concrete conditions control converting definition evidence for goal learning needs objectives operational plane questions research
---

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

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/02-goal-vs-other-work-objects.md` — §2: Goal vs Other Work Objects
- `references/04-07-goal-states.md` — §4–7: Goal States, Goal Identity, Material Goal Changes, Version Semantics
- `references/08-13-phase-01-detect.md` — §8–13: Phase 01 — DETECT, Activity-to-Outcome Transformation, Phase 02 — INSPECT, Goal Deduplication, Conflict Detection, Conflict Record
- `references/15-18-outcome.md` — §15–18: Outcome, Target, Evidence, Evidence Hierarchy
- `references/20-28-measurement-policy.md` — §20–28: Measurement Policy, Threshold Design, Baseline, Scope, Out of Scope, Constraints, Assumptions, Dependencies, Deadline
- `references/30-36-phase-04-measure.md` — §30–36: Phase 04 — MEASURE, Validator Contract, Evidence Freshness, Goal Completion Evidence, Phase 05 — BOUND, Blast Radius, Goal Preconditions
- `references/37-47-phase-06-validate.md` — §37–47: Phase 06 — VALIDATE, Outcome Test, Evidence Test, Criterion Test, Scope Test, Reproducibility Test, Stop Test, Phase 07 — RECONCILE, Reconciliation Rule, Goal Drift, Goal vs Current Reality
- `references/48-57-phase-08-version.md` — §48–57: Phase 08 — VERSION, Create vs Refine, Goal Storage Contract, Goal Fingerprint, Goal Completion Contract, Partial Completion, Unknown Completion, Goal Health, Goal Health Inputs, Goal Progress
- `references/58-66-learning-objective-variant.md` — §58–66: Learning Objective Variant, Research Goal Variant, Engineering Goal Variant, Operational Goal Variant, Decision Goal Variant, Consequential Goals, Safety Boundary, Assumption Escalation, Clarification Rule
- `references/68-77-canonical-user-facing-goal.md` — §68–77: Canonical User-Facing Goal, Completion Verification, Goal Learning, Memory Integration, Context Integration, Routing, Reference Map, Anti-Patterns, Goal Quality Gate, Golden Workflow — Simple Goal
- `references/78-79-golden-workflow-existing-goal.md` — §78–79: Golden Workflow — Existing Goal, Golden Workflow — Completion
