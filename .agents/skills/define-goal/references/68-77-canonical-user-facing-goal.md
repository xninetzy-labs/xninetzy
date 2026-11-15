# define-goal — §68–77

Contents: 68. Canonical User-Facing Goal; 69. Completion Verification; 70. Goal Learning; 71. Memory Integration; 72. Context Integration; 73. Routing; 74. Reference Map; 75. Anti-Patterns; 76. Goal Quality Gate; 77. Golden Workflow — Simple Goal

## 68. Canonical User-Facing Goal

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

## 69. Completion Verification

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

## 70. Goal Learning

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

## 71. Memory Integration

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

## 72. Context Integration

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

## 73. Routing

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

## 74. Reference Map

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

## 75. Anti-Patterns

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

## 76. Goal Quality Gate

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

## 77. Golden Workflow — Simple Goal

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
