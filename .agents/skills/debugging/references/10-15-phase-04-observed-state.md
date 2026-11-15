# debugging — §10–15

Contents: 10. Phase 04 — OBSERVED STATE; 11. Evidence Table; 12. Evidence Hierarchy; 13. Evidence Quality; 14. Phase 05 — BOUNDARY LOCALIZATION; 15. First Incorrect State

## 10. Phase 04 — OBSERVED STATE

Collect evidence before forming causal hypotheses.

Preferred evidence sources:

```text
stack trace
structured logs
request traces
metrics
runtime state
database state
queue state
tool output
test output
source code
configuration
dependency metadata
recent diff
deployment history
```

Preserve:

```yaml
observation:
  timestamp:
  source:
  value:
  context:
  trace_id:
  interpretation:
```

`interpretation` must remain separate from `value`.

---

## 11. Evidence Table

Canonical format:

| Time | Source | Observation                | Interpretation                      | Confidence |
| ---- | ------ | -------------------------- | ----------------------------------- | ---------- |
| t1   | log    | `foo_id=null`              | unexpected null at boundary         | HIGH       |
| t1   | stack  | serializer line 42         | failure occurs during serialization | HIGH       |
| t2   | source | no normalization in path B | possible missing invariant          | MEDIUM     |

Evidence must describe what was observed.

Interpretations are hypotheses or derived conclusions and must not be presented as
raw facts.

---

## 12. Evidence Hierarchy

When sources disagree, prefer direct runtime evidence over assumption.

Recommended order:

```text
1. current runtime observation
2. deterministic test result
3. current source/configuration
4. trace/log correlation
5. deployment/version metadata
6. recent history
7. documentation
8. memory
9. intuition
```

This ordering can be adjusted for a specific debugging domain when a stronger
source exists.

---

## 13. Evidence Quality

Classify evidence:

```text
DIRECT
DERIVED
INDIRECT
HISTORICAL
UNVERIFIED
```

Examples:

```text
DIRECT:
stack trace points to function X

DERIVED:
latency increased after dependency initialization

INDIRECT:
symptom resembles a known failure

HISTORICAL:
same error occurred six months ago

UNVERIFIED:
operator suspects cache corruption
```

Only direct or strongly corroborated derived evidence should establish a root cause.

---

## 14. Phase 05 — BOUNDARY LOCALIZATION

Map the failure across execution boundaries.

Typical chain:

```text
INPUT
 ↓
VALIDATION
 ↓
TRANSFORMATION
 ↓
BUSINESS LOGIC
 ↓
PERSISTENCE
 ↓
EXTERNAL SERVICE
 ↓
ASYNC/QUEUE
 ↓
RESPONSE
```

For each boundary ask:

```text
entered?
exited?
expected value?
actual value?
state changed?
error introduced?
```

The objective is to identify the **first incorrect state**, not merely the last
place where the system crashed.

---

## 15. First Incorrect State

Prefer:

```text
first divergence
```

over:

```text
last exception
```

Example:

```text
HTTP 500
 ↓
serializer exception
 ↓
missing object field
 ↓
object already malformed before serializer
 ↓
normalization branch omitted field
```

The serializer is the failure location.

The normalization boundary is the likely causal boundary.

---
