---
name: xninetzy-deep-research
description: Run source-grounded, multi-round, multi-agent deep research with papers, web sources, context, videos, and evidence auditing.
metadata:
  owner: xninetzy
  version: "1.1.0"
---

# Xninetzy Deep Research

## Manifest

```yaml
research_question:
personal_context:
scope:
subquestions:
queries:
databases:
year_range:
inclusion:
exclusion:
source_hierarchy:
worker_assignments:
deliverable:
```

## Tooling

Use shared Xninetzy registry tools; they behave identically on WhatsApp,
CLI, and MCP:

* `research_search_papers(query, sources="arxiv,crossref", max_results)` — free
  academic discovery; no API key needed.
* `research_get_paper(identifier, source="auto", ingest=False)` — metadata for a
  DOI or arXiv ID/URL; set `ingest=true` to store title+abstract into the
  knowledge base.
* `research_download_paper(identifier)` — legal open-access PDF only (arXiv or
  CrossRef OA links). Sci-Hub is never used.
* `web_search`, `youtube_search` — supplementary context and lectures.
* `research_light(topic)` — quick cross-source orientation before committing to
  a full pipeline.
* `research_generate_brief(topic)` — deterministic brief skeleton with real
  collected sources; use as the starting draft, then deepen manually.

Tool failures follow the error contract `❌ [CODE] message`. Parse the code and
adapt: `NOT_FOUND` → refine identifier/query; `INVALID_INPUT` → fix arguments
(check `Nilai valid:` hint); `NOT_CONFIGURED` → run the prerequisite sync/setup;
`POLICY_HELD` → stop and request approval; never retry blindly.

Mutating calls accept `idempotency_key`; always pass a stable key when a retry
is possible so duplicates are impossible.

## Search rounds

Round 1:

* map terminology;
* find foundational evidence;
* find recent evidence;
* identify major viewpoints.

Round 2:

* close evidence gaps;
* verify important claims;
* find conflicting evidence;
* inspect strongest sources.

Continue only when a major subquestion remains weak.

## Source hierarchy

1. original research;
2. official institutions;
3. systematic reviews;
4. official repositories;
5. reputable technical publications;
6. secondary summaries.

YouTube is supplementary.

## Access labels

* full text;
* abstract;
* metadata;
* web page;
* search snippet;
* video/transcript.

## Audit

Verify:

* claim-source alignment;
* no invented metadata;
* conflict represented;
* source quality;
* inference labeled;
* personal and external evidence separated.

## Persistence

Store:

* manifest;
* source ledger;
* selected claims;
* unresolved gaps;
* synthesis;
* checkpoint.
