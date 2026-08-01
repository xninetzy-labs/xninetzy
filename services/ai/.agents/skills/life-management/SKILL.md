---
name: life-management
description: Manage the owner's goals, tasks, reminders, habits, workouts, money logs, daily check-ins, and weekly reviews. Use for planning today, capturing commitments, completing tasks, scheduling reminders, tracking routines, and reviewing whether daily actions advance active goals.
metadata:
  triggers: "goal task reminder habit workout money checkin review today commitment routine progress"
  lifecycle: "state-intent-smallest-action-execute-event-review"
  version: "1.1"
---

# Life OS management

Use persisted state rather than assumptions. Every mutation must be attributable to the owner and safe to replay.

## Workflow

1. Inspect `os_today`, active goals, due reminders, and the relevant list tool before creating a commitment.
2. Classify the request as goal, task, reminder, habit, workout, money, check-in, review, or inbox capture.
3. Connect a task to an existing goal only when the relationship is explicit.
4. Keep the next action concrete, bounded, observable, and time-aware.
5. Create reminders from an explicit action and unambiguous time; ask when the time is ambiguous or already elapsed.
6. Log habits, workouts, and transactions only from facts supplied by the owner.
7. Mark completion through the canonical tool so reducers and progress events run.
8. Use daily/weekly review to compare intent, action, evidence, obstacles, and the next adaptation.

Do not fabricate completion, amounts, exercise volume, habit performance, or dates. Do not duplicate tasks or reminders when replaying a request. Use inbox capture when the desired commitment is still unclear.

## Completion contract

Return the state inspected, exact state change, connection to a goal, idempotency or approval status, and next review point.
