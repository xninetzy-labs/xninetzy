# Define Goal OS

```yaml
---
name: define-goal
description: General-purpose goal-definition system for turning vague intentions, requests, projects, learning objectives, research questions, technical work, academic tasks, and operational needs into concrete, measurable, verifiable outcomes with explicit scope, evidence, success criteria, and stop conditions. Supports goal creation, refinement, validation, conflict detection, and goal-state reuse without managing long-running execution artifacts.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "detect -> inspect -> formulate -> quantify -> bound -> validate -> reconcile -> create/refine"
---
```

# Define Goal OS

This skill defines **what success should look like before work begins**.

Its purpose is to transform an intention into an objective that an agent or human can pursue without guessing what "done" means.

The core principle is:

**Outcome > activity**

The system should prefer:

> **A concrete result + measurable evidence + bounded scope + explicit stop condition**

over:

> "Work on X."

The lifecycle is:

**Detect → Inspect → Formulate → Quantify → Bound → Validate → Reconcile → Create/Refine**

---

# 1. When to Use This Skill

Use this skill when the user:

* explicitly asks to define or create a goal,
* asks to set an objective,
* invokes the goal tool,
* asks to turn an intention into a measurable target,
* asks what "done" should mean,
* needs success criteria before beginning work.

Do **not** force goal creation for ordinary implementation requests when the user simply wants the work performed.

---

# 2. Goal Anatomy

A strong goal should answer:

### Outcome

What concrete state should exist when the work is complete?

### Artifact or Target

What system, file, repository, project, environment, dataset, document, behavior, or decision is affected?

### Evidence

What observable evidence proves the outcome exists?

### Success Threshold

What binary or quantitative condition defines success?

### Scope

What is included?

### Boundary

What is explicitly excluded when ambiguity could expand the work?

### Stop Condition

What should cause the agent to stop and ask rather than continue guessing?

---

# 3. Canonical Goal Structure

Represent the goal conceptually as:

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

Not every goal needs every field, but every important ambiguity should be resolved somewhere in the objective.

---

# 4. Outcome-First Rule

A goal should describe a **state that becomes true**, not merely an activity that takes place.

Weak:

> Research PostgreSQL.

Better:

> Produce a comparison of PostgreSQL indexing strategies that recommends one strategy for the current query workload, supported by official documentation and benchmark evidence.

Weak:

> Work on the dashboard.

Better:

> Deliver the dashboard's three required views with working filters and verified data against the specified dataset.

Weak:

> Study Docker.

Better:

> Containerize the backend so a clean environment can start the service with one documented command and pass the project's integration test suite.

---

# 5. Activity-to-Outcome Conversion

Convert activity verbs such as:

* study,
* investigate,
* improve,
* work on,
* research,
* fix,
* optimize,
* review,
* learn,
* prepare,

into observable outcomes.

Pattern:

```text
Activity
   ↓
Desired state
   ↓
Verification method
   ↓
Acceptance threshold
```

Example:

```text
"Improve API"
      ↓
"Reduce checkout latency"
      ↓
"Run existing benchmark"
      ↓
"p95 < 250 ms for 3 consecutive runs"
```

---

# 6. Quantification

Use numbers when they represent meaningful success.

Useful dimensions include:

### Testing

* exact test command,
* number of passing tests,
* required CI jobs,
* zero failures,
* acceptance-test result.

### Performance

* latency,
* throughput,
* memory,
* CPU,
* bundle size,
* execution time,
* number of consecutive runs.

### Quality

* accuracy,
* precision,
* recall,
* coverage,
* error rate,
* defect count,
* reviewed examples.

### Migration / Data

* records migrated,
* records verified,
* reconciliation rate,
* zero unresolved critical errors.

### Research

* number/type of authoritative sources,
* benchmark cases,
* competing alternatives evaluated,
* decision criteria satisfied.

### Deliverables

* exact files,
* expected directories,
* required sections,
* output format,
* required links.

Do not add artificial precision merely to make a goal look measurable.

---

# 7. Binary Validation

