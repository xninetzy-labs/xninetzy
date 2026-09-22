---
name: skill-improvement-opportunity-logger
description: 'Long-running capability layered on top of the Lightning RL trace. Watches
  installed skills for friction patterns: repeated tool calls, low-confidence retrievals,
  owner escalations, recovery thrashing, prompt-size blow-ups. Emits structured `ImprovementProposal`
  objects routed through Lightning → HITL → `skill-creator` → benchmark → publish
  loop. Use when the operator asks "what''s blocking the harness", or any time Lightning
  episodes are recorded into the trace store.'
metadata:
  author: xninetzy
  version: 1.0.0
  scope: process
  priority: P0
  required_tools: '["lightning_record_action","lightning_record_outcome","lightning_episode_finish","lightning_propose_improvement","lightning_list_proposals","skill_list","skill_get"]'
  optional_tools: '["os_inbox","hitl_request_approval","memory_search","memory_add"]'
  trigger_conditions: '["Lightning episode trace accumulates ≥ 50 episodes on a task
    type","owner asks \"what''s blocking the harness\"","an episode shows retry thrashing
    (≥ 3 consecutive failed tool calls)","a recovery loop fires more than twice in
    one episode"]'
  prerequisites: '["Lightning trace store has ≥ 1 episode for the relevant task type","target
    skill name or tool surface is known"]'
---


# skill-improvement-opportunity-logger

A skill that protects the harness from drifting into habits that
silently cost context, time, or correctness. It never edits skills
directly. It only emits proposals that flow through the same eval →
benchmark → approval gate that ships any other change.

## Operating procedure

```
OBSERVE
   ↓
EXTRACT
   ↓
CLUSTER
   ↓
PROPOSE
   ↓
ROUTE
```

### 1. OBSERVE

Pull the latest Lightning episodes for the targeted skill name or task
type. The minimum slice is:

- last `N` episodes (default 50, configurable) where the skill was used
- episodes where recovery fired more than once
- episodes where owner-inbox received an `intent=blocked` capture
- episodes where tool-call count exceeded the skill's expected bound

Required tools: `lightning_record_action`, `lightning_record_outcome`

### 2. EXTRACT

For each episode reduce to a structured trace summary:

```
episode {
    task_type
    skill_used
    tools_called_in_order
    tool_failures_in_order
    retries
    recoveries
    context_size_at_start
    context_size_at_end
    duration
    outcome_code
}
```

Persist these summaries to durable storage so subsequent analysis does
not re-scan raw Lightning episodes.

### 3. CLUSTER

Group similar friction patterns by:

- same skill
- same tool chain
- same failure mode class (`WRONG_TOOL`, `INSUFFICIENT_EVIDENCE`,
  `RECOVERY` thrashing, `CONTEXT_BUDGET_EXCEEDED`)
- same owner-inbox topic

If a cluster reaches the configured threshold (default: appears in
≥ 20 % of episodes for the skill), it graduates from `friction log`
to a candidate proposal.

### 4. PROPOSE

Emit a structured `ImprovementProposal` JSON:

```
ImprovementProposal {
    id: "<uuid>"
    source_episodes: ["<id>", ...]
    observed_problem: "<one-sentence description>"
    root_cause: "<best-known-cause>"
    evidence: { ... }
    affected_skills: ["<name>", ...]
    affected_tools: ["<tool>", ...]
    expected_gain: "<percentage on the same benchmark>"
    regression_risk: "<low|medium|high>"
    test_plan: "<which evals must pass before promotion>"
    approval_state: "pending"
}
```

Required tools: `lightning_propose_improvement`

### 5. ROUTE

The proposal must traverse three gates before it can mutate a skill:

1. `lightning_propose_improvement` records the proposal
2. `lightning_approve` — only the owner; the improvement does not
   auto-apply
3. `skill-creator` — once approved, this skill is invoked to mutate
   the target skill, regenerate evals, run benchmark, and only then
   publish

If any gate rejects, the proposal is archived with its evidence; it
may surface again later if the friction cluster persists.

## What this skill never does

- directly edits any SKILL.md
- calls `skill_install` or `skill_validate` without going through
  `skill-creator`
- bypasses Lightning → HITL approval
- promotes a change that the benchmark reports as a regression
- claims a skill is improved without producing evidence

## Output contract

A logged investigation returns:

```
skill-improvement-opportunity-logger report
target_skill: <name>
episodes_scanned: N
friction_clusters: [
    {
  id: "<hash>",
  frequency_pct: <float>,
  failure_class: "..."
  sample_episodes: ["<id>", ...]
  proposal_id: "<uuid>" | None
    }
]
recommended_action: "create proposal" | "monitor" | "no action"
```

## Failure classification

| Class                          | Action                          |
|--------------------------------|---------------------------------|
| `INSUFFICIENT_EVIDENCE`        | clusters below threshold; continue observing |
| `PROPOSAL_DUPLICATE`           | cluster already has an open proposal; link to it instead |
| `BENCHMARK_REGRESSION_RISK`    | reject if regression_risk=high and test_plan absent |
| `APPROVAL_TIMEOUT`             | proposal auto-archived after N days; cluster may re-trigger |

## Recovery

For false positives (cluster that later proves benign), the owner can
mark the proposal as "won't fix" via `lightning_reject` with reason
`false_positive`. The cluster is downgraded back to monitoring for a
configurable cooldown period to avoid re-issuing immediately.

## See also

- `skill-creator` — the next-step skill once an opportunity is approved
- `skill-security-review` — gates every publication
- `lightning_improve` — the proposal application engine; this skill feeds
  into it
- `memory-management` — for capturing repeated-owner friction into long-term
  memory
