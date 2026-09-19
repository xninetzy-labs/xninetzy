---
name: cv-analysis
description: Analyze a CV/resume text provided by owner. Surfaces skills, experience, gaps. Does not call external job boards in this step.
metadata:
  type: workflow
  layer: career
  consumes:
    - obsidian_read
    - knowledge_search
  produces:
    - cv_analysis_report
  tier: 0
---

# cv-analysis

Read owner's CV (text from Obsidian vault, or inline input) and produce
structured analysis. No external source calls.

## When to invoke

- Owner pastes a CV or references an Obsidian file
- Before `resume-tailoring` or `skill-gap`

## Inputs

```yaml
cv_source: obsidian_path | inline_text
cv_path: "<path>"  # if obsidian_path
cv_text: "<text>"  # if inline_text
```

## Workflow

```yaml
steps:
  - id: read
    tool: obsidian_read
    args: { path: "<cv_path>" }
    tier: 0
  - id: analyze
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [read]
```

## Output structure

```yaml
cv_analysis_report:
  skills: ["..."]
  experience:
    - role: "<title>"
      company: "<company>"
      duration_months: <int>
      highlights: ["..."]
  education: [...]
  gaps_observed: ["..."]
  suggested_next_skill: skill-gap | resume-tailoring
```

## Constraints

- Read CV only from owner-controlled locations (Obsidian vault or inline).
- Never upload CV to external services.
- Always cite line/section references when surfacing claims.

## Anti-patterns

- Do NOT fabricate skills absent from CV text.
- Do NOT grade the CV; surface strengths and gaps only.
