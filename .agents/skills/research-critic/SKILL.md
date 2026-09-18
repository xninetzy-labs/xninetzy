---
name: research-critic
description: Critique a completed research synthesis. Identifies missing sources, weak claims, over-strong conclusions, and unverified assumptions. Final pass before delivery to the user.
metadata:
  type: meta
  layer: research-orchestration
  consumes:
    - evidence-grader
    - contradiction-hunter
  produces:
    - critique
  tier: 0
---

# research-critic

Final critique pass over a research synthesis. This skill is **not**
factual evidence — it is a self-audit step before delivering results to
the owner.

## When to invoke

- After `evidence-grader` and `contradiction-hunter` produce their reports
- Always as the last step of a research plan before reporting back to user
- Whenever the user asks "are you sure" or "what's missing"

## Inputs

```yaml
synthesis: "<the proposed answer text>"
graded_evidence: [...]
contradictions: [...]
```

## Critique checklist

1. **Source coverage** — are all major independent sources represented?
2. **Evidence strength** — is every claim backed by `strong` or `moderate`
   grade, or is it `weak` / `uncertain`?
3. **Contradictions addressed** — if contradictions exist, did synthesis
   either resolve or explicitly flag them?
4. **Over-strong conclusions** — does the synthesis claim certainty where
   evidence is `weak`?
5. **Unsupported assumptions** — any claim that no source actually
   supports?
6. **Recency** — are there newer sources that would change the answer?
7. **Bias** — single-source dominance? Geographic / institutional skew?

## Output schema

```yaml
critique:
  verdict: ship | revise | insufficient
  findings:
    - severity: high | medium | low
      category: coverage | evidence | contradiction | certainty | assumption | recency | bias
      finding: "<human-readable>"
      fix: "<suggested action>"
  missing_queries:
    - "<search query to run for a follow-up>"
```

## Verdicts

- `ship` — synthesis is ready, no critical findings
- `revise` — one or more high-severity findings, revise before delivery
- `insufficient` — evidence base too thin to answer; request more sources

## Anti-patterns

- Do NOT auto-rewrite the synthesis. The critic surfaces findings; the
  planning loop decides.
- Do NOT mark findings as resolved without a citation.
- Do NOT skip the critique step on quick research plans. A quick plan
  may opt out of `min_independent_sources >= 2` (per research-planner)
  but must still pass through the critic for at least one high-severity
  sweep before delivery.
