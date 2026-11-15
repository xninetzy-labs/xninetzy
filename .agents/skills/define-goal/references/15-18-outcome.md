# define-goal — §15–18

Contents: 15. Outcome; 16. Target; 17. Evidence; 18. Evidence Hierarchy

## 15. Outcome

The outcome describes the desired future state.

Weak:

```text
"Work on the authentication system."
```

Strong:

```text
"Users with valid credentials can complete authentication and receive a valid
application session."
```

An outcome should describe **what is true**, not merely what someone does.

---

## 16. Target

Identify what the goal changes or evaluates.

Possible targets:

```text
repository
service
module
API
database
document
dataset
model
learning capability
project phase
environment
decision
workflow
personal commitment
```

Example:

```yaml
target:
  type: repository
  identifier: project-x
  environment: staging
```

Avoid vague targets such as:

```text
"the system"
"the project"
"everything"
```

unless the system/project is itself the intentionally bounded target.

---

## 17. Evidence

Evidence must answer:

```text
"What would we observe that proves the outcome exists?"
```

Evidence may be:

```text
test result
benchmark
measurement
artifact
diff
dataset statistic
deployment state
evaluation score
completed deliverable
verified system behavior
external authoritative record
```

Do not treat:

```text
"I believe it works"
```

as evidence.

---

## 18. Evidence Hierarchy

Prefer:

```text
DIRECT VERIFICATION
    >
REPRODUCIBLE MEASUREMENT
    >
DERIVED METRIC
    >
SUPPORTED OBSERVATION
    >
SELF-REPORT
    >
ASSUMPTION
```

The required evidence strength depends on consequence.

For consequential goals, prefer direct or reproducible verification.

---
