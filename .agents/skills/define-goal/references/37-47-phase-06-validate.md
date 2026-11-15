# define-goal — §37–47

Contents: 37. Phase 06 — VALIDATE; 38. Outcome Test; 39. Evidence Test; 40. Criterion Test; 41. Scope Test; 42. Reproducibility Test; 43. Stop Test; 44. Phase 07 — RECONCILE; 45. Reconciliation Rule; 46. Goal Drift; 47. Goal vs Current Reality

## 37. Phase 06 — VALIDATE

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

## 38. Outcome Test

Ask:

```text
Can a future observer distinguish success from non-success?
```

If no:

```text
REFINE
```

---

## 39. Evidence Test

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

## 40. Criterion Test

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

## 41. Scope Test

Ask:

```text
What exactly is included?
What exactly is excluded?
```

If the answer is unclear, the goal is not ready.

---

## 42. Reproducibility Test

Ask:

```text
Can the success evidence be reproduced or independently checked?
```

For deterministic systems, prefer automated validation.

For subjective domains, define the evaluator and evidence source explicitly.

---

## 43. Stop Test

Ask:

```text
When should the agent stop instead of continuing?
```

If none exists, add one.

---

## 44. Phase 07 — RECONCILE

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

## 45. Reconciliation Rule

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

## 46. Goal Drift

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

## 47. Goal vs Current Reality

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
