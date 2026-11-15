# define-goal — §30–36

Contents: 30. Phase 04 — MEASURE; 31. Validator Contract; 32. Evidence Freshness; 33. Goal Completion Evidence; 34. Phase 05 — BOUND; 35. Blast Radius; 36. Goal Preconditions

## 30. Phase 04 — MEASURE

Convert vague success into observable validators.

For each criterion define:

```yaml
criterion:
  criterion_id:
  description:
  validator:
  threshold:
  evidence_required:
  blocking:
```

Example:

```yaml
criterion:
  criterion_id: C1
  description: "All authentication integration tests pass."
  validator: "repo_test(auth-integration)"
  threshold: "100% required tests pass"
  evidence_required: "test_result"
  blocking: true
```

---

## 31. Validator Contract

A validator should answer:

```text
PASS
FAIL
UNKNOWN
```

Optionally:

```text
PARTIAL
```

for inherently partial outcomes.

The validator must define what it measures.

Do not use:

```text
"looks good"
"seems finished"
"probably works"
```

as formal validators.

---

## 32. Evidence Freshness

Evidence can become stale.

Examples:

```text
test result from old commit
quota from previous session
benchmark from previous environment
deployment state from previous release
```

Each evidence record should include:

```yaml
evidence:
  source:
  observed_at:
  target:
  environment:
  version:
  freshness:
```

Goal completion may require fresh evidence.

---

## 33. Goal Completion Evidence

A goal is completed only when:

```text
all blocking acceptance criteria pass
+
required evidence exists
+
evidence belongs to the intended target
+
evidence is sufficiently fresh
+
no unresolved material scope drift exists
```

---

## 34. Phase 05 — BOUND

Bind the goal to operational dimensions:

```text
target
scope
environment
time
resources
tools
ownership
blast radius
```

Example:

```yaml
bounds:
  repository: project-x
  environment: staging
  files:
    - apps/api/**
  max_changed_files: 15
  allowed_tools:
    - repo_search
    - repo_test
```

Only include a bound when it is meaningful.

---

## 35. Blast Radius

For engineering goals, optionally define:

```text
maximum affected services
maximum files changed
maximum data affected
allowed environments
allowed API surface
```

A goal should not silently authorize work outside its intended blast radius.

---

## 36. Goal Preconditions

Before accepting the goal:

```yaml
preconditions:
  - condition:
    status:
```

Possible:

```text
SATISFIED
UNSATISFIED
UNKNOWN
```

A critical unsatisfied precondition should block execution planning.

---
