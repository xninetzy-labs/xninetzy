# Define Goal — Outcome Anatomy

This reference expands the goal structure, evidence hierarchy, quantification rules, and goal patterns by domain. Read it when designing a concrete goal.

## Outcome-first rule

A goal should describe a **state that becomes true**, not merely an activity that takes place.

Weak: `Research PostgreSQL.`

Better: `Produce a comparison of PostgreSQL indexing strategies that recommends one strategy for the current query workload, supported by official documentation and benchmark evidence.`

Weak: `Work on the dashboard.`

Better: `Deliver the dashboard's three required views with working filters and verified data against the specified dataset.`

Weak: `Study Docker.`

Better: `Containerize the backend so a clean environment can start the service with one documented command and pass the project's integration test suite.`

## Activity-to-outcome conversion

Convert activity verbs such as study, investigate, improve, work on, research, fix, optimize, review, learn, prepare into observable outcomes:

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

## Quantification

Use numbers when they represent meaningful success. Useful dimensions:

* **Testing** — exact test command, number of passing tests, required CI jobs, zero failures, acceptance-test result.
* **Performance** — latency, throughput, memory, CPU, bundle size, execution time, number of consecutive runs.
* **Quality** — accuracy, precision, recall, coverage, error rate, defect count, reviewed examples.
* **Migration / Data** — records migrated, records verified, reconciliation rate, zero unresolved critical errors.
* **Research** — number/type of authoritative sources, benchmark cases, competing alternatives evaluated, decision criteria satisfied.
* **Deliverables** — exact files, expected directories, required sections, output format, required links.

Do not add artificial precision merely to make a goal look measurable.

## Binary validation

When reliable quantitative measurement is unavailable, prefer an honest binary validator:

> Build succeeds from a clean environment.

> The required test suite passes.

> The document contains all required sections.

> The prototype link opens successfully.

> The migration produces zero reconciliation errors.

> The design satisfies all explicitly stated acceptance criteria.

A binary validator is better than a fabricated metric.

## Evidence hierarchy

Prefer evidence in this order:

1. automated validator,
2. reproducible command/result,
3. observable artifact,
4. independent comparison,
5. manual review,
6. self-reported confidence.

Confidence alone should never be treated as proof of completion for consequential goals.

## Scope control

Goals should be bounded enough to prevent uncontrolled expansion:

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

Example: `Update only the authentication module and its tests.` This is preferable to `Fix the authentication system.` when unrelated refactoring is not intended.

## Out-of-scope definition

Use explicit exclusions only when they prevent likely scope drift:

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

## Stop conditions

A good goal defines when the agent should **stop and ask**:

* required information is missing,
* success criteria conflict,
* the target environment is unclear,
* the proposed change exceeds scope,
* a destructive operation becomes necessary,
* the existing state contradicts assumptions,
* evidence cannot be reproduced,
* the user must choose between materially different outcomes.

The goal is not to keep working indefinitely.

## Clarification rule

Ask one concise clarification question only when a reasonable interpretation could lead to a materially different outcome. Prefer questions about validator, target, environment, scope, deadline, or acceptance threshold. Do not ask for information that can be safely inferred from existing context.

## Assumption handling

When an assumption is safe and low-impact:

1. state it internally,
2. use it consistently,
3. do not fabricate evidence.

When an assumption could materially change the result, **stop and clarify.**

## Active goal state

Before creating a new goal, inspect the current goal state:

```text
none
active
completed
paused
blocked
conflicting
```

If there is no active goal and the proposed objective passes the quality bar, create the goal. If an active goal still matches the user's intent, reuse it rather than creating a duplicate. If the active goal conflicts materially with the new request, surface the conflict.

## Goal conflict handling

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

## Goal refinement

A goal may be refined when:

* the validator is too vague,
* the outcome is activity-based,
* scope has expanded,
* the deadline changes,
* the target changes,
* the evidence is insufficient,
* the original goal is technically impossible.

Preserve the original intent whenever possible. Do not refine a goal merely for stylistic reasons.

## Goal vs plan, task, learning objective

### Goal

Defines **what success is**.

