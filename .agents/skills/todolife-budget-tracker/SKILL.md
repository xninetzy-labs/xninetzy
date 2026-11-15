---
name: todolife-budget-tracker
description: Read-only tracker of daily food spending against the Rp20.000/day ceiling. Use for 'berapa hari ini', 'food budget' or the end-of-day review.
metadata:
  keywords: activates asks during mutates never note track user when
---

# todolife-budget-tracker

## Inputs

- Today's daily note (Meals section).
- Optional: prior 7-day notes for weekly trend.

## Output

```yaml
date: YYYY-MM-DD
spent_rp: <int>
budget_rp: 20000
remaining_rp: <int>
status: OK | ALERT | OVER
meals:
  - name: Breakfast | Lunch | Dinner | Snack
    amount_rp: <int>
    inside_budget: true | false
weekly_trend:
  - { date: ..., spent_rp: ... }
  ...
over_budget_streak_days: <int>
```

Trigger `Food Budget Alert` when `status: ALERT | OVER`. The daily planner must surface this in the daily note.

## Rules

- Budget ceiling is **hard**: Rp20.000/day. If owner has explicit monthly budget override, use that ceiling.
- Three meals baseline. Snack optional, counts toward budget.
- Never recommend skipping meals or extreme restriction. Weight 57→65kg is long-term; nutrition adequacy wins over budget pressure.
- If overspend, propose concrete swap (e.g. `gofood vs masak sendiri`) — never `kurangi makan`.

## Forbidden

- ❌ Edit meals list
- ❌ Lower budget silently
- ❌ Recommend starvation / calorie cut
- ❌ Mark `OK` when `OVER`

## Related

- `todolife-daily-planner` — writes the Meals section
- `money_add_transaction` (xninetzy MCP) — owner logs actuals there
