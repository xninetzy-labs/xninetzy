---
name: job-risk-analysis
description: Analyze a posting or company for scam/fraud risk signals. Heuristic check against public red-flag patterns. Never defames; always cites observation.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - company-research
  produces:
    - job_risk_report
  tier: 0
---

# job-risk-analysis

Heuristic risk screening. Surfaces common scam signals (upfront fees,
vague descriptions, unrealistic pay, missing company info). Never
defames; cites observation only.

## When to invoke

- Owner receives an unsolicited offer
- Before applying to a posting with low information

## Inputs

```yaml
posting_id: "<id>"
```

## Workflow

```yaml
steps:
  - id: fetch
    tool: career_search_jobs
    args: { posting_id: "<id>" }
    tier: 0
  - id: company
    tool: career_company_research
    args: { company_name: "<posting.company>" }
    tier: 0
  - id: score
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [fetch, company]
```

## Output structure

```yaml
job_risk_report:
  posting_id: "<id>"
  risk_grade: low | medium | high
  flags:
    - signal: "<description>"
      evidence: "<quoted observation>"
  recommendation: apply_with_caution | skip | safe
```

## Constraints

- Always cite evidence (quoted text).
- Never assert fraud; assert risk signals.
- Recommendation is heuristic; owner decides.

## Anti-patterns

- Do NOT defame.
- Do NOT score demographic or origin-based risk.
