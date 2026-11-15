---
name: todolife-project-router
description: Assigns project slots to VISWA, CERIA, AI/ML or academic work by deadline, rotation and remaining capacity. Use inside the daily planner or for 'hari ini project apa'.
metadata:
  keywords: activates allocating asks based projects proximity route schedule todolife user when
---

# todolife-project-router

## Inputs

- Today's daily note (or empty if pre-plan).
- `personal_project_list` from xninetzy MCP.
- Rotation baseline: today → VISWA, tomorrow → CERIA, next → ML research, then repeat. Owner can override explicitly.

## Decision algorithm

1. **Deadline escalation.** If any project task has `due_at` within 48h, that project gets today's slot regardless of rotation. Document the override.
2. **Rotation baseline.** Else, follow the day-of-week rotation.
3. **Capacity check.** If remaining flexible hours after CORE quotas < 1h, skip project slot entirely. Mark `NO_PROJECT_SLOT`.
4. **Next action decomposition.** For the chosen project, read the project note, find the smallest next-action TODO, slot it. If project note missing or has no next-action, generate one from `personal_project_status(project_id)` + the project objective.

## Output

```yaml
project_today: VISWA | CERIA | <name> | NONE
next_action: "<verb> <object>" — concrete, completable in one focused block
estimated_minutes: 60 | 90 | 120
override_reason: deadline | rotation | capacity
```

If `NONE`, daily plan shows `Project: BACKLOG` and the slot is reallocated to maintenance or optional.

## Anti-patterns

- ❌ Schedule two unrelated projects in one slot (context switching)
- ❌ Schedule a project with no concrete next action
- ❌ Override rotation without documenting reason
- ❌ Slot a project that pushes CORE to deficit

## Related

- `personal-os` — project lifecycle + status
- `todolife-daily-planner` — consumer
