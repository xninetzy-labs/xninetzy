# debugging — §22–28

Contents: 22. Phase 08 — CONTROLLED TEST; 23. Controlled-Test Contract; 24. Falsification; 25. Negative Evidence; 26. Phase 09 — ROOT CAUSE; 27. Primary Root Cause vs Contributing Factors; 28. Root-Cause Quality Gate

## 22. Phase 08 — CONTROLLED TEST

The controlled test must distinguish hypotheses.

A good test changes one meaningful variable while preserving the rest.

Conceptually:

```text
CONTROL
vs
EXPERIMENT
```

Examples:

```text
concurrency 1 vs 8
cache enabled vs disabled
dependency version A vs B
feature flag off vs on
normalized input vs raw input
transaction enabled vs disabled
```

The test must have a predicted outcome for each relevant hypothesis.

---

## 23. Controlled-Test Contract

```yaml
controlled_test:
  test_id:
  hypothesis_ids: []
  control:
  experiment:
  changed_variable:
  held_constant: []
  predicted_results: []
  command_or_procedure:
  observed_results: []
  conclusion:
```

Avoid changing multiple unrelated variables at once.

---

## 24. Falsification

After the controlled test:

```text
SUPPORTED
```

when predicted evidence appears.

```text
FALSIFIED
```

when a prediction is contradicted by reliable evidence.

```text
WEAKENED
```

when evidence becomes less consistent with the hypothesis but does not fully
exclude it.

The system must update the hypothesis matrix after each controlled test.

---

## 25. Negative Evidence

Negative evidence matters.

Examples:

```text
database is healthy
→ weakens database-corruption hypothesis

failure persists with cache disabled
→ weakens cache hypothesis

single-thread execution still fails
→ weakens race hypothesis

same binary fails only with production config
→ strengthens configuration hypothesis
```

Do not record only evidence that supports the preferred explanation.

---

## 26. Phase 09 — ROOT CAUSE

A root cause is established only when:

```text
1. the relevant failure can be reproduced or sufficiently bounded
2. the causal path is identified
3. observed evidence matches the causal mechanism
4. competing hypotheses are sufficiently weakened or falsified
5. a controlled intervention changes the failure as predicted
```

Root cause statement:

```text
ROOT CAUSE:
[one precise causal sentence]
```

Example:

```text
ROOT CAUSE:
The request path bypasses shared input normalization, allowing a null identifier
to reach the serializer and trigger the observed exception.
```

---

## 27. Primary Root Cause vs Contributing Factors

Use:

```yaml
root_cause:
  primary:
  contributing_factors: []
  triggering_condition:
  failure_mechanism:
```

Do not force unrelated failures into one root cause.

A single incident may contain:

```text
primary root cause
+
contributing factors
+
environmental trigger
```

The primary root cause should explain the causal path that produced the observed
failure.

---

## 28. Root-Cause Quality Gate

Reject a root-cause statement when it is merely:

```text
the stack trace location
the exception class
the symptom restated
a generic label
a guess
a component name
```

Bad:

```text
"Database issue."
```

Bad:

```text
"NullPointerException."
```

Good:

```text
"The background worker reads the job payload before the producer's transaction
commit is visible, so the worker receives an incomplete record."
```

---
