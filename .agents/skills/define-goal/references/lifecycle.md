# Define Goal — Lifecycle, Conflict, and Completion

This reference expands the goal state machine, refinement rules, quality tests, and completion contract. Read it when handling conflict, reconciling active goals, or auditing completion.

## Goal state model

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

## Goal creation rules

Before `create_goal`:

1. confirm goal creation is actually needed;
2. inspect active goal state;
3. formulate the outcome;
4. identify evidence;
5. quantify where meaningful;
6. bound scope;
7. define the stop condition;
8. resolve material ambiguity.

Create **one concise objective string**. Avoid embedding a full roadmap, decision log, snapshot, or execution ledger inside the goal.

## Goal tool boundary

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

## Goal quality tests

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

## Standard goal object

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

Only persist fields supported by the available goal system. Do not fabricate fields that the tool does not support.

## Standard goal creation format

A concise goal should resemble:

> **[Outcome] for [target] by [constraint/deadline], verified by [evidence/validator], with [scope boundary], stopping to ask if [material ambiguity/blocker].**

Example:

> Reduce checkout API p95 latency below 250 ms for the documented slow path by making the smallest safe server-side change, verified by `npm run test:checkout` and the existing local benchmark across three consecutive runs, limited to the checkout service and its tests, and stop if achieving the target requires changing shared infrastructure.

## Completion contract

When goal definition is complete, return:

**Goal** — the final objective.

**Target / Scope** — what the goal applies to and what is bounded.

**Evidence** — how completion will be verified.

**Success Criterion** — the exact threshold or binary condition.

**Goal State** — created, reused, refined, blocked, or not created.

**Next Action** — one clear next action when applicable.

If the goal cannot yet be validated, say explicitly:

> **Goal status: requires clarification**

Do not pretend that an underspecified intention is a valid measurable goal.

## Operating rules

The system must:

* define outcomes rather than activities;
* prefer measurable evidence;
* use binary validators when meaningful metrics do not exist;
* bound scope;
* make consequential assumptions explicit;
* ask only when ambiguity materially changes the outcome;
* inspect active goal state before creating a duplicate;
* never silently replace a conflicting active goal;
* separate goal definition from execution planning;
* never claim completion without the defined evidence.

The canonical lifecycle is:

**Detect → Inspect → Formulate → Quantify → Bound → Validate → Reconcile → Create/Refine**