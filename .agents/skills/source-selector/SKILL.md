---
name: "source-selector"
description: "Pick which source adapters to query for a given intent. Pure logic, no LLM. Maps research intent to the available adapter registry."
metadata:
  type: "meta"
  layer: "research-orchestration"
  consumes:
    - xninetzy.os.research.router
  produces:
    - source_list
  tier: "0"
---

# source-selector

Workflow guidance for choosing source adapters. The actual selection is
pure logic in `xninetzy/os/research/router.py` — this skill describes when
to call it and how to interpret results.

## When to invoke

- Before any `research_search` or `research_fetch` call
- When `research-planner` produces a multi-intent plan
- When user explicitly limits to a subset of sources

## Decision flow

1. Classify intent into one of: `paper | code | dataset | news | company |
   model | benchmark | security | patent | economics | geographic | entity |
   general`.
2. Call `route_by_name(intent, requires_open_access=..., language=...,
   freshness_days=...)`.
3. If returned list is empty AND the intent is in the planned set, **defer
   the step** (do not invent an unsupported source).
4. If the user wants a paid provider (Crunchbase, Product Hunt, etc.), surface
   it as out-of-scope unless the corresponding env var is set.

## Output

```yaml
sources:
  - id: <adapter id>
    category: <matches SourceCategory>
    free: <true | false>
```

Example for `intent=paper`:

```yaml
sources:
  - id: openalex
    category: paper
    free: true
  - id: arxiv
    category: paper
    free: true
  - id: crossref
    category: paper
    free: true
```

## Cross-source confirmation

For academic claims requiring evidence strength, the selector should pick
**at least two** independent sources (no shared identifier space).
Currently OpenAlex, arXiv, Crossref, Semantic Scholar, and PubMed all
expose DOI as a join key but differ in coverage: OpenAlex is the broadest
graph, Crossref the bibliographic backbone, arXiv the preprint-only
stream, Semantic Scholar the citation-rich view, PubMed the biomedical
slice. Treat as independent for confirmation — never collapse to one
source even when identifiers overlap.

## Out-of-scope intents (current state)

After multi-slice rollout, the registry currently has live adapters for
all categories except `company` (paid-only providers such as Crunchbase
and PitchBook are excluded by design). Categories with adapters:

| Intent | Sources |
|---|---|
| `paper` | openalex, arxiv, crossref, semantic_scholar, pubmed |
| `code` | github |
| `dataset` | huggingface, zenodo, kaggle |
| `news` | hackernews, reddit, rss |
| `model` | huggingface |
| `benchmark` | papers_with_code, open_llm_leaderboard |
| `security` | nvd |
| `patent` | patentsview |
| `economics` | world_bank, fred, bps |
| `geographic` | osm |
| `entity` | wikidata, dbpedia |
| `general` | stackoverflow, wayback |
| `company` | (none — paid-only; surface as out-of-scope) |

When the caller asks for a paid-only category, the selector must surface
"no adapter" rather than silently fallback to web search.
