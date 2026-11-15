# define-goal — §8–13

Contents: 8. Phase 01 — DETECT; 9. Activity-to-Outcome Transformation; 10. Phase 02 — INSPECT; 11. Goal Deduplication; 12. Conflict Detection; 13. Conflict Record

## 8. Phase 01 — DETECT

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

## 9. Activity-to-Outcome Transformation

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

## 10. Phase 02 — INSPECT

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

## 11. Goal Deduplication

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

## 12. Conflict Detection

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

## 13. Conflict Record

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
