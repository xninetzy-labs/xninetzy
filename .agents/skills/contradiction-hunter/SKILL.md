---
name: contradiction-hunter
description: Detect contradicting findings across a research result set. Identifies claims where independent sources disagree, and surfaces the disagreement for synthesis.
metadata:
  type: meta
  layer: research-orchestration
  consumes:
    - evidence-grader
  produces:
    - contradictions
  tier: 0
---

# contradiction-hunter

Workflow guidance for finding where independent sources disagree.
This skill is **not** factual evidence — it produces a structured
contradiction report.

## When to invoke

- After `evidence-grader` has assigned grades to a result set
- Before final synthesis in any multi-source research plan
- When the user asks "is there disagreement" or "what do sources say"

## Inputs

```yaml
graded_evidence:
  - record: <SourceRecord>
    grade: strong | moderate | weak | uncertain
    score: 0.0-1.0
    reasons: [...]
```

## Detection heuristics

1. **Identifier overlap + claim divergence**: two sources share a DOI/arXiv
   ID but disagree on metadata (year, author, abstract summary).
2. **Topic overlap + conclusion divergence**: sources share keywords but
   contradict in `snippet` text.
3. **Freshness conflict**: one source claims X, a more recent strong source
   claims not-X.

## Output schema

```yaml
contradictions:
  - topic: "<shared keyword / DOI / claim>"
    sources:
      - id: openalex
        claim: "<quoted snippet>"
      - id: arxiv
        claim: "<quoted snippet>"
    confidence: 0.0-1.0
    possible_explanations:
      - "<dataset / benchmark / year / model size difference>"
    verdict: requires_investigation | likely_different_setup | likely_error
```

## Anti-patterns

- Do NOT mark something a contradiction based on title-only match. Use
  shared identifier or shared quoted claim.
- Do NOT propose a winner. Surface the disagreement; let the synthesis
  step decide.

## Composition

After hunting, if any contradiction has `confidence >= 0.6`, escalate to a
follow-up plan with `research_fetch` on the conflicting identifiers.
