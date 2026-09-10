# Life Management — State and Classification

This reference expands persisted state hierarchy, request classification, goal/task/reminder/habit/workout/money/check-in rules, and inbox capture. Read it when handling a fresh request that touches personal commitments.

## Persisted state is the source of truth

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

## Separate intention from reality

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

A task being planned does not mean it was completed. A reminder being created does not mean the action happened. A workout plan does not mean the workout occurred. A financial intention does not mean a transaction took place.

## State inspection

Before creating or modifying a commitment, inspect the relevant state. At minimum, check:

* today's date/time,
* active goals,
* due reminders,
* relevant task list,
* existing matching records.

Do not create a duplicate simply because the same intent appears again.

## Current-time awareness

Use the actual current local date/time for time-sensitive operations. Distinguish:

* today,
* tomorrow,
* overdue,
* scheduled,
* already elapsed.

For example, a reminder requested for "tonight" should be resolved against the current local time rather than assuming a generic evening. When the requested time is ambiguous or already passed, ask for clarification before scheduling.

## Request classification

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

## Goal integration

Connect tasks to goals only when the relationship is explicit. Example:

```text
Goal:
Complete backend portfolio project

Task:
Implement authentication middleware

Relation:
Task contributes directly to goal
```

Do not attach unrelated tasks to goals merely to make the system appear more organized.

## Goal contribution

When a task is linked to a goal, the relationship should be meaningful. Useful relationship states:

```text
supports
required_for
unblocks
maintains
reviews
```

Avoid generic links such as `related_to`, `maybe_helpful` unless the system specifically requires them.

## Task quality

A good task should be:

**Concrete** — `Write integration tests for the login endpoint.`

**Bounded** — `Update only the authentication module and its tests.`

**Observable** — `The test command passes.`

**Time-aware** — `Complete during today's study session.`

Avoid `Work on backend.` Convert vague intentions into the smallest meaningful next action.

## Smallest next action

When a commitment is too broad, decompose it:

```text
"Prepare thesis"
        ↓
"Find the latest draft"
        ↓
"Review the introduction"
        ↓
"Rewrite the problem statement"
```

Prefer the smallest action that creates meaningful progress without unnecessary fragmentation.

## Task deduplication

Before creating a task:

1. search for an existing equivalent task,
2. compare target,
3. compare intended action,
4. compare timing,
5. determine whether the new request is actually a duplicate, update, or separate task.

When replaying an identical request, do not create a duplicate.

## Task states

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

## Reminder rules

A reminder requires **action + unambiguous time**.

Good: `Remind me at 19:00 to submit the report.`

Insufficient: `Remind me later.`

When the time is ambiguous: `What time should I remind you?`

When the requested time has already elapsed: `The requested time has passed. What time should I use instead?`

Do not silently choose a replacement time for consequential reminders.

## Reminder vs task

Keep them separate.

### Task

The commitment itself: `Submit the report.`

### Reminder

The prompt: `Remind me at 19:00 to submit the report.`

A reminder should usually reference an actionable commitment rather than becoming an independent duplicate commitment.

## Inbox capture

Use inbox capture when the user's intention is not yet precise enough to become a reliable commitment:

> "I should probably clean up my portfolio sometime."

Store as an inbox item rather than inventing `Clean portfolio tomorrow at 18:00.`

The inbox can later be refined into a goal, task, reminder, project, habit, or discarded idea.

## Personalization without fabrication

Use established preferences and constraints when they are already persisted and relevant. Do not invent:

* preferred schedules,
* financial limits,
* workout targets,
* habit frequencies,
* priorities,
* deadlines.

When no reliable state exists, ask only for information that materially changes the action.

## Safety boundaries

For sensitive personal records:

* minimize persisted data,
* avoid exposing unnecessary details,
* do not infer sensitive attributes,
* preserve user control over consequential changes,
* use explicit confirmation for high-impact mutations where required.