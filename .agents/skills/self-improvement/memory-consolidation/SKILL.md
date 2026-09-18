---
name: memory-consolidation
description: Consolidate episodic memory into procedure memory. Promotes validated procedures from memory_episodes to memory_procedures; retires obsolete entries. Never promotes without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - memory_episode_search
    - memory_relevance
    - reflect-trajectory
  produces:
    - memory_consolidation_proposal
  tier: 0
---

# memory-consolidation

Episode → procedure promoter. Reads recent episodes, identifies patterns
that succeeded ≥ N times, and proposes procedure promotion. Application
always requires `memory_promote` (FINAL) or `memory_retire` (FINAL).

## When to invoke

- `memory_episode_search` returns many similar episodes
- Lightning episode count > 100 and `memory_relevance` score dropping
- Owner asks "why is the agent forgetting what worked?"

## Inputs

```yaml
window_days: 7
min_success_count: 3
scope: owner | global
```

## Workflow

```yaml
steps:
  - id: episodes
    tool: memory_episode_search
    args:
      scope: "<owner | global>"
      days: 7
    tier: 0
  - id: relevance
    tool: memory_relevance
    args: { episode_ids: ["..."] }
    tier: 0
  - id: propose
    tool: improvement_propose
    args:
      target_kind: memory_consolidation
      risk_level: high
    tier: 0
```

## Output structure

```yaml
memory_consolidation_proposal:
  promote:
    - source_episode_ids: ["..."]
      procedure_text: "<single-sentence procedure>"
      confidence: 0.0-1.0
      proposed_change_id: "<id>"
  retire:
    - episode_id: "<id>"
      reason: "<superseded by newer episode | low relevance | owner-flagged>"
```

## Constraints

- Never auto-promote. Always go through `memory_promote` (FINAL).
- Never retire an episode that has unverified claims without surfacing.
- Apply path = `memory_promote` (FINAL) and/or `memory_retire` (FINAL).
