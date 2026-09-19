---
name: "paper-analysis"
description: "Analyze a single paper from a DOI / arXiv ID / S2 paper ID. Extract metadata, methodology, claims, and limitations. Outputs structured analysis card."
metadata:
  type: "workflow"
  layer: "research-academic"
  consumes:
    - research_fetch
    - research_grade_evidence
  produces:
    - paper_card
  tier: "0"
---

# paper-analysis

Deep-dive workflow for a single paper. Use when the user provides an
identifier or references one specific work.

## When to invoke

- User says "analyze this paper", "what does this paper say", "summarize
  arXiv:XXXX.YYYYY"
- User shares a DOI or URL

## Workflow

```yaml
steps:
  - id: fetch_openalex
    tool: research_fetch
    args:
      identifier: "<doi or id>"
      source: openalex
    tier: 0
  - id: fetch_arxiv
    tool: research_fetch
    args:
      identifier: "<arxiv id>"
      source: arxiv
    tier: 0
  - id: fetch_crossref
    tool: research_fetch
    args:
      identifier: "<doi>"
      source: crossref
    tier: 0
  - id: fetch_s2
    tool: research_fetch
    args:
      identifier: "<s2 id or doi>"
      source: semantic_scholar
    tier: 0
  - id: grade
    tool: research_grade_evidence
    depends_on: [fetch_openalex, fetch_arxiv, fetch_crossref, fetch_s2]
    tier: 0
  - id: synthesize
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [grade]
```

## Output structure

```yaml
paper_card:
  identifiers:
    doi: "<string | null>"
    arxiv: "<string | null>"
    openalex: "<string | null>"
    s2: "<string | null>"
    pmid: "<string | null>"
  title: "<string>"
  authors: ["..."]
  year: <int | null>
  venue: "<string | null>"
  methodology: "<2-3 sentence summary>"
  claims:
    - claim: "<quoted or paraphrased>"
      evidence_strength: strong | moderate | weak | uncertain
  limitations:
    - "<noted by synthesis or surfaced by contradiction-hunter>"
  citation: "<formatted citation string>"
  source_consistency:
    - source: openalex | arxiv | crossref | s2
      agrees: true | false
      drift: "<if any>"
```

## Note on workflow steps

Steps marked `tool: agent_synthesis (LLM-side, not an MCP tool)` are
performed by the orchestrator/agent itself, not by an MCP tool call.
Only `research_fetch`, `research_grade_evidence`, and the registered
research v2 tools are actual MCP tools. Skill invocations (e.g.
`contradiction-hunter`, `research-critic`) are also LLM-side — they are
followed as workflow guidance, not invoked as MCP tool calls.

## Constraints

- Fetch from at least 2 independent sources for cross-validation.
- Mark `source_consistency.drift = true` when sources disagree on metadata
  (year, author, title).
- Surface limitations even when the paper does not list them.

## Anti-patterns

- Do NOT generate a card from a single source.
- Do NOT paraphrase the abstract as the methodology section.
- Do NOT skip the grader.
