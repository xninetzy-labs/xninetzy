---
name: personal-os
description: Use when the user wants to manage goals, projects, open loops, skills, or run a daily/weekly review. Enforces project→next_action and open-loop lifecycle rules. Do NOT use for one-off reminders or chat memory — those have their own tools.
metadata:
  type: workflow
  domain: personal_os
  capabilities:
    - personal_project_create
    - personal_project_list
    - personal_project_status
    - personal_open_loop_create
    - personal_open_loop_list
    - personal_open_loop_resolve
    - personal_skill_register
    - personal_skill_advance
    - personal_review_run
  version: 1.0.0
---

# Personal OS Workflow

Use this skill when the request maps to any of:

- tracking a project / goal
- recording an unresolved item ("waiting on X", "need to decide Y")
- advancing a skill state with evidence
- running a daily / weekly / monthly review

Do NOT collapse projects and tasks into one. A project without a
next action is stalled by definition.

## Decision tree

```text
user request
   ├── "start / track a project"        → personal_project_create
   ├── "what am I working on?"          → personal_project_list
   ├── "this is no longer active"       → personal_project_status
   ├── "I'm waiting on X / need to Y"   → personal_open_loop_create
   ├── "did X resolve?"                 → personal_open_loop_resolve
   ├── "I practiced / applied skill"    → personal_skill_advance
   └── "weekly review"                  → personal_review_run
```

## Required workflow

### Project creation

Every project MUST be created with a `next_action`. Never create a
project with an empty `next_action`. If the user has no clear next
step, ask before creating.

### Open loops

Open loops are the right place for:

- pending responses
- deferred decisions
- items the user wants closure on

Do NOT use open loops for:

- reminders with a fixed time (use the reminder system)
- chat history facts (use memory)

Idempotency: same `(owner, title)` returns the existing loop.

### Review

`personal_review_run` returns `stalled_projects`, `open_loops`, and
`recommendations`. Surface them in the conversation. Do NOT
silently make decisions for the user. Recommendations are
**suggestions**, not commands.

## Non-negotiable rules

- Never auto-complete a project.
- Never auto-resolve an open loop without an explicit user request.
- Never bulk-close loops in a review.
- Never silently redefine goal / project relationships.
- Never fabricate evidence for `personal_skill_advance`.
