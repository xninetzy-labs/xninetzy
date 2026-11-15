---
name: todolife-schedule-auditor
description: Read-only audit of a daily or weekly schedule for conflicts, overlaps, impossible windows and priority violations. Use for 'cek jadwal', 'validasi plan', 'ada bentrok?' or before the daily planner writes.
metadata:
  keywords: activates asks mutates never obsidian pass todolife user validation when
---

# todolife-schedule-auditor

Pure validation. No mutations.

## Inputs

- Daily plan (Obsidian note at `Daily/YYYY/YYYY-MM-DD.md`) or a candidate schedule.
- College schedule source for current semester.
- Prayer times for the date.
- Sleep window.

## Audit checks

### Structural

- All time blocks must be `HH:MM` and `HH:MM` on the same date.
- No two non-prayer blocks may overlap.
- Sleep window (default 23:00–04:00) must not contain any non-sleep block.
- Class blocks must match college schedule byte-for-byte (start, end, location).
- Travel buffer ≥ 15 minutes between class end and next block if location changes.

### Priority

- P0 (class, prayer, sleep, fixed) cannot be overridden.
- P1 (math, ML, college task, exercise) cannot be removed to make room for P2/P3/P4.
- P4 (optional) blocks must come after P1 slots are full.

### Quota

- Math slot total = 2h.
- ML slot total = 2h.
- College task slot total = 2h.
- Exercise slot total = 1h.
- Food estimate ≤ Rp20.000.

### Realism

- Total scheduled hours ≤ 24h.
- Sum of fixed + core + project + meals + travel + buffer ≤ 18h awake window.
- No block of "ML + Project" counted in both ML quota and project quota (no double-count).

## Output

```yaml
verdict: PASS | PASS_WITH_WARNINGS | FAIL
conflicts:
  - block_a: HH:MM-HH:MM label
    block_b: HH:MM-HH:MM label
    overlap_minutes: <int>
warnings:
  - kind: buffer_short | travel_missing | budget_overshoot
    block: HH:MM-HH:MM label
    detail: <text>
overload:
  detected: true | false
  deficit_hours: <float>
```

If `verdict: FAIL`, the upstream planner must resolve before persisting. If `PASS_WITH_WARNINGS`, planner may persist but must include warnings in the note.

## Forbidden

- ❌ Mutate the plan being audited
- ❌ Silently rewrite blocks
- ❌ Mark conflicts as `OK` to force pass

## Related

- `todolife-daily-planner` — calls this as its validation pass
- `xninetzy-obsidian-orchestra` — vault-level structural audits (different scope)