### Plan

Defines **how to reach success**.

Example:

**Goal**: Reduce API p95 latency below 250 ms and verify it with the existing benchmark across three consecutive runs.

**Plan**: Profile the endpoint, inspect database queries, optimize the slow path, rerun tests, then benchmark.

Do not turn this skill into a long execution plan unless another skill explicitly handles planning.

### Task

A task is an action. A goal is an outcome.

```text
Task: Run benchmark.

Goal: Reduce p95 latency below 250 ms.
```

A goal may contain several tasks, but the goal should not be reduced to a checklist of actions.

### Learning objective

For learning:

Weak: `Learn Docker.`

Strong: `Demonstrate independent ability to containerize the target backend, explain the Dockerfile decisions, start it from a clean environment, and pass the integration tests.`

The learning goal must define **competence**, not exposure.

## Technical goal patterns

### Bug fixing

Use `reproduce → fix → regression validator`. Example:

> Reproduce the checkout failure, apply the smallest safe fix, and verify that the original failing test passes without introducing failures in the targeted test suite.

### Testing

Define exact tests, expected result, coverage or case count when meaningful.

### Performance

Define metric, threshold, workload, environment, measurement method, number of valid runs.

### Refactoring

Define behavioral preservation, affected scope, test evidence, acceptable change boundary.

### Deployment

Define target environment, healthy state, verification command, rollback condition.

## Research goal patterns

A research goal should produce a decision, explanation, or validated conclusion.

Weak: `Research vector databases.`

Strong: `Compare three candidate vector-storage approaches for the current RAG workload and recommend one based on retrieval quality, operational complexity, and measured query latency, using official documentation plus reproducible benchmark results.`

A research goal should specify decision/question, evidence standard, relevant alternatives, scope, and completion condition.

## Academic goal patterns

For academic assignments, goals should describe the required deliverable and its validation.

Example: `Produce a submission-ready report that satisfies every explicit requirement in the current assignment brief, uses the required structure and formatting, includes evidence-backed analysis and references, and passes final content and visual QA.`

When the assignment has a rubric, use rubric criteria as part of the validator. Do not invent grading requirements not present in the course materials.

## Project goal patterns

Project goals should define the milestone outcome.

Example: `Deliver the authentication milestone with login, token validation, protected routes, and automated tests covering the required success and failure cases.`

Avoid vague goals like `Work on authentication.`

## Quantification rules by domain

* **Software Engineering** — test pass rate, build status, defect count, latency, coverage, benchmark results, API response behavior.
* **Data Analytics** — dataset completeness, defined KPI correctness, validation checks, model/dashboard acceptance criteria.
* **Machine Learning** — target metric, evaluation split, benchmark baseline, error threshold, reproducibility condition.
* **Infrastructure / Operations** — uptime, health checks, deployment result, resource thresholds, rollback trigger.
* **Learning** — correct recall, successful implementation, independent solution, transfer task, artifact evidence.
* **Academic Work** — explicit rubric requirements, required sections, required artifacts, citation/reference requirements, verified submission-ready format.

## Deadline-aware goals

When a deadline exists, include it when it materially constrains execution.

Example: `Complete the required report by August 28, 2026, with all mandated sections, references, and final PDF QA completed before submission.`

Do not confuse the deadline with the success criterion. Deadline = when. Success criterion = what.

## Blast radius

For technical changes, define the maximum acceptable impact when relevant.

Example: `Modify only the checkout service and its tests; do not alter shared authentication or database schemas.`

This reduces accidental expansion.

## Evidence reproducibility

A strong validator should ideally be reproducible. Prefer:

```text
command
+
expected result
+
environment
```

Example: `Run npm run test:checkout; all checkout tests must pass.`

For performance: `Run the existing benchmark three times under the documented local workload; all runs must show p95 below 250 ms.`

## Completion integrity

Never mark a goal complete because:

* the work "looks done";
* the agent feels confident;
* the user asked to stop without evidence;
* a partial artifact exists;
* an unverified command was assumed to succeed.

Completion requires the defined evidence. If evidence is incomplete, status is `incomplete / unverified`, not successful.