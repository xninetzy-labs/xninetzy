# code-review — §39–48

Contents: 39. Observability; 40. Test Analysis; 41. Coverage Delta; 42. Test Adequacy; 43. Missing Tests; 44. Regression Risk; 45. Blast Radius; 46. Backward Compatibility; 47. Database Changes; 48. Background Jobs

## 39. Observability

A behavior change should preserve sufficient observability.

Check:

```text
logs
metrics
traces
request IDs
audit events
error context
```

Particularly for:

```text
auth
billing
security
state transitions
background jobs
external integrations
```

Do not request sensitive payloads simply to improve logging.

---

## 40. Test Analysis

Use:

```text
repo_test
```

where available.

Determine:

```text
tests added
tests modified
tests removed
tests covering changed behavior
tests covering failure paths
regression coverage
integration coverage
authorization coverage
```

Passing tests are evidence of tested behavior, not proof of complete correctness.

---

## 41. Coverage Delta

Required:

```yaml
coverage:
  lines_added:
  lines_changed:
  lines_covered:
  coverage_pct:
  baseline_coverage_pct:
  delta:
```

If exact coverage is unavailable:

```text
UNKNOWN
```

Do not invent coverage percentages.

---

## 42. Test Adequacy

A change should have tests proportional to behavioral risk.

Examples:

```text
pure rename
  -> focused static check may suffice

new parser
  -> valid + invalid inputs

new auth rule
  -> allow + deny matrix

new retry
  -> retryable + non-retryable + exhaustion

new API endpoint
  -> success + validation + auth + error

new state transition
  -> valid + invalid transitions
```

---

## 43. Missing Tests

Do not flag:

```text
"no tests"
```

as automatically high severity.

Instead determine:

```text
risk
behavioral change
existing test architecture
testability
criticality
```

Possible severity:

```text
INFO
LOW
MEDIUM
HIGH
```

depending on evidence.

---

## 44. Regression Risk

Identify what can break outside the diff.

Use:

```text
repo_symbol
repo_dependency
repo_architecture
repo_diff
```

Trace:

```text
changed symbol
 ↓
direct callers
 ↓
indirect callers
 ↓
public APIs
 ↓
affected modules
```

Classify:

```text
LOCAL
MODERATE
WIDE
SYSTEMIC
UNKNOWN
```

---

## 45. Blast Radius

For shared code measure:

```text
fan_in
fan_out
affected callers
affected modules
public API count
```

A one-line change in a highly central module may deserve more scrutiny than
a large isolated refactor.

---

## 46. Backward Compatibility

Check:

```text
API
database schema
serialization
configuration
CLI
environment variables
events
queues
file formats
```

Possible change:

```text
compatible
migration_required
breaking
unknown
```

Do not assume all internal code can change freely when a public contract exists.

---

## 47. Database Changes

For migrations inspect:

```text
schema change
existing data
nullability
indexes
foreign keys
rollback
deployment ordering
application compatibility
```

Potential issue:

```text
application deploy
before
schema exists
```

or:

```text
schema removal
before
old application removed
```

Review migration sequencing.

---

## 48. Background Jobs

When queue/worker behavior changes inspect:

```text
job identity
retry
idempotency
visibility timeout
dead-letter behavior
ordering
duplicate execution
serialization
```

A worker may execute the same job more than once even if application code appears
single-shot.

---
