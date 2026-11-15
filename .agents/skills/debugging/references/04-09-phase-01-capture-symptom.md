# debugging — §4–9

Contents: 4. Phase 01 — CAPTURE SYMPTOM; 5. Phase 02 — SCOPE; 6. Scope Integrity; 7. Phase 03 — REPRODUCE; 8. Reproduction Quality; 9. Flaky / Intermittent Debugging

## 4. Phase 01 — CAPTURE SYMPTOM

Capture the operator's statement without prematurely interpreting it.

Required:

```yaml
symptom:
  reported_at:
  reporter:
  system:
  component:
  environment:
  expected_behavior:
  observed_behavior:
  exact_error:
  affected_operation:
  first_known_occurrence:
  recurrence:
  scope:
```

Preserve exact error messages when useful.

Do not rewrite:

```text
"returns 403"
```

into:

```text
"authorization bug"
```

before evidence exists.

---

## 5. Phase 02 — SCOPE

Define the debugging boundary:

```text
repository
service
module
symbol
request
job
database operation
external dependency
environment
deployment
```

Also identify:

```text
branch
commit
build
runtime version
dependency version
configuration source
feature flags
tenant/user scope when relevant
```

Scope must be narrow enough to debug and broad enough to include the actual
execution path.

---

## 6. Scope Integrity

Do not alter the debugging target while investigating.

A changed:

```text
branch
commit
configuration
dependency
environment
request
input
feature flag
```

may invalidate previous evidence.

Record material environment changes explicitly.

---

## 7. Phase 03 — REPRODUCE

The first objective is deterministic reproduction.

Produce:

```text
reproduction_recipe
```

with:

```yaml
reproduction:
  prerequisites: []
  setup: []
  command:
  request:
  input:
  expected:
  actual:
  reproduction_rate:
  attempts:
  environment:
  commit:
```

A reproduction is stronger when it can be run repeatedly with the same result.

---

## 8. Reproduction Quality

Classify:

```text
DETERMINISTIC
REPEATABLE
INTERMITTENT
RARE
NON_REPRODUCIBLE
UNKNOWN
```

Suggested confidence:

```text
DETERMINISTIC
→ failure reproduced consistently

REPEATABLE
→ failure reproduced under controlled repetition

INTERMITTENT
→ failure appears under some executions

RARE
→ failure reproduced only under limited conditions

NON_REPRODUCIBLE
→ available evidence cannot reproduce it
```

Do not fabricate deterministic reproduction from a single observation.

---

## 9. Flaky / Intermittent Debugging

For intermittent failures, collect:

```text
attempt_number
timestamp
input_fingerprint
runtime
environment
concurrency
ordering
latency
result
error
trace_id
```

Estimate the observed failure frequency:

```text
failure_rate =
failed_attempts / total_attempts
```

Do not label a failure:

```text
"race condition"
```

merely because it is intermittent.

Intermittence is evidence about reproducibility, not proof of mechanism.

---
