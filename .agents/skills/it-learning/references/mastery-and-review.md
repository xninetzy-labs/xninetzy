# IT Learning — Mastery, Review, and Progress

This reference expands mastery thresholds, feedback loops, spaced review, review system, time/energy awareness, standard session record, and progress review format. Read it when assessing mastery or scheduling review.

## Mastery evidence threshold

Do not upgrade mastery solely because the learner answers one question correctly. Prefer multiple evidence points:

```text
Recall
+
Application
+
Independent attempt
+
Transfer/debugging
```

For important concepts, require evidence across at least two different modes.

Example for SQL joins:

1. explain INNER vs LEFT JOIN,
2. write correct queries,
3. debug a wrong join,
4. choose a join strategy for a real schema.

## Confidence tracking

Track confidence and correctness separately:

```text
high confidence + incorrect   → probable misconception
low confidence + correct     → strengthen retrieval confidence
high confidence + correct    → candidate for transfer practice
```

This helps detect the dangerous state of confident misunderstanding.

## Spaced review

Schedule review based on demonstrated performance.

A concept that is weak, recently corrected, or repeatedly forgotten should return sooner. A concept that is independently solved, successfully recalled later, or transferable can be reviewed less frequently. Do not use an arbitrary fixed interval for every concept.

## Review modes

Review may use:

* free recall,
* flash-style questions,
* explain-from-memory,
* code reconstruction,
* debugging,
* comparison,
* mini-project,
* retrieval from a concept graph.

Rotate formats where useful to test robust knowledge.

## Forgetting and relearning

A previously mastered concept may become rusty. Do not automatically reset mastery to zero. Distinguish:

```text
mastered but rusty
```

from:

```text
never mastered
```

Use the shortest review intervention capable of restoring performance.

## Error memory

Previous errors should influence future teaching.

Example:

```text
Previous error:
Confused authorization with authentication

Future intervention:
Contrast both concepts before introducing OAuth roles
```

Do not repeatedly teach the entire topic if the actual weakness is narrow.

## Review system

Review should inspect:

* mastered concepts,
* weak concepts,
* failed recall,
* recurring errors,
* unfinished evidence,
* prerequisite blockers,
* motivation/energy constraints,
* roadmap progress.

The review should produce a decision: continue / reinforce / revisit prerequisite / change practice type / advance.

## Adaptive decision rules

After every meaningful attempt:

### Correct and easy

Increase difficulty or introduce transfer.

### Correct with heavy guidance

Reduce scaffolding and repeat independently.

### Incorrect with correct concept

Target the procedural mistake.

### Incorrect due to misconception

Repair the mental model.

### Incorrect due to prerequisite gap

Switch to the prerequisite.

### Correct but uncertain

Use another recall or application task.

## Standard session record

Each completed session should contain:

```text
Target:
Roadmap:
Concept:
Objective:
Duration:
Energy:
Task:
Evidence:
Result:
Confidence:
Mastery:
Errors:
Reflection:
Next Action:
Review Date:
Recall Due:
```

Do not fabricate fields that were not actually observed.

## Progress review format

A review should answer:

### What improved?

Specific demonstrated capabilities.

### What remains weak?

Concepts with weak evidence.

### What was blocked?

Prerequisites, environment, time, or understanding.

### What should change?

Practice type, resource, scope, or sequence.

### What comes next?

One bounded next action.

## Completion contract

Every learning interaction that advances the learning state should end with:

**Target and stage** — what the learner is currently trying to achieve.

**Evidence/source status** — what evidence exists and which sources support the plan.

**One bounded next action** — the smallest meaningful next step.

**Success criterion** — what observable result counts as completion.

**Next review or recall checkpoint** — when or under what condition the learner should revisit the concept.

If evidence is missing, state explicitly: **Evidence status: insufficient**. Never imply mastery without supporting evidence.

## Default output structure

For a planning request:

```text
Target
Current State
Prerequisites
Roadmap
Next Session
Evidence Required
Success Criterion
Review Checkpoint
```

For a study session:

```text
Objective
Brief Context
Practice Task
Evidence to Produce
Success Criterion
Recall
Reflection
Next Focus
```

For a progress review:

```text
Demonstrated Progress
Weak Concepts
Evidence Gaps
Prerequisite Issues
Mastery Assessment
Adaptation
Next Action
Review / Recall
```