---
name: optimize-tool-routing
description: Recommend changes to the source-routing table and tool-intent resolver based on cross-source classification accuracy. Surfaces routing-table diffs; never applies without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - intent_resolve
    - tool_route
    - reflect-trajectory
    - analyze-failure
  produces:
    - routing_candidates
  tier: 0
---

# optimize-tool-routing

Routing-table variant generator. Reads `intent_resolve` accuracy signals
+ reflection lessons + failure diagnoses and surfaces candidate routing
edits. Application always requires `improvement_approve` (FINAL).

## When to invoke

- `tool_selection_accuracy` from `evaluate-agent` is below 0.7
- Reflection surfaces a `tool`-applicability lesson
- Owner asks "why did this query route to the wrong source?"

## Inputs

```yaml
target: source_routing | intent_resolver | tool_aliases
evidence_refs: ["<plan_id>", "..."]
```

## Workflow

```yaml
steps:
  - id: gather
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: propose
    tool: improvement_propose
    args:
      target_kind: routing_table
      risk_level: medium
    tier: 0
```

## Output structure

```yaml
routing_candidates:
  target: source_routing
  baseline_intent: paper
  baseline_sources: [openalex, arxiv, crossref]
  candidates:
    - intent: paper
      sources: [openalex, semantic_scholar, pubmed, arxiv, crossref]
      rationale: "<cite lesson + accuracy signal>"
      proposed_change_id: "<id>"
```

## Constraints

- Never propose removing `wikidata` or `dbpedia` from `entity` routing.
- Never propose routing FINAL-class tools (hebat_upload_submission,
  portal_krs_war_arm, etc.) through auto-execute paths.
- Apply path = `improvement_approve` (FINAL).
