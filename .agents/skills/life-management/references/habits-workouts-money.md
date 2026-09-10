# Life Management — Habits, Workouts, and Money

This reference expands habit records and evidence, workout management and logging, and money integrity. Read it when handling repeated behaviors, physical activity, or financial entries.

## Habit management

A habit should represent a recurring behavior, not a one-time task. Useful fields:

```text
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

## Habit evidence

Only log habit completion when there is actual evidence. Valid evidence may be:

* explicit user report,
* canonical tracking event,
* verified automation signal.

Do not infer: `The user intended to exercise, therefore exercise happened.`

Keep:

**planned habit**

separate from:

**completed habit**.

## Workout management

Workout records should contain only facts actually supplied or verified. Possible fields:

```text
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

Do not invent duration, weights, repetitions, calories, distance, intensity, or completion. If the user says: `I trained legs today.` — record only what is known.

## Workout planning vs logging

Separate:

### Planned workout

> Run for 30 minutes tomorrow.

### Completed workout

> Ran for 30 minutes today.

The planned workout must not be written as completed activity.

## Money management

Money logs must be based on explicit facts. Possible fields:

```text
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

Do not infer amounts, currencies, categories, or transaction dates. When the user gives an ambiguous amount: `Spent 50.` — do not assume the currency unless established by canonical context.

## Financial integrity

Financial records are higher-integrity data. Never fabricate:

* transaction amount,
* currency,
* transaction date,
* merchant,
* category,
* account,
* balance.

When correcting a financial record, preserve the original auditability where the system supports it.

## Daily check-in

A check-in should capture actual state, not create fictional metrics. Possible dimensions:

* energy,
* focus,
* stress,
* mood,
* priorities,
* obstacles,
* reflection.

Only record values explicitly provided by the user or generated through a supported check-in mechanism.