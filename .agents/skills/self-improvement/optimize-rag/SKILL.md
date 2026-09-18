---
name: optimize-rag
description: Recommend RAG retrieval-parameter changes (top_k, score threshold, source whitelist) based on evidence grading output. Surfaces config diffs; never applies without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - reflect-trajectory
    - evidence-grader
    - research_grade_evidence
  produces:
    - rag_config_candidates
  tier: 0
---

# optimize-rag

RAG-config variant generator. Reads graded evidence + reflection lessons
and surfaces candidate retrieval-parameter changes. Application always
requires `improvement_approve` (FINAL).

## When to invoke

- `evidence_grade_distribution` shows high `weak`/`uncertain` count
- Reflection surfaces a `tool`-applicability lesson about retrieval
- Owner asks "why is RAG returning low-quality chunks?"

## Inputs

```yaml
target: top_k | score_threshold | source_whitelist | reranker
evidence_refs: ["<plan_id>", "..."]
```

## Workflow

```yaml
steps:
  - id: grades
    tool: research_grade_evidence
    args:
      record_dicts: []
    tier: 0
  - id: lessons
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: propose
    tool: improvement_propose
    args:
      target_kind: rag_config
      risk_level: medium
    tier: 0
```

## Output structure

```yaml
rag_config_candidates:
  target: top_k
  baseline: { top_k: 5, score_threshold: 0.28 }
  candidates:
    - params: { top_k: 8, score_threshold: 0.32 }
      rationale: "<cite lesson>"
      expected_metric_delta:
        evidence_grade_distribution:
          strong: "+N"
          weak: "-N"
      proposed_change_id: "<id>"
```

## Constraints

- Never propose a config that disables source provenance.
- Never propose removing rate-limit or circuit-breaker guards.
- Apply path = `improvement_approve` (FINAL); never auto-apply.