When reliable quantitative measurement is unavailable, prefer an honest binary validator.

Examples:

> Build succeeds from a clean environment.

> The required test suite passes.

> The document contains all required sections.

> The prototype link opens successfully.

> The migration produces zero reconciliation errors.

> The design satisfies all explicitly stated acceptance criteria.

A binary validator is better than a fabricated metric.

---

# 8. Evidence Hierarchy

Prefer evidence in this order:

1. automated validator,
2. reproducible command/result,
3. observable artifact,
4. independent comparison,
5. manual review,
6. self-reported confidence.

Confidence alone should never be treated as proof of completion for consequential goals.

---

# 9. Goal Quality Bar

Before a goal is created or accepted, verify that it answers:

**What concrete thing will be true?**

**How will completion be verified?**

**What defines success?**

**What is the scope?**

**What should stop the work?**

A goal that cannot answer these questions should be refined before execution.

---

# 10. Scope Control

Goals should be bounded enough to prevent uncontrolled expansion.

Useful bounds include:

* affected files,
* repository,
* environment,
* module,
* dataset,
* project phase,
* deadline,
* number of examples,
* allowed tools,
* target platform,
* maximum blast radius.

Example:

> Update only the authentication module and its tests.

This is preferable to:

> Fix the authentication system.

when unrelated refactoring is not intended.

---

# 11. Out-of-Scope Definition

Use explicit exclusions only when they prevent likely scope drift.

Example:

```text
In scope:
- API validation
- authentication middleware
- affected tests

Out of scope:
- UI redesign
- database migration
- unrelated dependency upgrades
```

Do not add unnecessary exclusions to simple goals.

---

# 12. Stop Conditions

A good goal defines when the agent should **stop and ask**.

Typical stop conditions:

* required information is missing,
* success criteria conflict,
* the target environment is unclear,
* the proposed change exceeds scope,
* a destructive operation becomes necessary,
* the existing state contradicts assumptions,
* evidence cannot be reproduced,
* the user must choose between materially different outcomes.

The goal is not to keep working indefinitely.

---

# 13. Clarification Rule

Ask one concise clarification question only when a reasonable interpretation could lead to a materially different outcome.

Prefer questions about:

* validator,
* target,
* environment,
* scope,
* deadline,
* acceptance threshold.

Examples:

> Which metric should define success here: latency, cost, or user-visible behavior?

> Should this be verified locally, in staging, or in production?

> What evidence is sufficient for you to consider the goal complete?

Do not ask for information that can be safely inferred from existing context.

---

# 14. Assumption Handling

When an assumption is safe and low-impact:

1. state it internally,
2. use it consistently,
3. do not fabricate evidence.

When an assumption could materially change the result:

**stop and clarify.**

---

# 15. Active Goal State

Before creating a new goal, inspect the current goal state.

Possible states:

```text
none
active
completed
paused
blocked
conflicting
```

If there is no active goal and the proposed objective passes the quality bar:

**create the goal.**

If an active goal still matches the user's intent:

**reuse it rather than creating a duplicate.**

If the active goal conflicts materially with the new request:

**surface the conflict.**

---

# 16. Goal Conflict Handling

When a new objective conflicts with the active goal:

```text
Active Goal
    ↓
Compare target / scope / outcome
    ↓
Compatible?
 ┌───────────┴───────────┐
Yes                       No
 ↓                         ↓
Reuse              Surface conflict
                         ↓
          finish / complete / separate goal
```

Do not silently replace an active goal.

---

# 17. Goal Refinement

A goal may be refined when:

* the validator is too vague,
* the outcome is activity-based,
* scope has expanded,
* the deadline changes,
* the target changes,
* the evidence is insufficient,
* the original goal is technically impossible.

Preserve the original intent whenever possible.

Do not refine a goal merely for stylistic reasons.

---

# 18. Goal vs Plan

Keep these separate.

### Goal

Defines **what success is**.

### Plan

Defines **how to reach success**.

Example:

**Goal**

> Reduce API p95 latency below 250 ms and verify it with the existing benchmark across three consecutive runs.

**Plan**

