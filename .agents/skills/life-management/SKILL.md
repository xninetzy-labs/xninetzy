# Life Management OS

```yaml
---
name: life-management
description: General-purpose personal operating system for managing goals, tasks, reminders, habits, routines, workouts, finances, check-ins, commitments, inbox capture, daily planning, and weekly reviews. Uses persisted state as the source of truth, preserves attribution and idempotency, distinguishes intention from verified completion, connects actions to goals when explicitly related, and supports adaptive planning based on actual evidence.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "inspect -> classify -> reconcile -> prioritize -> act -> record -> verify -> review -> adapt"
---
```

# Life Management OS

This skill provides a reusable operating system for managing personal commitments and routines without confusing **plans, actions, and outcomes**.

It should help answer:

**What matters today?**
**What have I committed to?**
**What needs to happen next?**
**What did I actually do?**
**Which goals are moving forward?**
**What should change based on evidence?**

The core lifecycle is:

**Inspect → Classify → Reconcile → Prioritize → Act → Record → Verify → Review → Adapt**

---

# 1. Core Principles

## 1.1 Persisted state is the source of truth

Use persisted records for:

* goals,
* tasks,
* reminders,
* habits,
* workouts,
* money logs,
* check-ins,
* review history,
* commitments.

Do not reconstruct the user's state from conversational assumptions when a canonical record exists.

---

## 1.2 Separate intention from reality

Keep these states distinct:

```text
intended
planned
scheduled
started
completed
verified
cancelled
blocked
```

A task being planned does not mean it was completed.

A reminder being created does not mean the action happened.

A workout plan does not mean the workout occurred.

A financial intention does not mean a transaction took place.

---

# 2. State Inspection

Before creating or modifying a commitment, inspect the relevant state.

At minimum, check:

* today's date/time,
* active goals,
* due reminders,
* relevant task list,
* existing matching records.

Do not create a duplicate simply because the same intent appears again.

---

# 3. Current-Time Awareness

Use the actual current local date/time for time-sensitive operations.

Distinguish:

* today,
* tomorrow,
* overdue,
* scheduled,
* already elapsed.

For example, a reminder requested for "tonight" should be resolved against the current local time rather than assuming a generic evening.

When the requested time is ambiguous or already passed, ask for clarification before scheduling.

---

# 4. Request Classification

Classify incoming requests into one primary domain:

### Goal

Desired long-term outcome.

### Task

Concrete action with a finite completion condition.

### Reminder

Prompt to perform a specific action at a defined time.

### Habit

Repeated behavior tracked over time.

### Workout

Planned or completed physical activity record.

### Money

Financial transaction, budget item, or money-related record.

### Check-in

Current state, mood, energy, reflection, or daily status.

### Review

Analysis of accumulated activity and adaptation.

### Inbox

An intention or commitment that is not yet clear enough to formalize.

Use the narrowest useful classification.

---

# 5. Goal Integration

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

---

# 6. Goal Contribution

When a task is linked to a goal, the relationship should be meaningful.

Useful relationship states:

```text
supports
required_for
unblocks
maintains
reviews
```

Avoid generic links such as:

```text
related_to
maybe_helpful
```

unless the system specifically requires them.

---

# 7. Task Quality

A good task should be:

**Concrete**

> Write integration tests for the login endpoint.

**Bounded**

> Update only the authentication module and its tests.

**Observable**

> The test command passes.

**Time-aware**

> Complete during today's study session.

Avoid:

> Work on backend.

Convert vague intentions into the smallest meaningful next action.

---

# 8. Smallest Next Action

When a commitment is too broad, decompose it.

Example:

```text
"Prepare thesis"
        ↓
"Find the latest draft"
        ↓
"Review the introduction"
        ↓
"Rewrite the problem statement"
```

The system should prefer the smallest action that creates meaningful progress without unnecessary fragmentation.

---

# 9. Task Deduplication

Before creating a task:

1. search for an existing equivalent task,
2. compare target,
3. compare intended action,
4. compare timing,
5. determine whether the new request is actually a duplicate, update, or separate task.

When replaying an identical request:

**do not create a duplicate.**

---

# 10. Task States

Use explicit task states where supported:

```text
inbox
planned
scheduled
in_progress
completed
blocked
cancelled
deferred
```

Do not mark a task complete merely because the user discussed it.

---

# 11. Reminder Rules

A reminder requires:

**Action + unambiguous time**

Good:

> Remind me at 19:00 to submit the report.

Insufficient:

> Remind me later.

When the time is ambiguous:

> What time should I remind you?

When the requested time has already elapsed:

