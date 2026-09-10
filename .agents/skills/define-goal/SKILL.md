---
name: define-goal
description: Goal-definition system for turning intentions, requests, projects, learning objectives, and operational needs into concrete, measurable, verifiable outcomes. Use when the user asks to define, create, refine, or validate a goal and its success criteria.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "detect -> inspect -> formulate -> quantify -> bound -> validate -> reconcile -> create/refine"
---

# Define Goal OS

This skill defines **what success should look like before work begins**. Its purpose is to transform an intention into an objective that an agent or human can pursue without guessing what "done" means.

The core principle is **outcome > activity**. The system should prefer a concrete result + measurable evidence + bounded scope + explicit stop condition over vague intentions such as "work on X."

The lifecycle is:

**Detect → Inspect → Formulate → Quantify → Bound → Validate → Reconcile → Create/Refine**

## When to use

* the user explicitly asks to define or create a goal;
* the user asks to set an objective or invoke the goal tool;
* the user asks to turn an intention into a measurable target;
* the user asks what "done" should mean;
* success criteria must be set before significant work begins.

## When NOT to use

* ordinary implementation requests where the user simply wants the work performed;
* goals with no actionable structure (capture instead);
* execution or planning — route to `xninetzy-assignment-orchestrator`, `it-learning`, or `life-management` after the goal is set.

## Goal anatomy

A strong goal answers:

* **Outcome** — what concrete state exists when work is complete.
* **Artifact or target** — what system, file, repository, environment, dataset, document, behavior, or decision is affected.
* **Evidence** — what observable evidence proves the outcome exists.
* **Success threshold** — what binary or quantitative condition defines success.
* **Scope** — what is included.
* **Boundary** — what is explicitly excluded.
* **Stop condition** — what should cause the agent to stop and ask.

Canonical structure:

```text
Goal
 ├── Outcome
 ├── Target
 ├── Evidence
 ├── Success Criterion
 ├── Scope
 ├── Out of Scope
 ├── Constraints
 ├── Deadline
 └── Stop Condition
```

## Core workflow

1. **Detect.** Determine whether the user is asking for a goal, a task, or a capture. Convert vague activity verbs (study, improve, work on, learn, prepare) into an outcome-first framing before creating the goal.
2. **Inspect.** Before creating a new goal, inspect the current goal state and reuse, refine, or surface a conflict rather than silently producing a duplicate.
3. **Formulate.** State the outcome, target, evidence, success criterion, scope, out-of-scope, constraints, deadline, and stop condition.
4. **Quantify.** Use numbers when they represent meaningful success: test pass rate, latency, accuracy, sample size, migration rate, deliverable counts, validatory thresholds. Add artificial precision only when a measurement is real.
5. **Bound.** Define the affected files, repository, environment, module, dataset, project phase, deadline, allowed tools, target platform, and maximum blast radius.
6. **Validate.** Apply the quality tests (concrete outcome, evidence, threshold, scope, reproducibility, stop). Repair before creation when a critical test fails.
7. **Reconcile.** Surface conflict with the active goal rather than silently replacing it.
8. **Create or refine.** Create a single concise objective string, or refine an existing goal when scope, deadline, evidence, or target materially changes.

## Goal quality bar

Before a goal is created or accepted, verify it answers:

* What concrete thing will be true?
* How will completion be verified?
* What defines success?
* What is the scope?
* What should stop the work?

A goal that cannot answer these questions must be refined before execution.

## Clarification rule

Ask one concise clarification question only when a reasonable interpretation could lead to a materially different outcome. Prefer questions about validator, target, environment, scope, deadline, or acceptance threshold. Do not ask for information that can be safely inferred from existing context.

## Goal vs plan, task, learning objective

* **Goal** — defines what success is.
* **Plan** — defines how to reach success.
* **Task** — an action with a finite completion condition.
* **Learning objective** — describes competence, not exposure.

Do not collapse a goal into a checklist or a task list. Do not turn this skill into a long execution plan; another skill handles planning.

## Active goal states

```text
none
active
completed
paused
blocked
conflicting
```

Reuse an active goal when it still matches the user's intent; surface conflict when a new objective materially differs.

## Routing

* Complex assignment work → `xninetzy-assignment-orchestrator`.
* Learning capability → `it-learning` and `xninetzy-learning-coach`.
* Personal commitments → `life-management`.
* Research → `xninetzy-deep-research`.
* Cross-session continuity → `xninetzy-memory`.

## Reference map

* `references/anatomy.md` — outcome-first framing, evidence hierarchy, binary validation, and goal patterns by domain.
* `references/lifecycle.md` — full state machine, conflict handling, refinement, completion contract, and quality tests.

## Operating rules

* define outcomes rather than activities;
* prefer measurable evidence over confidence;
* bound scope and define stop conditions up front;
* make consequential assumptions explicit;
* ask only when ambiguity materially changes the outcome;
* inspect active goal state before creating a duplicate;
* never silently replace a conflicting active goal;
* separate goal definition from execution planning;
* never claim completion without the defined evidence.

The purpose is simple:

> **Before doing the work, make "done" precise enough that both the agent and the user can recognize it without guessing.**