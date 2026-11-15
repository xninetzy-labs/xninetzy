# define-goal — §58–66

Contents: 58. Learning Objective Variant; 59. Research Goal Variant; 60. Engineering Goal Variant; 61. Operational Goal Variant; 62. Decision Goal Variant; 63. Consequential Goals; 64. Safety Boundary; 65. Assumption Escalation; 66. Clarification Rule

## 58. Learning Objective Variant

For learning goals, outcome must describe demonstrated capability.

Weak:

```text
"Study React."
```

Strong:

```text
"Build and explain a React feature that uses state, controlled forms, and async
data loading, validated through the defined exercise."
```

Evidence may include:

```text
working artifact
assessment result
oral explanation
code review
problem-solving performance
```

Exposure time alone is usually not enough evidence of competence.

---

## 59. Research Goal Variant

Research goals should distinguish:

```text
question
population/data
method
evidence standard
deliverable
uncertainty boundary
```

Example:

```yaml
research_goal:
  question:
  evidence_required:
  population:
  method:
  deliverable:
  uncertainty_boundary:
```

Do not define research success as:

```text
"find evidence supporting hypothesis X"
```

when the evidence may disconfirm it.

Prefer:

```text
"determine whether the evidence supports, weakens, or fails to resolve X under
the predefined method."
```

---

## 60. Engineering Goal Variant

For software goals, prefer:

```text
target repository
target component
behavioral outcome
validator
environment
regression requirement
scope boundary
```

Example:

```text
Outcome:
The authentication endpoint returns the intended response for all defined
valid and invalid credential scenarios.

Evidence:
integration test suite.

Threshold:
100% required scenarios pass.

Scope:
POST /auth/login in staging.

Out of scope:
UI redesign.
```

---

## 61. Operational Goal Variant

For operational work:

```text
desired system state
affected environment
metric
threshold
observation window
rollback/stop condition
```

Do not define a goal solely as:

```text
"monitor the service"
```

Prefer:

```text
"Maintain the service below the defined error-rate threshold for the observation
window, with alerting verified."
```

---

## 62. Decision Goal Variant

For decisions, success is not "pick an option."

Instead define:

```text
decision question
decision deadline
criteria
available evidence
constraints
required decision artifact
```

Example:

```text
Goal:
Produce a documented architecture decision for the selected service boundary,
using the predefined criteria and evidence set.
```

The decision itself may remain uncertain.

---

## 63. Consequential Goals

For goals affecting:

```text
production
financial state
academic state
security posture
privacy
external users
irreversible data
```

require stronger:

```text
scope binding
validator
evidence
approval
stop conditions
```

The goal definition skill does not itself grant permission to perform the action.

Authorization belongs to the relevant execution/policy layer.

---

## 64. Safety Boundary

Goal definition must never implicitly create authority.

This:

```text
Goal:
Submit KRS with selected courses.
```

does not imply:

```text
permission to submit
```

Similarly:

```text
Goal:
Deploy to production.
```

does not imply:

```text
production deployment authorization
```

The goal expresses desired outcome, not execution authority.

---

## 65. Assumption Escalation

If a hidden assumption could materially change the goal:

```text
assumption
→ uncertainty
→ validation question
```

Ask one concise question only when the ambiguity can materially change:

```text
outcome
target
validator
scope
deadline
authority
```

Do not ask for information that can be safely inferred.

---

## 66. Clarification Rule

Use a clarification question when:

```text
interpretation A → materially different outcome
interpretation B → materially different outcome
```

Do not ask when:

```text
multiple phrasings
minor formatting
non-material implementation preference
information already present in context
```

Preferred question shape:

```text
"What should count as success: A or B?"
```

Avoid:

```text
"Can you provide more details?"
```

---