> The requested time has passed. What time should I use instead?

Do not silently choose a replacement time for consequential reminders.

---

# 12. Reminder vs Task

Keep them separate.

### Task

The commitment itself.

> Submit the report.

### Reminder

The prompt.

> Remind me at 19:00 to submit the report.

A reminder should usually reference an actionable commitment rather than becoming an independent duplicate commitment.

---

# 13. Habit Management

A habit should represent a recurring behavior, not a one-time task.

Useful fields include:

```text id="7xg2qm"
habit
frequency
target
tracking_period
completion_state
streak
notes
```

Examples:

> Read 20 minutes, 5 days per week.

> Practice SQL, Monday through Friday.

Do not create arbitrary streaks or targets without user-provided or previously established values.

---

# 14. Habit Evidence

Only log habit completion when there is actual evidence.

Valid evidence may be:

* explicit user report,
* canonical tracking event,
* verified automation signal.

Do not infer:

> The user intended to exercise, therefore exercise happened.

Keep:

**planned habit**

separate from:

**completed habit**.

---

# 15. Workout Management

Workout records should contain only facts actually supplied or verified.

Possible fields:

```text id="8o3q3w"
date
activity
duration
sets
repetitions
distance
load
intensity
notes
status
```

Do not invent:

* duration,
* weights,
* repetitions,
* calories,
* distance,
* intensity,
* completion.

If the user says:

> I trained legs today.

Record only what is known.

---

# 16. Workout Planning vs Logging

Separate:

### Planned workout

> Run for 30 minutes tomorrow.

from:

### Completed workout

> Ran for 30 minutes today.

The planned workout must not be written as completed activity.

---

# 17. Money Management

Money logs must be based on explicit facts.

Possible fields:

```text id="zc9wfg"
date
amount
currency
category
direction
account
description
status
```

Where:

* `direction = income | expense | transfer`

Do not infer amounts, currencies, categories, or transaction dates.

When the user gives an ambiguous amount:

> "Spent 50"

do not assume the currency unless established by canonical context.

---

# 18. Financial Integrity

Financial records are higher-integrity data.

Never fabricate:

* transaction amount,
* currency,
* transaction date,
* merchant,
* category,
* account,
* balance.

When correcting a financial record, preserve the original auditability where the system supports it.

---

# 19. Daily Check-In

A check-in should capture actual state, not create fictional metrics.

Possible dimensions:

* energy,
* focus,
* stress,
* mood,
* priorities,
* obstacles,
* reflection.

Only record values explicitly provided by the user or generated through a supported check-in mechanism.

---

# 20. Daily Planning

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

---

# 21. Capacity Awareness

Planning should account for realistic capacity.

Distinguish:

**available time**

from:

**available energy**

A technically difficult task may require high focus.

A routine task may be suitable for lower-energy periods.

Do not automatically maximize the number of tasks scheduled.

---

# 22. Commitment Reconciliation

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

Identify stale or conflicting commitments.

Possible outcomes:

```text
keep
reschedule
split
defer
cancel
clarify
```

Do not silently delete commitments because they became inconvenient.

---

# 23. Inbox Capture

Use inbox capture when the user's intention is not yet precise enough to become a reliable commitment.

Example:

> "I should probably clean up my portfolio sometime."

Store as an inbox item rather than inventing:

> "Clean portfolio tomorrow at 18:00."

The inbox can later be refined into:

* goal,
* task,
* reminder,
* project,
* habit,
* or discarded idea.

---

# 24. Completion Recording

Completion should use the canonical state-changing mechanism.

When marking a task complete:

1. verify the task identity,
2. update the canonical record,
3. allow associated progress/reducer events to execute,
4. verify the resulting state.

Do not directly fabricate a progress number from conversation.

---

# 25. Idempotency

Every mutation should be safe to replay.

Before applying a mutation:

```text id="0x9u2u"
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

This is especially important for:

* reminders,
* task creation,
* habit logs,
* money entries,
* completion events.

---

# 26. Event-Based Thinking

Important state changes should conceptually generate events:

```text id="7z68n3"
Task completed
      ↓
Goal progress event
      ↓
Review signal
      ↓
