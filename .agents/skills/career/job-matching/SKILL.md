---
name: job-matching
description: Score job postings against an owner profile (skills, experience, preferences). Surfaces ranked matches with reasoning.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - memory_add
  produces:
    - job_match_report
  tier: 0
---

# job-matching

Match postings to owner profile. Reads profile from `memory_add` (or
ad-hoc input) and postings from `career_search_jobs`.

## When to invoke

- Owner asks "which of these jobs suit me?"
- After `job-search` returns a long list

## Inputs

```yaml
profile:
  skills: ["python", "rust", "postgres"]
  years_experience: int
  preferences:
    work_mode: remote | hybrid | onsite
    willing_to_relocate: bool
    min_salary_usd: int | null
postings_source: career_search_jobs | inline_list
```

## Workflow

```yaml
steps:
  - id: fetch_profile
    tool: memory_get_context
    args: { chat_id: "<owner>" }
    tier: 0
  - id: score_each
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [fetch_profile]
```

## Output structure

```yaml
job_match_report:
  matches:
    - posting_id: "<id>"
      match_score: 0.0-1.0
      skill_overlap: ["..."]
      skill_gap: ["..."]
      reasoning: "<short>"
  total_postings: <int>
  total_matches: <int>
```

## Constraints

- Always cite the posting source and ID.
- Always separate `skill_overlap` from `skill_gap`.
- Never rank without per-posting reasoning.

## Anti-patterns

- Do NOT bias toward familiar companies.
- Do NOT score on demographics, age, or location.
