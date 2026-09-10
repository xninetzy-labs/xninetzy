# Life Management — Planning and Reconciliation

This reference expands current-time awareness, capacity, daily planning, commitment reconciliation, overdue handling, blockers, and event-based thinking. Read it when planning a day, reconciling commitments, or handling overdue work.

## Capacity awareness

Planning should account for realistic capacity. Distinguish:

**available time**

from:

**available energy**

A technically difficult task may require high focus. A routine task may be suitable for lower-energy periods. Do not automatically maximize the number of tasks scheduled.

## Daily planning

A daily plan should combine:

```text
today
+
active goals
+
due tasks
+
scheduled reminders
+
known constraints
+
available capacity
```

Prioritize:

1. urgent commitments,
2. important goal-supporting actions,
3. blocked items that can be unblocked,
4. maintenance routines,
5. optional tasks.

Avoid filling the entire day with optimistic assumptions.

## Commitment reconciliation

Before creating today's plan, reconcile:

```text
planned tasks
vs
scheduled tasks
vs
overdue tasks
vs
completed tasks
vs
active goals
```

Identify stale or conflicting commitments. Possible outcomes:

```text
keep
reschedule
split
defer
cancel
clarify
```

Do not silently delete commitments because they became inconvenient.

## Overdue work

Overdue does not automatically mean failed. An overdue item should be reviewed for:

* still relevant,
* deadline changed,
* blocked,
* should be rescheduled,
* should be cancelled,
* should be decomposed.

Do not endlessly carry obsolete tasks forward.

## Blockers

Track blockers explicitly. Useful blocker types:

* missing information,
* time constraint,
* dependency,
* technical issue,
* decision required,
* low capacity,
* external dependency.

A blocked task should not be treated as ignored or failed.

## Completion recording

Completion should use the canonical state-changing mechanism. When marking a task complete:

1. verify the task identity,
2. update the canonical record,
3. allow associated progress/reducer events to execute,
4. verify the resulting state.

Do not directly fabricate a progress number from conversation.

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

## Event-based thinking

Important state changes should conceptually generate events:

```text
Task completed
      ↓
Goal progress event
      ↓
Review signal
      ↓
Next-focus adaptation
```

The Life OS should prefer canonical event/reducer paths over ad hoc modifications.

## Goal progress

Do not manufacture goal progress percentages. Progress should come from:

* completed linked tasks,
* verified milestones,
* evidence,
* explicit goal metrics,
* canonical progress calculations.

A user completing one task does not automatically mean a goal is `50% complete.`

## Avoiding overplanning

Do not create a large system because the user asked:

> "What should I do today?"

Return a focused plan based on current state. Prefer:

**3 important actions**

over:

**27 perfectly categorized tasks.**

The system should reduce cognitive load, not create more management work.

## Review evidence

Use evidence to judge progress. Examples:

```text
Completed task:
PR merged

Goal:
Ship portfolio backend

Evidence:
Merged PR + passing CI
```

This is stronger than:

> "I worked on the backend for three hours."

Time can be useful context, but it is not mastery or goal progress by itself.