Next-focus adaptation
```

The Life OS should prefer canonical event/reducer paths over ad hoc modifications.

---

# 27. Goal Progress

Do not manufacture goal progress percentages.

Progress should come from:

* completed linked tasks,
* verified milestones,
* evidence,
* explicit goal metrics,
* canonical progress calculations.

A user completing one task does not automatically mean a goal is "50% complete."

---

# 28. Blockers

Track blockers explicitly.

Useful blocker types:

* missing information,
* time constraint,
* dependency,
* technical issue,
* decision required,
* low capacity,
* external dependency.

A blocked task should not be treated as ignored or failed.

---

# 29. Overdue Work

Overdue does not automatically mean failed.

An overdue item should be reviewed for:

* still relevant,
* deadline changed,
* blocked,
* should be rescheduled,
* should be cancelled,
* should be decomposed.

Do not endlessly carry obsolete tasks forward.

---

# 30. Daily Review

A daily review should compare:

```text
Intent
↓
Action
↓
Evidence
↓
Obstacle
↓
Outcome
↓
Next adaptation
```

Useful questions:

### What mattered today?

The highest-value commitments.

### What actually happened?

Verified completed actions.

### What blocked progress?

Specific obstacles.

### What should move?

One or more concrete adaptations.

---

# 31. Weekly Review

A weekly review should inspect:

* active goals,
* completed tasks,
* overdue tasks,
* recurring habits,
* workout records,
* money activity,
* check-ins,
* blockers,
* commitments,
* next week priorities.

The review should produce decisions, not merely statistics.

---

# 32. Weekly Adaptation

For each active goal, classify:

```text
on_track
needs_attention
blocked
stalled
completed
no_longer_relevant
```

Then choose the smallest appropriate adaptation:

* continue,
* increase practice,
* reduce scope,
* change next action,
* remove blocker,
* reschedule,
* revise goal,
* close goal.

---

# 33. Avoiding Overplanning

Do not create a large system because the user asked:

> "What should I do today?"

Return a focused plan based on current state.

Prefer:

**3 important actions**

over:

**27 perfectly categorized tasks.**

The system should reduce cognitive load, not create more management work.

---

# 34. Review Evidence

Use evidence to judge progress.

Examples:

```text id="u5n7yw"
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

---

# 35. Personalization Without Fabrication

Use established preferences and constraints when they are already persisted and relevant.

Do not invent:

* preferred schedules,
* financial limits,
* workout targets,
* habit frequencies,
* priorities,
* deadlines.

When no reliable state exists, ask only for information that materially changes the action.

---

# 36. Safety Boundaries

For sensitive personal records:

* minimize persisted data,
* avoid exposing unnecessary details,
* do not infer sensitive attributes,
* preserve user control over consequential changes,
* use explicit confirmation for high-impact mutations where required.

---

# 37. Standard Daily Planning Output

```text id="lj7wfr"
Today
Current State
Top Priorities
Due / Overdue
Goal Contributions
Constraints / Blockers
Smallest Next Actions
Scheduled Reminders
End-of-Day Review
```

Only include sections that materially help.

---

# 38. Standard Task Completion Output

```text id="n5y0wv"
Task
Previous State
New State
Evidence
Goal Connection
Idempotency Status
Next Review
```

---

# 39. Standard Weekly Review Output

```text id="rb2m9e"
Goals
Progress Evidence
Completed Commitments
Missed / Overdue
Habits
Workouts
Money Summary
Blockers
Key Lessons
Next Week Focus
Adaptation
```

Do not add unsupported numerical summaries.

---

# 40. Completion Contract

Every mutation or meaningful management interaction should return the relevant subset of:

**State inspected**
What existing records were checked.

**Exact state change**
What was created, modified, completed, scheduled, or logged.

**Goal connection**
Which active goal it supports, if explicitly connected.

**Evidence**
What proves the change or completion.

**Idempotency status**
Created, reused, already applied, updated, or safely ignored.

**Approval status**
When a consequential action requires confirmation.

**Next review point**
When or under what condition the item should be revisited.

If the underlying fact is unknown:

> **State: unverified**

Never fill the gap with an invented record.

---

# 41. Operating Rules

The system must:

**inspect persisted state before mutating it,**

**classify the request correctly,**

**preserve the distinction between intention and completion,**

**make the next action concrete and bounded,**

**schedule reminders only from explicit actions and unambiguous times,**

**record habits, workouts, and money only from verified facts,**

**connect tasks to goals only when the relationship is explicit,**

**use canonical completion events,**

**make mutations safe to replay,**

**avoid duplicate commitments,**

**surface blockers and stale commitments,**

**review actual evidence before adapting plans,**

**never fabricate personal activity, financial data, dates, amounts, or progress.**

The canonical lifecycle is:

**Inspect → Classify → Reconcile → Prioritize → Act → Record → Verify → Review → Adapt**

The purpose of Life OS is not to make the user manage more data.

It is to make the user's **actual commitments, actions, evidence, and next decisions visible enough to act on reliably**.
