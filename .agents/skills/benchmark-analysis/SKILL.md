---
name: benchmark-analysis
description: Find and compare benchmarks used in academic papers for a given task. Surfaces the most-cited benchmarks, dataset links, and evaluation protocols.
metadata:
  type: workflow
  layer: research-academic
  consumes:
    - research_search
    - research_fetch
    - evidence-grader
  produces:
    - benchmark_landscape
  tier: 0
---

# benchmark-analysis

Identify and compare benchmarks for a specific task. Builds a landscape view
of how a research problem is evaluated across the literature.

## When to invoke

- User asks "what benchmarks exist for X", "how is X evaluated",
  "what dataset should I use for X"
- Topic implies empirical ML/AI evaluation

## Workflow

```yaml
steps:
  - id: search_papers
    tool: research_search
    args:
      intent: paper
      query: "<task> benchmark evaluation"
      limit: 20
    tier: 0
  - id: grade
    tool: research_grade_evidence
    depends_on: [search_papers]
    tier: 0
  - id: aggregate_benchmarks
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [grade]
```

## Output structure

```yaml
benchmark_landscape:
  task: "<echo>"
  benchmarks:
    - name: "<e.g. MMLU>"
      aliases: ["..."]
      first_introduced: <int | null>
      most_cited_paper: "<title + id>"
      source_consistency: <int>
      evaluation_protocol: "<summary>"
      dataset_size: <int | null>
      license: "<string | null>"
  recommended_for_owner:
    - name: "<benchmark name>"
      reason: "<why>"
```

## Note on workflow steps

Steps marked `tool: agent_synthesis (LLM-side, not an MCP tool)` are
performed by the orchestrator/agent itself, not by an MCP tool call.
Only `research_search`, `research_fetch`, and the registered research v2
tools are actual MCP tools. To fetch the originating paper for each
benchmark (per Constraints), add `research_fetch` steps keyed by
`most_cited_paper` IDs surfaced from the search step.

## Constraints

- Cite the originating paper for each benchmark.
- Surface at least 3 distinct benchmarks when available.
- Note license + dataset size when surfaced.

## Anti-patterns

- Do NOT include benchmarks that no source actually evaluates on.
- Do NOT recommend without surfacing the limitation.
- Do NOT conflate leaderboard with benchmark.
