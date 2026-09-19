---
name: interview-prep
description: Generate interview preparation pack for a target posting: company brief, likely questions, technical refreshers, project storytelling prompts.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - company-research
    - cv-analysis
  produces:
    - interview_prep_pack
  tier: 0
---

# interview-prep

Build an interview-prep pack from posting + company brief + CV.

## When to invoke

- Owner has an interview scheduled
- After applying to a posting

## Inputs

```yaml
posting_id: "<id>"
cv_analysis_report: <from cv-analysis>
company_research_report: <from company-research>
```

## Workflow

```yaml
steps:
  - id: posting
    tool: career_search_jobs
    args: { posting_id: "<id>" }
    tier: 0
  - id: questions
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [posting]
```

## Output structure

```yaml
interview_prep_pack:
  posting_id: "<id>"
  company_brief: "<short>"
  likely_questions:
    - question: "<text>"
      suggested_answer_prompt: "<cite CV experience>"
  technical_refreshers:
    - topic: "<e.g. system design>"
      sources:
        - skill: research-paper-search
  project_storytelling_prompts:
    - experience_ref: "<CV entry>"
      story_arc: "<STAR format>"
```

## Constraints

- Always cite CV entries when suggesting answer prompts.
- Never invent experience absent from CV.
- Always include `technical_refreshers` tied to existing skill bodies.

## Anti-patterns

- Do NOT suggest answers that contradict the CV.
- Do NOT propose memorized scripts; suggest talking points only.
