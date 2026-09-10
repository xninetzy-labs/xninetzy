# Life Management — Reviews and Output

This reference expands daily review, weekly review, weekly adaptation, completion contract, standard output formats, and operating rules. Read it when generating the closing report of a Life OS interaction.

## Daily review

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

## Weekly review

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

## Weekly adaptation

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

## Standard daily planning output

```text
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

## Standard task completion output

```text
Task
Previous State
New State
Evidence
Goal Connection
Idempotency Status
Next Review
```

## Standard weekly review output

```text
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

## Completion contract

Every mutation or meaningful management interaction should return the relevant subset of:

**State inspected** — what existing records were checked.

**Exact state change** — what was created, modified, completed, scheduled, or logged.

**Goal connection** — which active goal it supports, if explicitly connected.

**Evidence** — what proves the change or completion.

**Idempotency status** — created, reused, already applied, updated, or safely ignored.

**Approval status** — when a consequential action requires confirmation.

**Next review point** — when or under what condition the item should be revisited.

If the underlying fact is unknown: **State: unverified**. Never fill the gap with an invented record.

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

The canonical lifecycle is:

**Inspect → Classify → Reconcile → Prioritize → Act → Record → Verify → Review → Adapt**