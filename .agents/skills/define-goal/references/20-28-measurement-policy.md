# define-goal — §20–28

Contents: 20. Measurement Policy; 21. Threshold Design; 22. Baseline; 23. Scope; 24. Out of Scope; 25. Constraints; 26. Assumptions; 27. Dependencies; 28. Deadline

## 20. Measurement Policy

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

## 21. Threshold Design

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

## 22. Baseline

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

## 23. Scope

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

## 24. Out of Scope

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

## 25. Constraints

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

## 26. Assumptions

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

## 27. Dependencies

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

## 28. Deadline

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
