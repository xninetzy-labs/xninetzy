---
name: literature-review
description: Compose a structured literature review across academic sources. Decomposes
  a topic into sub-questions, calls research_search + research_fetch per sub-question,
  then grades + synthesizes.
metadata:
  type: workflow
  layer: research-academic
  consumes: '["research-planner","source-selector","research_search","research_fetch","evidence-grader","research-critic"]'
  produces: '["literature_review"]'
  tier: '0'
---


# literature-review

End-to-end workflow for producing a structured literature review on a topic.
This skill is **not** factual evidence — it is the orchestration procedure.

## When to invoke

- User asks "literature review", "survey", "state of the art", "what's known
  about X"
- Topic spans multiple sub-questions
- User wants citations, not just a snippet

## Workflow

```yaml
steps:
  - id: decompose
    tool: research-planner (skill — LLM-side, not an MCP tool)
    input: { topic: "<user topic>" }
    output: { sub_questions: ["...", "..."] }
  - id: search_per_subq
    tool: research_search
    args:
      intent: paper
      query: "<sub-question N>"
      limit: 10
    depends_on: [decompose]
    tier: 0
  - id: grade_evidence
    tool: research_grade_evidence
    depends_on: [search_per_subq]
    tier: 0
  - id: critic_pass
    tool: research-critic (skill — LLM-side, not an MCP tool)
    depends_on: [grade_evidence]
```

## Output structure

```yaml
literature_review:
  topic: "<echo>"
  sub_questions: [...]
  references:
    - title, url, citation, identifiers, evidence_grade
  themes:
    - theme: "<name>"
      papers: ["<id>", "<id>"]
      summary: "<paragraph>"
  gaps:
    - "<open question surfaced>"
  critic_verdict: ship | revise | insufficient
```

## Constraints

- Always include at least 2 independent sources per claim.
- Always run `evidence-grader` before writing themes.
- Always run `research-critic` before delivery.
- Cap at 30 references per sub-question to keep the review focused.

## Anti-patterns

- Do NOT include `weak` or `uncertain` grade references in the final
  synthesis without an explicit caveat.
- Do NOT skip the critic pass even on "quick" reviews.
- Do NOT cite the same paper across multiple themes unless the paper actually
  addresses both.

## Note on workflow steps

Steps marked `(skill — LLM-side, not an MCP tool)` are performed by the
orchestrator/agent itself. Only `research_search`, `research_fetch`,
`research_compare_sources`, and `research_grade_evidence` are actual MCP
tools in the registry. Skill invocations (e.g. `research-planner`,
`research-critic`, `evidence-grader`) are workflow guidance the agent
follows between MCP tool calls — not MCP tool calls themselves.
