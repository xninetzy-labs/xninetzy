# Xninetzy Deep Research — Rounds, Sources, and Tools

This reference expands search strategy, search rounds, the research stopping rule, source hierarchy, source types, access labels, tooling, tool error handling, and mutation safety. Read it when designing a research campaign.

## Research is not search

Search results are discovery material. They are not automatically evidence.

The system must distinguish:

```text
query
  ↓
candidate source
  ↓
source inspection
  ↓
evidence extraction
  ↓
claim verification
  ↓
synthesis
```

Do not treat a search snippet as equivalent to reading the underlying source.

## Subquestion decomposition

Break complex questions into answerable subquestions:

```text
Main Question
│
├── Definition / terminology
├── Mechanism
├── Evidence of effectiveness
├── Alternatives
├── Limitations
├── Context-specific applicability
├── Risks
└── Practical recommendation
```

Each important conclusion should map back to at least one subquestion.

## Search strategy

Build multiple search queries rather than relying on one formulation. Query families:

* **Terminology** — definitions and competing terminology.
* **Foundational** — seminal or foundational evidence.
* **Current** — recent research and current practice.
* **Comparative** — competing approaches.
* **Critical** — limitations and negative evidence.
* **Context-specific** — evidence applicable to the user's actual environment.

## Search rounds

### Round 1 — Landscape

Goals:

* map terminology,
* locate foundational sources,
* find recent evidence,
* identify major viewpoints,
* discover likely debates,
* identify candidate primary sources.

Do not attempt exhaustive verification yet.

### Round 2 — Evidence Closure

Goals:

* close important evidence gaps,
* verify major claims,
* inspect strongest sources,
* seek contradictory evidence,
* test whether initial conclusions survive scrutiny.

### Round 3 — Targeted Investigation

Continue only when a major unresolved question remains. Examples:

* conflicting findings,
* unclear causality,
* unusual domain,
* critical missing evidence,
* methodological disagreement.

Do not perform additional search merely to increase citation count.

## Research stopping rule

Research can stop when:

* all important subquestions have sufficient evidence,
* major claims have supporting sources,
* important contradictions have been investigated,
* critical source-quality concerns are resolved,
* the remaining uncertainty is explicitly documented.

A large number of sources is not itself a stopping criterion.

## Source hierarchy

Default priority:

1. original research,
2. official institutions and primary documentation,
3. systematic reviews/meta-analyses,
4. official repositories and datasets,
5. reputable technical publications,
6. high-quality secondary analysis,
7. general summaries.

Use lower-level sources when they provide context unavailable elsewhere, but do not silently treat them as equivalent to primary evidence.

## Source types

Classify each source:

```text
academic paper
systematic review
official document
official dataset
technical documentation
reputable publication
news/reporting
video/lecture
secondary summary
search result
```

Source type affects confidence and interpretation.

## Access labels

Every important source should have an access state:

```text
full_text
abstract
metadata
web_page
search_snippet
video
transcript
```

Do not claim that a full paper was reviewed when only its abstract was accessible.

## Tooling

Use available research tools according to their intended role.

### Academic discovery

`research_search_papers(query, sources="arxiv,crossref", max_results)` — use for academic discovery.

### Paper metadata

`research_get_paper(identifier, source="auto", ingest=false)` — use to verify paper identity and metadata.

### Legal open-access retrieval

`research_download_paper(identifier)` — use only when a legal open-access PDF is available. Never use unlawful paper retrieval methods.

### Web research

`web_search` — use for current context, official information, non-academic material, and supplementary evidence.

### Video research

`youtube_search` — use for lectures, demonstrations, interviews, talks, and supplementary context. YouTube should generally remain supplementary to stronger evidence where applicable.

### Rapid orientation

`research_light(topic)` — use when a quick evidence landscape is useful before deciding whether full research is warranted.

### Structured research skeleton

`research_generate_brief(topic)` — use as a starting structure based on collected sources, then verify and deepen manually.

## Tool error handling

Research tools may return structured errors. Interpret codes explicitly:

### NOT_FOUND

Refine the query or identifier.

### INVALID_INPUT

Correct the arguments using the available validation hint.

### NOT_CONFIGURED

Perform the required setup/sync when supported.

### POLICY_HELD

Stop and request the necessary approval.

Never retry blindly.

## Mutation safety

When a research tool changes persistent state:

* use a stable `idempotency_key` when supported,
* prevent duplicate ingestion,
* distinguish proposed mutation from completed mutation,
* verify the resulting state.

Examples: paper ingestion, knowledge-base writes, research checkpoint persistence.

## Video research

Videos can provide demonstrations, lectures, interviews, expert explanations, and implementation walkthroughs. For important claims, identify the speaker, title, date, context, and transcript or relevant segment when available. Treat videos as supplementary unless the video itself is the primary source.

## Current-fact verification

When a claim may have changed after the model's knowledge horizon, verify it through current web research or current authoritative documentation. Examples include current software versions, product specifications, regulations, prices, current institutional leadership, active APIs, and current academic policies. Do not rely on historical memory when current verification is material.

## Recency

For rapidly changing topics, prioritize recent evidence: software frameworks, AI model capabilities, cloud services, cybersecurity, regulations, market conditions, current products. For foundational concepts, older sources may remain authoritative. Recency should be judged relative to the research question.