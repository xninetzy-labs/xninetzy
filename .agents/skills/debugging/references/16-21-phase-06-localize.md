# debugging — §16–21

Contents: 16. Phase 06 — LOCALIZE; 17. Phase 07 — HYPOTHESIS GENERATION; 18. Hypothesis Contract; 19. Evidence-For / Evidence-Against Rule; 20. Hypothesis Ranking; 21. Bayesian Language Policy

## 16. Phase 06 — LOCALIZE

Produce a localization record:

```yaml
localization:
  component:
  file:
  symbol:
  line_or_range:
  boundary:
  first_incorrect_state:
  downstream_failure:
  evidence_refs: []
```

Use `repo_symbol` and `repo_search` to establish exact code ownership and call
paths.

Do not guess source locations from filenames alone.

---

## 17. Phase 07 — HYPOTHESIS GENERATION

Create multiple plausible hypotheses.

Recommended categories:

```text
LOGIC
STATE
INPUT
DATA
CONCURRENCY
TIMING
CACHE
DEPENDENCY
CONFIGURATION
ENVIRONMENT
NETWORK
DATABASE
API_CONTRACT
RESOURCE_EXHAUSTION
RACE
ORDERING
OBSERVABILITY
```

Do not limit hypotheses to the first plausible code defect.

---

## 18. Hypothesis Contract

Each hypothesis must contain:

```yaml
hypothesis:
  id:
  statement:
  category:

  supporting_evidence: []
  refuting_evidence: []

  predicted_observations: []
  falsification_test:

  confidence:
  status:
```

Allowed status:

```text
OPEN
SUPPORTED
WEAKENED
FALSIFIED
ESTABLISHED
```

---

## 19. Evidence-For / Evidence-Against Rule

Every meaningful hypothesis must state both:

```text
what would support it
```

and:

```text
what would refute it
```

Bad:

```text
"It looks like a race condition."
```

Good:

```text
Hypothesis:
shared mutable state is accessed concurrently.

Supports:
failures correlate with concurrency > 1.

Refutes:
same failure occurs with concurrency = 1.

Controlled test:
run identical workload at concurrency 1, 2, 4, 8.
```

---

## 20. Hypothesis Ranking

Rank by evidence, not intuition.

Recommended factors:

```text
direct evidence
causal proximity
reproduction coverage
explanatory power
number of assumptions
contradicting evidence
testability
```

Example:

```yaml
ranking:
  hypothesis_id:
  confidence: HIGH | MEDIUM | LOW
  rationale:
  strongest_evidence:
  strongest_refutation:
```

Do not use arbitrary numeric probability unless the system has a validated
probabilistic model.

---

## 21. Bayesian Language Policy

Avoid unsupported claims such as:

```text
"90% likely"
"almost certainly"
"99% race condition"
```

unless those values are produced by an actual validated model or measurement.

Prefer:

```text
HIGH confidence
MEDIUM confidence
LOW confidence
```

with explicit evidence.

---
