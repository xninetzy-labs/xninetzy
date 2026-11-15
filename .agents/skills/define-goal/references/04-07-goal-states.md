# define-goal — §4–7

Contents: 4. Goal States; 5. Goal Identity; 6. Material Goal Changes; 7. Version Semantics

## 4. Goal States

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

## 5. Goal Identity

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

## 6. Material Goal Changes

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

## 7. Version Semantics

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
