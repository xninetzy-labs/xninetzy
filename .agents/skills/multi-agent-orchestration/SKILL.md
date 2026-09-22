---
name: multi-agent-orchestration
description: 'Distributes a structured project across parallel sub-agents that each
  reason independently against a scoped context slice. Used for large audit / refactor
  / research tasks where one agent''s context window is insufficient. Merges results
  with an explicit verification step and surfaces contradictions to the owner. Stays
  client-side: orchestration lives in this skill, never on the Xninetzy server (no
  server-side agent loop). Use when the operator asks for a multi-aspect audit, parallel
  investigation, or any task whose blast radius calls for four or more focused agents.'
metadata:
  author: xninetzy
  version: 1.0.0
  scope: harness
  priority: P0
  required_tools: '["lightning_episode_start","lightning_episode_finish","lightning_record_action","lightning_record_outcome","todo_tool","hitl_request_approval"]'
  optional_tools: '["context_engineering","repo_search","security_scope","repo_architecture","os_inbox"]'
  trigger_conditions: '["structured project of ≥ 4 distinct sub-domains","operator
    asks \"audit architecture, security, and tests in parallel\"","a single agent''s
    context budget is exceeded"]'
  prerequisites: '["project plan exists (use `structured-project-execution`)","sub-agents
    declared with non-overlapping responsibilities","merge strategy stated before
    execution begins"]'
---


# multi-agent-orchestration

One agent cannot audit a 1000-file repo, run the security scan, the
test suite, the documentation drift, and the dependency review in
sequence without losing context. This skill splits the work across
focused sub-agents and merges verified results.

Crucially, **orchestration stays client-side**. Xninetzy does not have
a server-side agent loop. This skill is a procedure the harness runs to
coordinate sub-tasks; it never requires the server to spawn or chain
agents.

## Operating procedure

```
DECOMPOSE
   ↓
ASSIGN
   ↓
EXECUTE
   ↓
MERGE
   ↓
VERIFY
   ↓
REPORT
```

### 1. DECOMPOSE

Split the parent task along non-overlapping axes. Each axis MUST be
verifiable independently. Examples:

- **Architecture audit**: top-level layout, dependency graph, public-API
  surface, configuration drift, observability gaps
- **Security audit**: input-validation surface, authn/z, secret
  handling, dependency CVEs, outgoing network scope
- **Test audit**: coverage gaps, flaky patterns, missing assertion
  quality, regression risk
- **Documentation drift**: README, AGENTS.md, skills, tool descriptions

Each axis is a sub-agent with its own context slice, its own
`memory_context` window, and its own Lightning episode.

Refuse to decompose a task that has fewer than four sub-agents worth of
work; one agent is cheaper.

### 2. ASSIGN

For each sub-agent:

- name (e.g., `arch-audit`)
- scope (which paths / files / domains)
- tools allowed (a whitelist per sub-agent; never the full catalog)
- output contract (what the sub-agent must produce before the merge)
- deadline (round budget)
- evidence required (which test / scan / grep result proves it done)
- failure mode (what to do if it cannot complete)

Assignments go through `todo_tool`. Each sub-agent runs as an
isolated `lightning_episode_start` so its tool calls are independently
auditable.

Required: every sub-agent receives the **same minimal context slice**
(L0-L2) plus the **same project state slice** (L4) so they can verify
each other later.

### 3. EXECUTE

Parallelize where safe:

- independent sub-agents run concurrently
- dependent sub-agents (one consumes another's output) run sequentially

Sub-agents communicate only through:

- durable artifacts (file paths, SQLite rows)
- structured hand-off messages in `os_inbox`

Sub-agents **never** mutate the parent agent's working memory directly.

### 4. MERGE

The merge step is explicit and deterministic. Default merge order:

1. **highest severity first**: any security-risk finding goes to the top
2. **contradictions surfaced**: if two sub-agents disagree on a fact,
   the merge records the disagreement, not a vote or pick
3. **shared findings deduplicated**: if both arch and security audit
   flag a missing rate limiter, dedupe to one entry with both sources
4. **missing-evidence flagged**: any axis whose output is missing the
   evidence required in `ASSIGN` is marked incomplete and routed back
   for a retry with the same scope (not expanded)

The merge produces a single report with the same JSON shape as the
sub-agent outputs.

### 5. VERIFY

Verification of the merged report runs two checks:

- **cross-check**: every finding has at least one independent
  confirmation in another sub-agent's output, OR an explicit
  reason-no-cross-check accepted by the owner
- **evidence attachment**: every finding cites a tool, file, line range,
  or external source

Sub-agents provide their cross-check evidence through their
lightning_record_action calls; the merge cross-references them.

### 6. REPORT

The final report routes through `os_inbox` with idempotency key
`project:<project_id>`. The owner sees:

- each sub-agent's deliverable
- the cross-check matrix
- contradictions
- the merged proposal list

If contradictions remain unresolved, the report is `INCOMPLETE` —
the harness does not finish the project.

## Output contract

A multi-agent-orchestration invocation returns:

```
multi-agent-orchestration report
project_id: <uuid>
sub_agents: [{ name, scope, status, episodes: [...] }, ...]
merged_findings: [{ severity, location, evidence, sources: [...] }, ...]
contradictions: [{ finding_a, finding_b, owner_decision_pending: true }, ...]
cross_check_matrix: { finding_id: [confirmed_by, ...] }
verdict: COMPLETE | INCOMPLETE
```

## Failure classification

| Class                          | Action                                |
|--------------------------------|---------------------------------------|
| `SUB_AGENT_INCOMPLETE`         | retry once with same scope; route to owner if second miss |
| `CROSS_CHECK_FAILED`           | owner decision required; do not finalize |
| `CONTRADICTION_UNRESOLVED`     | leave report `INCOMPLETE` |
| `MERGE_CONFLICT`               | prefer higher-severity finding; dedupe, log |
| `STATE_DRIFT`                  | re-load parent project state from SQLite |

## Recovery

A sub-agent that returns no evidence is restarted with stricter
verification requirements. A project that loses >50% of sub-agents
to failure is `ABORTED` and routed to the owner — manual recovery is
cheaper than a degraded merge.

## See also

- `context-engineering` — sub-agent context construction
- `structured-project-execution` — the spine for the parent project
- `repo-context-packaging` — packaging the L4 layer for sub-agents
- `tdd-workflow` — verification protocol for engineering sub-agents
