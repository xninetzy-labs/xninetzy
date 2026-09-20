---
layout: ../../layouts/DocsLayout.astro
title: Personal OS
description: Goals, projects, skills, open loops, and reviews as a coherent layer over Obsidian/notes.
section: Operations
badge: Reference
difficulty: intermediate
readingTime: 8 min
---

Personal OS is the **coordination layer** over the existing goal /
task / habit / journal / workout / money managers
(`xninetzy/os/life/`). It does NOT replace them — it adds:

1. **`personal_projects`** with explicit `next_action` and stall
   detection
2. **`open_loops`** for unresolved items with importance + age
3. **`skill_state`** tracking evidence-based mastery
4. **`review`** engine that surfaces stalled projects + loop
   overflow

```text
USER
  ↓
Personal OS (xninetzy/context/personal_os/)
  ├── personal_projects  (project_id, goal_id, status, next_action)
  ├── open_loops        (loop_id, importance, age_days, status)
  ├── skill_state       (skill_id, status, evidence_count)
  └── review            (active + stalled + recommendations)
        ↓
        Evaluation → Learning → Lightning
```

## 1. Projects

`personal_project_create(title, objective, goal_id, next_action)` —
next_action is **mandatory**. A project without next_action will be
flagged by `personal_review_run` as stalled after 14 days of no
activity.

`status` state machine: `active → paused → completed | abandoned`.
Pausing is preferred over abandoning; abandonment should be a
deliberate owner decision.

## 2. Open Loops

`open_loops` track unresolved items:

- pending responses
- deferred decisions
- things the user wants closure on

Do NOT use open loops for fixed-time reminders or chat history. Each
loop carries `importance` (low / medium / high), `age_days`, and an
optional `project_id`. `(owner_scope, title)` is unique → same loop
returned on duplicate open.

## 3. Skill state

`personal_skill_register(name)` creates a tracker. `advance_skill`
increments `evidence_count` and updates `last_practiced`. Status
progression: `unknown → exposed → practicing → applied → strong →
stale`. `stale` is set when evidence is missing for an extended
period (caller-side decision based on policy).

`evidence_count` is incremented by the caller, not by the system —
this preserves human agency over what counts as mastery.

## 4. Review

`personal_review_run(period)` returns:

- `active_projects`: list of project IDs in `active` status
- `open_loops`: list of loop IDs currently open
- `stalled_projects`: projects with `last_activity` ≥ 14 days old
- `recommendations`: human-readable suggestions such as
  `"3 active projects inactive >= 14 days — review next_action."`

The review engine never mutates state. Recommendations are
suggestions, not commands.

## 5. MCP tools

| Tool | Use |
|---|---|
| `personal_project_create` | Create project (requires next_action) |
| `personal_project_list` | List active projects (or filter by status) |
| `personal_project_status` | Transition status, optionally update next_action |
| `personal_open_loop_create` | Track unresolved item |
| `personal_open_loop_list` | List open loops with age + importance |
| `personal_open_loop_resolve` | Close a loop |
| `personal_skill_register` | Register a skill tracker |
| `personal_skill_advance` | Record evidence + status update |
| `personal_review_run` | Run a review |

Total registered tools: **401** (audit-script-verified).

## 6. Skill

`.agents/skills/personal-os/SKILL.md` enforces:

- `next_action` required for projects
- open-loop ↔ reminder / memory boundaries
- no auto-completion of projects
- no auto-resolution of loops
- review recommendations are suggestions, not commands

## 7. Separation of concerns

| Concern | System |
|---|---|
| Calendar / time blocks | `os/jobs/` scheduler |
| Reminders | `os/reminders/` |
| Chat memory | `context/memory/`, `context/capability_graph/` |
| Knowledge / notes | Obsidian (`os/notes/`) |
| Goal / task / habit CRUD | `os/life/*_manager.py` |
| **Personal OS coordination** | `context/personal_os/` (this layer) |
| Reviews | `personal_review_run` |
| Self-improvement | `context/learning/`, `context/evaluation/`, `os/lightning/` |

## 8. Tests

`tests/personal_os/test_service.py` covers:

- Project CRUD with mandatory next_action
- Open-loop idempotency on `(owner, title)`
- Skill evidence accumulation
- Review stalled-project detection (uses injected clock)
- Loop resolution removes from open list

## 9. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `XNINETZY_PERSONAL_OS_STALL_DAYS` | `14` | Days without activity before a project is "stalled" |

(Read by `stall_project`.)

## 10. Failure containment

| Failure | Behavior |
|---|---|
| Empty `next_action` on create | Accepted but flagged by review |
| Unknown status string | `ValueError` raised, surfaced via tool error |
| Resolve nonexistent loop | Returns `None`, surfaced via tool error |
| Skill `advance` on missing name | Auto-registers first, then advances |
| DB unavailable | `PersonalOS` raises — surface as tool error |
