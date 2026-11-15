---
name: todolife-daily-planner
description: 'Builds a conflict-free daily plan: locks sleep, prayer and class, allocates the Daily Core, rotates VISWA/CERIA slots, enforces the Rp20.000 food budget and saves to Obsidian Daily/YYYY/YYYY-MM-DD.md after an audit. Use for ''buat todolist hari ini'' or a morning plan.'
metadata:
  keywords: activates allocating asks auditing college commitments completion deadlines enforcing exercise existing first fixed locking math never owner persisting prior produce project result rotation schedule slotting task tasks times today todos under user when without work writes
---
# todolife-daily-planner

Generates one daily plan per invocation. The plan must be:

- conflict-free (no overlap between fixed and flexible);
- realistic (total hours ≤ 24h, with sleep protected);
- prioritized (FIXED > CORE > PROJECT > MAINTENANCE > OPTIONAL);
- persisted (writes to Obsidian at `Daily/YYYY/YYYY-MM-DD.md`).

## Operating procedure

### 1. AUDIT (mandatory before any plan)

Run all of these in order. If any source is missing, mark `MISSING` and stop.

1. **Date / weekday** — `datetime_now` from xninetzy MCP.
2. **College schedule** — owner-supplied source for current semester (Ganjil 2026/2027 baseline). Reject class times that conflict with prayer or sleep.
3. **Prayer times** — derive from date + Asia/Jakarta; fixed windows of ±15min around each prayer. If owner provides override, use override.
4. **Sleep window** — 23:00 → 04:00 by default; protected block.
5. **Existing tasks** — `task_list` for unfinished items.
6. **Deadlines** — `goal_list` + `task_list` filtered by `due_at`.
7. **Math / ML roadmaps** — Obsidian notes tagged `math-roadmap`, `ml-roadmap`. If absent, mark `MISSING` and pick one topic from `Mathematical AI Research Roadmap` (linear algebra as default start).
8. **Project state** — `personal_project_list` for VISWA, CERIA, others.
9. **Vault conventions** — `obsidian_folder_status`, `obsidian_template_list`. If `Daily/YYYY/` folder missing, create via `obsidian_create_folder`.

Audit output is an internal representation; do not dump it to the user.

### 2. LOCK

Mark blocks with `LOCKED` flag:

- class blocks (from college schedule);
- prayer blocks (5 daily prayers + optional Dhuha);
- sleep (23:00–04:00);
- any explicit `fixed` task from `task_list`.

LOCKED blocks cannot move, shrink, or be overwritten. If a LOCKED block overlaps another, the second is rejected — re-source and retry.

### 3. ALLOCATE CORE

In strict order. Each block is 60–120 minutes, single focus, deep-work:

1. **Mathematics 2h** — follow current topic from math roadmap; default topic if missing = `Linear Algebra → Matrix multiplication`.
2. **ML 2h** — follow current topic from ml roadmap; default if missing = `Classical ML → Logistic regression derivation`.
3. **College Task / Learning 2h** — pick from unfinished academic tasks, ordered by deadline.
4. **Exercise 1h** — high energy: gym/strength; medium: cardio; low: walking/mobility.

Allocation must respect:

- No double-counting (a "ML + CERIA model research" block is one slot, not two).
- Energy-aware: heaviest cognitive work (math) gets the highest-energy slot.
- Travel buffer after class: minimum 15 minutes between class end and next task if location changes.

### 4. ALLOCATE PROJECT

From remaining flexible time, in this order:

1. Project with nearest deadline (escalate to P2).
2. Project rotation: today → `VISWA`, tomorrow → `CERIA`, next → ML research, then repeat. Owner can override via explicit statement.

Each project task decomposed to a **next concrete action** (e.g. `CERIA — inspect auth flow`), never abstract (`work on CERIA`).

### 5. ALLOCATE OPTIONAL

Reading / math game / exploration only if leftover ≥ 30 minutes and no CORE deficit. Reading priority: math book → ML book → research paper → academic book → general.

### 6. ALLOCATE MEALS + BUDGET

