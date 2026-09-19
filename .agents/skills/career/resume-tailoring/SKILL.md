---
name: resume-tailoring
description: Tailor a CV to a specific job posting. Produces a diff between current CV and tailored version. Never writes to disk without owner approval.
metadata:
  type: workflow
  layer: career
  consumes:
    - cv-analysis
    - career_search_jobs
  produces:
    - resume_tailoring_diff
  tier: 0
---

# resume-tailoring

Diff current CV against target posting requirements. Output is a
suggested diff, never an auto-write.

## When to invoke

- Owner asks "tailor my CV for X posting"
- Before applying to a specific role

## Inputs

```yaml
cv_analysis_report: <from cv-analysis>
posting_id: "<from career_search_jobs>"
tone: conservative | balanced | bold
```

## Workflow

```yaml
steps:
  - id: fetch_posting
    tool: career_search_jobs
    args: { posting_id: "<posting_id>" }
    tier: 0
  - id: propose_diff
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [fetch_posting]
```

## Output structure

```yaml
resume_tailoring_diff:
  posting_id: "<id>"
  changes:
    - section: skills | summary | experience
      before: "<excerpt>"
      after: "<excerpt>"
      rationale: "<cite posting requirement>"
  apply_path: obsidian_save_note | manual_edit
```

## Constraints

- Never overwrite the source CV file.
- Always emit `apply_path` so owner can review before committing.
- Only suggest edits supported by facts in the original CV.

## Anti-patterns

- Do NOT fabricate experience the owner doesn't have.
- Do NOT pad with skills absent from original CV.
