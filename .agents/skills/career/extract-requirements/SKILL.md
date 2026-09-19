---
name: extract-requirements
description: Pull structured requirements (skills, stack, experience signals) from a job posting.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_extract_requirements
    - career_get_job
  produces:
    - requirements_report
  tier: 0
---

# extract-requirements

Heuristic keyword extraction from posting text. Output is keyword
list; LLM-side refinement recommended for nuance.

## When to invoke

- Before CV tailoring or interview prep
- After fetching a posting

## Inputs

```yaml
posting_id: "<id>"
```

## Workflow

```yaml
steps:
  - id: extract
    tool: career_extract_requirements
    args: { posting_id: "<id>" }
    tier: 0
```

## Output structure

```yaml
requirements_report:
  posting_id: "<id>"
  requirements: ["python", "docker", ...]
  caveat: "Keyword extraction is heuristic; LLM refinement recommended for nuance."
  status: ok | not_found
```

## Constraints

- Always cite `caveat` about heuristic nature.
- Always include `posting_id` in output.
- Never infer experience years absent from the posting.

## Anti-patterns

- Do NOT add requirements from postings other than the requested one.
- Do NOT pad with skills from the company's generic JD template.
