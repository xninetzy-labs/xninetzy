---
name: alternative-titles
description: Expand a role title to synonyms + seniority variants. Useful before a broad job search.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_find_alternative_titles
  produces:
    - alternative_titles_report
  tier: 0
---

# alternative-titles

Heuristic synonym + seniority expansion. LLM-side refinement
recommended for novel roles.

## When to invoke

- Before a job search to maximize recall
- When owner uses an unfamiliar job-title convention

## Inputs

```yaml
query: "<original role title>"
```

## Workflow

```yaml
steps:
  - id: expand
    tool: career_find_alternative_titles
    args: { query: "<query>" }
    tier: 0
```

## Output structure

```yaml
alternative_titles_report:
  query: "<echo>"
  alternative_titles:
    - "<expanded title>"
    - "<expanded title>"
  caveat: "Heuristic; LLM refinement recommended for novel roles."
```

## Constraints

- Always emit `caveat`.
- Always include original query in `alternative_titles`.
- Never add titles outside the registered synonym map without LLM refinement.

## Anti-patterns

- Do NOT invent role titles from your own prior.
- Do NOT mix seniority levels silently (preserve junior/mid/senior separation).