> Profile the endpoint, inspect database queries, optimize the slow path, rerun tests, then benchmark.

Do not turn this skill into a long execution plan unless another skill explicitly handles planning.

---

# 19. Goal vs Task

A task is an action.

A goal is an outcome.

Example:

```text
Task:
Run benchmark.

Goal:
Reduce p95 latency below 250 ms.
```

A goal may contain several tasks, but the goal should not be reduced to a checklist of actions.

---

# 20. Goal vs Learning Objective

For learning:

Weak:

> Learn Docker.

Strong:

> Demonstrate independent ability to containerize the target backend, explain the Dockerfile decisions, start it from a clean environment, and pass the integration tests.

The learning goal must define **competence**, not exposure.

---

# 21. Technical Goal Patterns

### Bug fixing

Use:

**reproduce → fix → regression validator**

Example:

> Reproduce the checkout failure, apply the smallest safe fix, and verify that the original failing test passes without introducing failures in the targeted test suite.

### Testing

Define:

* exact tests,
* expected result,
* coverage or case count when meaningful.

### Performance

Define:

* metric,
* threshold,
* workload,
* environment,
* measurement method,
* number of valid runs.

### Refactoring

Define:

* behavioral preservation,
* affected scope,
* test evidence,
* acceptable change boundary.

### Deployment

Define:

* target environment,
* healthy state,
* verification command,
* rollback condition.

---

# 22. Research Goal Patterns

A research goal should produce a decision, explanation, or validated conclusion.

Weak:

> Research vector databases.

Strong:

> Compare three candidate vector-storage approaches for the current RAG workload and recommend one based on retrieval quality, operational complexity, and measured query latency, using official documentation plus reproducible benchmark results.

A research goal should specify:

* decision/question,
* evidence standard,
* relevant alternatives,
* scope,
* completion condition.

---

# 23. Academic Goal Patterns

For academic assignments, goals should describe the required deliverable and its validation.

Example:

> Produce a submission-ready report that satisfies every explicit requirement in the current assignment brief, uses the required structure and formatting, includes evidence-backed analysis and references, and passes final content and visual QA.

When the assignment has a rubric, use rubric criteria as part of the validator.

Do not invent grading requirements not present in the course materials.

---

# 24. Project Goal Patterns

Project goals should define the milestone outcome.

Example:

> Deliver the authentication milestone with login, token validation, protected routes, and automated tests covering the required success and failure cases.

Avoid:

> Work on authentication.

---

# 25. Quantification Rules by Domain

## Software Engineering

Prefer:

* test pass rate,
* build status,
* defect count,
* latency,
* coverage,
* benchmark results,
* API response behavior.

## Data Analytics

Prefer:

* dataset completeness,
* defined KPI correctness,
* validation checks,
* model/dashboard acceptance criteria.

## Machine Learning

Prefer:

* target metric,
* evaluation split,
* benchmark baseline,
* error threshold,
* reproducibility condition.

## Infrastructure / Operations

Prefer:

* uptime,
* health checks,
* deployment result,
* resource thresholds,
* rollback trigger.

## Learning

Prefer:

* correct recall,
* successful implementation,
* independent solution,
* transfer task,
* artifact evidence.

## Academic Work

Prefer:

* explicit rubric requirements,
* required sections,
* required artifacts,
* citation/reference requirements,
* verified submission-ready format.

---

# 26. Deadline-Aware Goals

When a deadline exists, include it when it materially constrains execution.

Example:

> Complete the required report by August 28, 2026, with all mandated sections, references, and final PDF QA completed before submission.

Do not confuse the deadline with the success criterion.

**Deadline = when**

**Success criterion = what**

---

# 27. Blast Radius

For technical changes, define the maximum acceptable impact when relevant.

Example:

> Modify only the checkout service and its tests; do not alter shared authentication or database schemas.

This reduces accidental expansion.

---

# 28. Evidence Reproducibility

A strong validator should ideally be reproducible.

Prefer:

```text
command
+
expected result
+
environment
```

Example:

> Run `npm run test:checkout`; all checkout tests must pass.