Three meals (breakfast, lunch, dinner). Estimated cost ≤ Rp20.000/day. If estimate > budget, surface `Food Budget Alert` and propose swaps; do not delete meals. Optional snack up to budget.

### 7. VALIDATE

Run the full checklist (section "Validation"). If any check fails:

- mark `OVERLOAD DETECTED`;
- protect P0/P1;
- move P2/P3 to backlog/next day;
- report deficit honestly. **Never fake completion.**

### 8. PERSIST

Write to `Daily/YYYY/YYYY-MM-DD.md` using the `todolife-daily-template` body. Frontmatter:

```yaml
---
type: daily-plan
date: YYYY-MM-DD
weekday: <Senin|Selasa|Rabu|Kamis|Jumat|Sabtu|Minggu>
semester: Ganjil 2026/2027
core_status: CORE_COMPLETE | CORE_PARTIAL | CORE_DEFICIT
food_spent_rp: <int>
food_budget_rp: 20000
tags: [daily, todolife]
---
```

Then add to `Task Capture` backlog only items that were moved.

### 9. END-OF-DAY REVIEW

If invoked with `mode: review`, compare planned vs actual by reading checkboxes in the daily note. Produce:

- per-core completion (X / 2h);
- per-project delta;
- food delta;
- sleep delta;
- unfinished items moved to next-day backlog via `task_capture`.

## Core quotas (defaults, override explicitly)

| Slot | Hours | Source |
|---|---|---|
| Math | 2 | roadmap topic |
| ML | 2 | roadmap topic |
| College Task | 2 | unfinished academic task |
| Exercise | 1 | energy-adaptive |
| Project | flexible | nearest-deadline + rotation |
| Optional | leftover | only if core satisfied |

## Priority hierarchy

- P0 LOCKED: class, prayer, sleep, fixed meeting
- P1 CORE: math, ML, college task, exercise
- P2 PROJECT: VISWA, CERIA, academic project, deadline task
- P3 MAINTENANCE: email, admin, cleanup
- P4 OPTIONAL: reading, math game, exploration

P0/P1 are non-negotiable. P2 may push P3/P4 but never P0/P1.

## Validation checklist (block finalize until all pass)

- [ ] No two blocks overlap
- [ ] All class times match source exactly
- [ ] All 5 prayers within ±15min of canonical time
- [ ] Sleep 23:00–04:00 untouched
- [ ] Math tracked as `Xh / 2h`
- [ ] ML tracked as `Xh / 2h`
- [ ] College Task tracked as `Xh / 2h`
- [ ] Exercise tracked as `Xh / 1h`
- [ ] Project slotted with concrete next action
- [ ] Food estimate ≤ Rp20.000
- [ ] Travel buffer after class
- [ ] Optional only if no CORE deficit
- [ ] No double-counted hours
- [ ] Total hours ≤ 24h

## Forbidden behaviors

- ❌ Skip the audit step
- ❌ Shift class time
- ❌ Use sleep as buffer
- ❌ Mark CORE COMPLETE when CORE PARTIAL
- ❌ Write abstract project todos
- ❌ Count `ML + CERIA model research` as both 2h ML and 2h project
- ❌ Delete meals to fit budget
- ❌ Starvation / extreme calorie-cut advice (weight 57→65kg is long-term goal only)

## Required tool calls

- `datetime_now`
- `task_list`, `goal_list`
- `personal_project_list`
- `obsidian_folder_status`, `obsidian_template_list`
- `obsidian_create_folder` (if `Daily/YYYY/` missing)
- `obsidian_daily` (read existing if present)
- `obsidian_create` or `obsidian_append` (write plan)
- `task_capture` (for moved/backlog items)
- `obsidian_save_note` (alternative write path)

## Related skills

- `personal-os` — wraps goals / projects / open loops / weekly review
- `xninetzy-memory` (layer governance) — persists the daily completion as episodic memory
- `xninetzy-obsidian-orchestra` — structural mutations; do not invoke for daily plans (read-only)
- `obsidian-knowledge` — read/write semantic knowledge
