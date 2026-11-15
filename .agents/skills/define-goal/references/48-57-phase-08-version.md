# define-goal — §48–57

Contents: 48. Phase 08 — VERSION; 49. Create vs Refine; 50. Goal Storage Contract; 51. Goal Fingerprint; 52. Goal Completion Contract; 53. Partial Completion; 54. Unknown Completion; 55. Goal Health; 56. Goal Health Inputs; 57. Goal Progress

## 48. Phase 08 — VERSION

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

## 49. Create vs Refine

### CREATE

Use when:

```text
no equivalent active goal exists
```

### REFINE

Use when:

```text
same logical goal
but clearer outcome / scope / validator / boundary
```

### SUPERSEDE

Use when:

```text
new goal version replaces the previous objective
```

### REJECT / BLOCK

Use when:

```text
critical ambiguity
unresolved conflict
missing validator
unsafe scope
impossible hard constraint
```

---

## 50. Goal Storage Contract

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

## 51. Goal Fingerprint

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

## 52. Goal Completion Contract

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

## 53. Partial Completion

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

## 54. Unknown Completion

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

## 55. Goal Health

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

## 56. Goal Health Inputs

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

## 57. Goal Progress

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
