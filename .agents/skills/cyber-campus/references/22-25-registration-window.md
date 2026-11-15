# cyber-campus — §22–25

Contents: 22. Registration Window; 23. Planning State; 24. Dry Run; 25. Action Hash

## 22. Registration Window

Before KRS planning verify:

```text
registration_open
registration_close
current_time
portal_time
```

Classify:

```text
OPEN
NOT_YET_OPEN
CLOSED
UNKNOWN
```

Never use a historical deadline as current state.

---

## 23. Planning State

Planning state must be separate from portal state.

Example:

```yaml
plan:
  period: "2026/2027 Ganjil"
  additions:
    - course_code: IF101
      class: A
  removals:
    - course_code: IF204
  total_credits_after:
  conflicts:
  quota_risks:
  prerequisite_failures:
  eligibility_failures:
```

A plan is not yet an action.

---

## 24. Dry Run

A KRS dry run must calculate:

```text
selected courses
removed courses
final credit count
schedule conflicts
quota risks
prerequisite failures
eligibility failures
registration window
existing KRS state
unknown conditions
```

No portal mutation.

Output:

```text
DRY_RUN_READY
DRY_RUN_BLOCKED
DRY_RUN_UNCERTAIN
```

---

## 25. Action Hash

Before approval generate a deterministic action hash.

Conceptually:

```text
sha256(
  portal
  +
period
  +
current_krs_hash
  +
additions
  +
removals
  +
selected_classes
)
```

Include:

```text
normalized course identifiers
class identifiers
action type
academic period
```

Do not hash mutable prose.

Store:

```yaml
approval_binding:
  action_hash:
  generated_at:
  plan_version:
```

---