For performance:

> Run the existing benchmark three times under the documented local workload; all runs must show p95 below 250 ms.

---

# 29. Completion Integrity

Never mark a goal complete because:

* the work "looks done,"
* the agent feels confident,
* the user asked to stop without evidence,
* a partial artifact exists,
* an unverified command was assumed to succeed.

Completion requires the defined evidence.

If evidence is incomplete:

**status = incomplete / unverified**

not successful.

---

# 30. Goal State Model

Use a simple lifecycle:

```text
draft
  ↓
validated
  ↓
active
  ↓
completed
```

Alternative states:

```text
blocked
paused
cancelled
superseded
```

A goal should only move to **completed** when its success criteria are satisfied.

---

# 31. Goal Creation Rules

Before `create_goal`:

1. confirm goal creation is actually needed,
2. inspect active goal state,
3. formulate the outcome,
4. identify evidence,
5. quantify where meaningful,
6. bound scope,
7. define the stop condition,
8. resolve material ambiguity.

Create **one concise objective string**.

Avoid embedding a full roadmap, decision log, snapshot, or execution ledger inside the goal.

---

# 32. Goal Tool Boundary

This skill is responsible for:

* defining goals,
* refining goals,
* validating success criteria,
* reconciling goal state,
* creating/updating the goal when supported.

It is **not** responsible for:

* long-running execution state,
* durable progress snapshots,
* decision logs,
* task ledgers,
* project management databases,
* resume artifacts,
* detailed execution plans.

Those belong to other specialized systems.

---

# 33. Goal Quality Tests

Before accepting a goal, apply these tests.

### Concrete outcome test

Can someone state what will be true afterward?

### Evidence test

Can someone inspect evidence proving it?

### Threshold test

Is success binary or quantitatively defined?

### Scope test

Is the target bounded enough to avoid unnecessary work?

### Reproducibility test

Can the validator be run or inspected again?

### Stop test

Is there a clear reason to stop and ask?

A goal that fails a critical test should be repaired before creation.

---

# 34. Standard Goal Object

Conceptually:

```text
{
  objective,
  target,
  outcome,
  evidence,
  success_criteria,
  scope,
  out_of_scope,
  constraints,
  deadline,
  stop_condition,
  status
}
```

Only persist fields supported by the available goal system.

Do not fabricate fields that the tool does not support.

---

# 35. Standard Goal Creation Format

A concise goal should resemble:

> **[Outcome] for [target] by [constraint/deadline], verified by [evidence/validator], with [scope boundary], stopping to ask if [material ambiguity/blocker].**

Example:

> Reduce checkout API p95 latency below 250 ms for the documented slow path by making the smallest safe server-side change, verified by `npm run test:checkout` and the existing local benchmark across three consecutive runs, limited to the checkout service and its tests, and stop if achieving the target requires changing shared infrastructure.

---

# 36. Completion Contract

When goal definition is complete, return:

**Goal**
The final objective.

**Target / Scope**
What the goal applies to and what is bounded.

**Evidence**
How completion will be verified.

**Success Criterion**
The exact threshold or binary condition.

**Goal State**
Created, reused, refined, blocked, or not created.

**Next Action**
One clear next action when applicable.

If the goal cannot yet be validated, say explicitly:

> **Goal status: requires clarification**

Do not pretend that an underspecified intention is a valid measurable goal.

---

# 37. Operating Rules

The system must:

**define outcomes rather than activities,**

**prefer measurable evidence,**

**use binary validators when meaningful metrics do not exist,**

**bound scope,**

**make consequential assumptions explicit,**

**ask only when ambiguity materially changes the outcome,**

**inspect active goal state before creating a duplicate,**

**never silently replace a conflicting active goal,**

**separate goal definition from execution planning,**

**never claim completion without the defined evidence.**

The canonical lifecycle is:

**Detect → Inspect → Formulate → Quantify → Bound → Validate → Reconcile → Create/Refine**

The purpose of the skill is simple:

> **Before doing the work, make "done" precise enough that both the agent and the user can recognize it without guessing.**
