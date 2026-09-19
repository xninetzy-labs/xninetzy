---

...

...
name: "life-management"
description: "Personal operating system for goals, tasks, reminders, habits, routines, workouts, finances, check-ins, inbox capture, daily planning, and weekly reviews. Use when the user asks to capture a commitment, manage a goal or task, set a reminder, log a habit or workout, record a transaction, perform a check-in, or run a daily/weekly review."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "inspect -> classify -> reconcile -> prioritize -> act -> record -> verify -> review -> adapt"
...

# Life Management OS

This skill provides a reusable operating system for managing personal commitments and routines without confusing **plans, actions, and outcomes**.

It should help answer:

* What matters today?
* What have I committed to?
* What needs to happen next?
* What did I actually do?
* Which goals are moving forward?
* What should change based on evidence?

The core lifecycle is:

**Inspect → Classify → Reconcile → Prioritize → Act → Record → Verify → Review → Adapt**

## Core principles

* **Persisted state is the source of truth.** Use persisted records for goals, tasks, reminders, habits, workouts, money logs, check-ins, review history, and commitments. Do not reconstruct the user's state from conversational assumptions when a canonical record exists.
* **Separate intention from reality.** A task being planned does not mean it was completed. A reminder being created does not mean the action happened. A workout plan does not mean the workout occurred. A financial intention does not mean a transaction took place.

## When to use

* capturing a goal, task, reminder, habit, workout, money entry, or check-in;
* reconciling the day's commitments and overdue work;
* running a daily or weekly review;
* adapting the next focus based on evidence.

## When NOT to use

* academic-portal-specific workflows — use `xninetzy-cyber-campus` or `hebat-academic`;
* learning-specific mastery and recall — use `it-learning` and `xninetzy-learning-coach`;
* generic chat with no commitment intent — no skill needed.

## Request classification

Classify incoming requests into one primary domain:

* **Goal** — desired long-term outcome.
* **Task** — concrete action with a finite completion condition.
* **Reminder** — prompt to perform a specific action at a defined time.
* **Habit** — repeated behavior tracked over time.
* **Workout** — planned or completed physical activity record.
* **Money** — financial transaction, budget item, or money-related record.
* **Check-in** — current state, mood, energy, reflection, or daily status.
* **Review** — analysis of accumulated activity and adaptation.
* **Inbox** — an intention or commitment that is not yet clear enough to formalize.

Use the narrowest useful classification.

## Core workflow

1. **Inspect.** Before creating or modifying a commitment, inspect the relevant state: today's date/time, active goals, due reminders, relevant task list, and existing matching records. Do not create a duplicate simply because the same intent appears again.
2. **Classify.** Map the request to the narrowest domain above. If the user's intention is not yet precise enough, route to **Inbox** rather than inventing a precise commitment.
3. **Reconcile.** Before planning, surface conflicting or stale commitments. Possible outcomes: keep, reschedule, split, defer, cancel, clarify.
4. **Prioritize.** Combine today's date, active goals, due tasks, scheduled reminders, known constraints, and available capacity. Avoid filling the entire day with optimistic assumptions.
5. **Act.** Execute the smallest meaningful next action. Use canonical completion paths rather than ad hoc modifications.
6. **Record.** Use the canonical state-changing mechanism. Mark tasks complete through the canonical completion event so associated progress reducers and review signals can fire.
7. **Verify.** Compare the resulting persisted state against the intended change. Never claim completion without observing the canonical state change.
8. **Review.** Compare intention → action → evidence → outcome → obstacle → adaptation. Produce a decision, not merely a statistic.
9. **Adapt.** Continue, reinforce, reschedule, reduce scope, change route, repair prerequisite, revise goal, archive, or stop.

## Goal integration

Connect tasks to goals only when the relationship is explicit.

Example:

```text
Goal:
Complete backend portfolio project

Task:
Implement authentication middleware

Relation:
Task contributes directly to goal
```

Do not attach unrelated tasks to goals merely to make the system appear more organized.

## Task and reminder rules

A good task should be **concrete**, **bounded**, **observable**, and **time-aware**:

* Concrete: `Write integration tests for the login endpoint.`
* Bounded: `Update only the authentication module and its tests.`
* Observable: `The test command passes.`
* Time-aware: `Complete during today's study session.`

Avoid vague tasks like `Work on backend.` Convert vague intentions into the smallest meaningful next action.

A reminder requires action + unambiguous time. When the requested time has already elapsed, ask for clarification before scheduling. Do not silently choose a replacement time for consequential reminders.

A reminder should usually reference an actionable commitment rather than becoming an independent duplicate commitment.

## Inbox capture

Use inbox capture when the user's intention is not yet precise enough to become a reliable commitment:

> "I should probably clean up my portfolio sometime."

Store as an inbox item rather than inventing `Clean portfolio tomorrow at 18:00.` The inbox can later be refined into a goal, task, reminder, project, habit, or discarded idea.

## Idempotency

Every mutation should be safe to replay. Before applying:

```text
requested change
      ↓
existing state
      ↓
already applied?
 ┌──────────────┴──────────────┐
yes                            no
 ↓                              ↓
reuse/confirm                 apply
```

This is especially important for reminders, task creation, habit logs, money entries, and completion events.

## Personalization without fabrication

Use established preferences and constraints when they are already persisted and relevant. Do not invent preferred schedules, financial limits, workout targets, habit frequencies, priorities, or deadlines. When no reliable state exists, ask only for information that materially changes the action.

## Routing

* Goal framing → `define-goal`.
* Academic status → `xninetzy-cyber-campus` or `hebat-academic`.
* Learning → `it-learning`.
* Cross-session continuity → `xninetzy-memory`.
* OS inbox and triage → `xninetzy-os`.

## Reference map

* `references/state-and-classification.md` — persisted state hierarchy, request classification, goal/task/reminder/habit/workout/money/check-in rules, and inbox capture.
* `references/planning-and-reconciliation.md` — current-time awareness, capacity, daily planning, commitment reconciliation, overdue handling, blockers, and event-based thinking.
* `references/habits-workouts-money.md` — habit and workout records, money integrity, financial records, and completion recording.
* `references/reviews-and-output.md` — daily and weekly review format, completion integrity, standard output formats, and operating rules.

## Operating rules

The system must:

* inspect persisted state before mutating it,
* classify the request correctly,
* preserve the distinction between intention and completion,
* make the next action concrete and bounded,
* schedule reminders only from explicit actions and unambiguous times,
* record habits, workouts, and money only from verified facts,
* connect tasks to goals only when the relationship is explicit,
* use canonical completion events,
* make mutations safe to replay,
* avoid duplicate commitments,
* surface blockers and stale commitments,
* review actual evidence before adapting plans,
* never fabricate personal activity, financial data, dates, amounts, or progress.

The purpose of Life OS is not to make the user manage more data. It is to make the user's **actual commitments, actions, evidence, and next decisions visible enough to act on reliably.**