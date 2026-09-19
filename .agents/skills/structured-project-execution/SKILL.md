---
name: "structured-project-execution"
description: "Durable execution state for non-trivial multi-step work (≥ 30 steps). Replaces ad-hoc \"carry state in the conversation context\" with a state machine: PLAN → IN_PROGRESS → BLOCKED → VERIFIED → DONE, with explicit checkpoints, decisions, artifacts, verifications, and rollback strategies persisted between harness invocations. Use on any engineering / research / security task expected to span more than a single MCP exchange."
metadata:
  author: "xninetzy"
  version: "1.0.0"
  scope: "harness"
  priority: "P0"
  required_tools:
    - repo_search
    - write_file
    - read_file
    - todo_tool
    - lightning_episode_start
    - lightning_episode_finish
    - lightning_record_action
    - hitl_request_approval
  optional_tools:
    - os_inbox
    - memory_add
    - memory_search
  trigger_conditions:
    - the operator asks for a project of ≥ 30 steps, multi-PR, or multi-week work
    - the operator asks for a security audit, repository migration, or large refactor
    - any task whose previous attempt lost state across harness invocations
  prerequisites:
    - target project / goal
    - target branch / working directory
    - approval status (auto vs HITL-gated)
---

# structured-project-execution

Ad-hoc execution drifts. This skill enforces a state machine so a 100-step
project survives harness restarts, model swaps, or operator absences.

## State machine

```
PLAN
   ↓
IN_PROGRESS
   ↓
BLOCKED          ←→ APPROVAL_REQUESTED
   ↓                  ↓
VERIFIED            APPROVED
   ↓                  ↓
DONE            ←←  IN_PROGRESS  (resume)
   ↓
ARCHIVED
```

Every transition is persisted with: timestamp, actor (skill or owner),
relevant episode IDs, and the artifact or decision that triggered it.

## Operating procedure

```
OBJECTIVE
   ↓
PLAN
   ↓
CHECKPOINT
   ↓
EXECUTE
   ↓
VERIFY
   ↓
HANDOFF
```

### 1. OBJECTIVE

State the desired end-state in measurable terms. Without a measurable
end-state, refuse to proceed.

### 2. PLAN

Decompose into a hierarchical task tree:

```
Project
├── milestone 1
│   ├── task 1.1
│   ├── task 1.2
│   └── task 1.3
├── milestone 2
│   ├── task 2.1
│   └── ...
```

For each task, capture:

- `goal` — one sentence
- `dependencies` — other task IDs that must complete first
- `evidence` — what proves it done (test, diff, owner sign-off)
- `verification` — which tool / test / owner check confirms it
- `approval_requirement` — bool; if true, `hitl_request_approval` must
  succeed before status flips to `VERIFIED`
- `rollback_strategy` — how to revert without leaving the repo dirty

Persist the plan via `todo_tool` or a project-state SQLite table
(`xninetzy/db/project_state.py`).

### 3. CHECKPOINT

Each task completion produces a checkpoint:

```
Checkpoint {
    task_id
    status
    completed_at
    artifact_path
    verification_result
    lightning_episode_ids: [...]
    blocker: <string | None>
}
```

Persist every checkpoint. The state machine can resume from any
checkpoint on next invocation.

### 4. EXECUTE

For each task:

- run the smallest sufficient tool sequence
- record every tool call via `lightning_record_action` + `lightning_record_outcome`
- capture the produced artifact path or output
- on failure, do NOT silently retry — call `skill-improvement-opportunity-logger`
  classify / record / continue
- on success, mark checkpoint and proceed to next task

If a task blocks (needs HITL, missing evidence, etc.), transition to
`BLOCKED` and surface to the owner via `os_inbox` + `hitl_request_approval`.

### 5. VERIFY

Run the listed `verification` step:

- read the checkpoint
- execute the verification tool
- compare expected vs actual
- if mismatch → transition back to `IN_PROGRESS` with a fresh checkpoint
- if match → transition to `VERIFIED`

### 6. HANDOFF

When all tasks are `VERIFIED`:

- mark project `DONE`
- emit a handoff summary: what changed, what tests pass, what risks remain
- persist the handoff to `os_inbox` so the owner has a single traceable
  artifact
- for security-sensitive projects, archive the audit log into
  `memory_research_store` with full provenance

If the owner discontinues the project mid-flight, mark `ARCHIVED` (not
`DONE`) so future attempts do not relaunch the same scope.

## Output contract

The skill emits a state summary on every invocation:

```
structured-project-execution state
project_id: <uuid>
status: PLAN | IN_PROGRESS | BLOCKED | VERIFIED | DONE | ARCHIVED
completed: N / total
current_task: <id>
next_task: <id>
blockers: [...]
artifacts: [...]
verification_status: pass | pending | fail
next_action: <string>
```

## Failure classification

| Class                          | Cause                                      | Action                                |
|--------------------------------|--------------------------------------------|---------------------------------------|
| `BLOCKED_APPROVAL`             | owner has not approved                       | route via HITL, wait for approval    |
| `VERIFICATION_MISMATCH`        | checkpoint artifact fails verification       | revert task to `IN_PROGRESS`         |
| `ROLLBACK_REQUIRED`            | failure left dirty state                    | execute rollback_strategy           |
| `STALE_STATE`                  | project not resumed in N days               | mark `ARCHIVED`                     |
| `DEPENDENCY_VIOLATION`         | task started before dependency satisfied    | block until unblocked               |

## Recovery

A failed checkpoint never silently rolls forward. Each failure produces
an evidence record, optionally a `Lightning` improvement proposal, and
a state transition. The owner can resume any time via
`structured-project-execution status <project_id>`.

## See also

- `context-engineering` — L4 / L5 layers consume project state
- `multi-agent-orchestration` — distributes per-task execution across
  parallel sub-agents
- `memory-management` — promotes proven project conventions into
  semantic memory
- `tdd-workflow` — the default verification protocol for engineering tasks
