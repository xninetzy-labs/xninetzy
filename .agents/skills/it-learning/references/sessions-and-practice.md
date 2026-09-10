# IT Learning — Sessions, Practice, and Evidence

This reference expands daily/session planning, the study session lifecycle, active learning priority, active recall, practice design, project-based learning, and evidence types. Read it when designing a session or selecting evidence.

## Daily / session planning

Each study session should have:

### Objective

One clearly bounded capability.

### Context

Why the task matters in the roadmap.

### Work

Specific actions to perform.

### Evidence

What should exist at the end.

### Success criterion

What counts as "done correctly."

### Recall

What should be recalled after practice.

### Reflection

What remains uncertain.

Avoid sessions that contain too many unrelated objectives.

## Study session lifecycle

Use:

```text
planned
  ↓
started
  ↓
active practice
  ↓
evidence produced
  ↓
completed
  ↓
mastery assessed
  ↓
review scheduled
```

A study session is incomplete when the learner only consumes material without producing evidence.

## Active learning priority

Prefer this approximate order:

**Recall → Attempt → Feedback → Correction → Explanation → Re-attempt**

over:

**Read → Highlight → Watch → Read Again**

Use passive material as support, not as the primary proof of learning.

## Active recall

Use due recall before rereading whenever practical. Recall should test:

* definitions,
* relationships,
* procedures,
* trade-offs,
* debugging logic,
* architecture decisions,
* examples,
* counterexamples.

Do not only ask "What is X?" Also ask:

* When would you use X instead of Y?
* What breaks if this assumption is false?
* How would you debug this?
* What trade-off does this design introduce?

## Practice design

Practice should progress from:

**guided → partial → independent → unfamiliar**

A learner should eventually encounter tasks where the solution is not directly demonstrated. For programming, progressively move from:

```text
follow example
→ modify example
→ implement from specification
→ debug broken implementation
→ design solution independently
```

## Project-based learning

Projects should be broken into incremental milestones. For technical projects, inspect:

* architecture,
* modules,
* dependencies,
* data flow,
* APIs/interfaces,
* persistence,
* error handling,
* testing,
* deployment,
* observability,
* security where relevant.

Do not treat "build an app" as one task. Use:

```text
Project
 ↓
Architecture
 ↓
Modules
 ↓
Milestones
 ↓
Implementation
 ↓
Tests
 ↓
Integration
 ↓
Deployment
 ↓
Evaluation
```

## Evidence types

Evidence may include:

### Conceptual evidence

* explanation,
* diagram,
* comparison,
* worked example.

### Practical evidence

* code,
* SQL,
* notebook,
* API,
* Docker image/configuration,
* deployment,
* dashboard,
* model,
* agent workflow.

### Performance evidence

* problem-solving result,
* debugging result,
* test result,
* design review,
* timed recall.

### Project evidence

* milestone completion,
* repository state,
* architecture decision record,
* tests,
* demo.

Evidence should be specific enough that another person could inspect it.

## Feedback loop

After every meaningful practice cycle:

```text
Attempt
→ Evaluate
→ Identify error
→ Correct
→ Re-attempt
```

Do not move forward simply because the learner finished the assigned material.

## Misconception handling

When an answer is wrong, distinguish:

* factual gap,
* conceptual misunderstanding,
* procedural error,
* syntax error,
* careless mistake,
* prerequisite gap,
* interpretation error.

Do not merely provide the correct answer. The learner should understand **why the reasoning failed**. When useful, create a targeted contrast:

```text
Incorrect mental model
        ↓
Why it fails
        ↓
Correct model
        ↓
Minimal example
        ↓
Re-attempt
```

## Learning through projects

When the learner is building something:

```text
Project Need
 ↓
Relevant Concept
 ↓
Minimal Explanation
 ↓
Immediate Implementation
 ↓
Test
 ↓
Debug
 ↓
Reflect
```

Project work should become learning evidence when it actually demonstrates understanding.

## Project evidence

Strong evidence includes:

* implemented feature,
* passing test,
* debugged defect,
* architecture explanation,
* documented trade-off,
* reproducible command,
* working prototype,
* successful deployment.

Do not treat a copied tutorial implementation as strong evidence of independent mastery.

## Academic integration

When learning is driven by an academic requirement:

```text
Assignment Requirement
 ↓
Required Competence
 ↓
Prerequisites
 ↓
Diagnostic
 ↓
Learning Session
 ↓
Evidence
 ↓
Assignment Output
```

The assignment artifact and learning mastery should remain separate states.