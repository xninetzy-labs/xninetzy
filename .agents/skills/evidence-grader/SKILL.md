---
name: "evidence-grader"
description: "Assign evidence strength to a list of SourceRecord items. Considers primary source, peer-review signals, freshness, independence, and confidence metadata."
metadata:
  type: "meta"
  layer: "research-orchestration"
  consumes:
    - research_search
    - research_fetch
  produces:
    - graded_evidence
  tier: "0"
---

# evidence-grader

Assign a qualitative strength label and numeric score to each source record
in a research result set. Pure function over `SourceRecord` objects.

## When to invoke

- After `research_search` or `research_fetch` returns records
- Before `research_compare_sources` merges across providers
- As the final step of a research plan before synthesis

## Inputs

```yaml
records:
  - <SourceRecord>
grading_policy:
  prefer_open_access: bool
  freshness_days: int | null
  min_independent_sources: int (default 2)
```

## Output schema

```yaml
graded:
  - record: <SourceRecord>
    grade: strong | moderate | weak | uncertain
    score: 0.0-1.0
    reasons:
      - "<human-readable reason>"
```

## Grading rubric

| Signal | Score delta |
|---|---|
| `primary_source == True` | +0.20 |
| `identifiers.doi` present | +0.10 |
| `identifiers.arxiv` present | +0.05 |
| `published_at` within `freshness_days` | +0.10 |
| `license` present and open | +0.05 |
| `author` present and not anonymous | +0.05 |
| Confidence metadata missing | -0.10 |
| `snippet` empty | -0.10 |

Grade bands:

| Score | Grade |
|---|---|
| >= 0.75 | strong |
| >= 0.50 | moderate |
| >= 0.25 | weak |
| < 0.25 | uncertain |

## Composition

After grading, count `strong` + `moderate` records. If
`count < min_independent_sources`, flag the result set as
`insufficient_evidence` rather than synthesizing.
