---
name: todolife-core-tracker
description: Read-only tracker of Daily Core quotas (Math 2h, ML 2h, College Task 2h, Exercise 1h) that surfaces deficits. Use for 'udah berapa jam math hari ini', 'core status' or the end-of-day review.
metadata:
  keywords: activates and asks modifies never plan surface track user when
---

# todolife-core-tracker

## Inputs

- Today's daily note at `Daily/YYYY/YYYY-MM-DD.md`.
- Optional: prior daily notes for streak math.

## Output

```yaml
date: YYYY-MM-DD
core_status: CORE_COMPLETE | CORE_PARTIAL | CORE_DEFICIT
quota:
  math: { planned: 2h, actual: Xh, gap: Yh }
  ml: { planned: 2h, actual: Xh, gap: Yh }
  college: { planned: 2h, actual: Xh, gap: Yh }
  exercise: { planned: 1h, actual: Xh, gap: Yh }
streaks:
  math_complete_days: <int>
  ml_complete_days: <int>
  college_complete_days: <int>
  exercise_complete_days: <int>
```

## How to compute actual

Read checkbox state from the daily note. Each completed checkbox = full block duration. Partial completion = user explicitly marks `[partial] Xh`.

If the note is missing or unreadable, output `core_status: UNKNOWN` and surface a `note_missing` warning.

## Forbidden

- ❌ Edit the daily note
- ❌ Inflate `actual` to match `planned`
- ❌ Mark CORE_COMPLETE if any quota < 100%

## Related

- `todolife-daily-planner` — writer; tracker is read-only
- `personal-os` — weekly review consumes tracker output
