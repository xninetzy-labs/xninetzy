---

...

...
name: "xninetzy-deep-research"
description: "Source-grounded deep-research operating system for complex research questions requiring multi-round discovery, evidence synthesis, academic papers, official sources, web research, videos, personal context, claim auditing, contradiction analysis, provenance tracking, and reusable research memory. Use for deep research, literature review, comparative analysis, fact-checking, and current-fact verification where evidence integrity matters."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "frame -> orient -> decompose -> search -> triage -> verify -> contrast -> synthesize -> audit -> persist -> deliver"
...

# Xninetzy Deep Research OS

This skill is a reusable operating system for conducting **complex, evidence-grounded research**. It is designed for questions where a normal search or single-source answer is insufficient.

The system should produce research that is:

**traceable, source-aware, current when necessary, contradiction-sensitive, reproducible, and honest about uncertainty.**

The canonical lifecycle is:

**Frame → Orient → Decompose → Search → Triage → Verify → Contrast → Synthesize → Audit → Persist → Deliver**

## Core principles

* **Research is not search.** Search results are discovery material, not evidence. The system must distinguish query → candidate source → source inspection → evidence extraction → claim verification → synthesis. Do not treat a search snippet as equivalent to reading the underlying source.
* **Claims require evidence.** For important claims, the system should answer: What is the claim? Which source supports it? What part of the source supports it? How strong is the evidence? Is the claim direct evidence or inference?
* **Uncertainty is part of the result.** A strong research answer does not hide uncertainty. Represent: established, well_supported, mixed, uncertain, insufficient_evidence, contradicted. Do not force a conclusion simply because the user expects a definitive answer.

## When to use

* multi-source research with provenance and audit trail;
* literature or systematic-style review;
* comparative or technical analysis requiring structured evidence;
* fact-checking where sources can disagree;
* current-fact verification for software, policies, regulations, prices, leadership, or APIs.

## When NOT to use

* a single stable fact lookup;
* casual brainstorming or open-ended exploration;
* reading one supplied document unless cross-source synthesis is requested.

## Core workflow

1. **Frame.** Write the research question, scope, evidence standard, deliverable, freshness requirement, decision context, and intended audience.
2. **Orient.** Run a lightweight landscape pass to map terminology, foundational sources, recent evidence, major viewpoints, and likely debates before deep collection.
3. **Decompose.** Break the question into 5–12 answerable subquestions spanning descriptive, comparative, evaluative, implementation, risk, ethics, and gap concerns.
4. **Search.** Build multiple query families: terminology, foundational, current, comparative, critical, and context-specific. Do not rely on one formulation.
5. **Triage.** For each candidate source, assess relevance, authority, method quality, recency, accessibility, and independence. Do not keep weak sources merely because they are convenient.
6. **Verify.** Inspect the strongest sources directly. Mark access level (full_text, abstract, metadata, web_page, search_snippet, video, transcript). Never claim a full paper was reviewed when only its abstract was accessible.
7. **Contrast.** When credible sources disagree, preserve both sides, identify why they may differ, inspect populations, methods, measurements, and dates, and retain residual uncertainty. Do not hide disagreement to produce a cleaner narrative.
8. **Synthesize.** Answer the research question rather than summarize the browsing process. Structure the synthesis around Question → Key Findings → Evidence → Contradictions/Limitations → Contextual Interpretation → Conclusion → Recommendation/Decision.
9. **Audit.** Verify claim-source alignment, metadata, contradictions, inference vs finding, source quality, freshness, and personal-vs-external evidence separation before delivery.
10. **Persist.** Save manifest, source ledger, claim ledger, unresolved gaps, synthesis, and checkpoint when persistence is required.
11. **Deliver.** Return the research question, scope, evidence status, key findings, conflicts/limitations, confidence, research gaps, recommendation/decision, persistence status, and next action.

## Research manifest

Every substantial research process should begin with a structured manifest:

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
decision_context:
freshness_requirement:
evidence_standard:
```

For deep research, avoid beginning without a clear research question and scope.

## Search rounds

### Round 1 — Landscape

Map terminology, locate foundational sources, find recent evidence, identify major viewpoints, discover likely debates, and identify candidate primary sources. Do not attempt exhaustive verification yet.

### Round 2 — Evidence Closure

Close important evidence gaps, verify major claims, inspect strongest sources, seek contradictory evidence, and test whether initial conclusions survive scrutiny.

### Round 3 — Targeted Investigation

Continue only when a major unresolved question remains. Do not perform additional search merely to increase citation count.

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

Classify each source: academic paper, systematic review, official document, official dataset, technical documentation, reputable publication, news/reporting, video/lecture, secondary summary, or search result. Source type affects confidence and interpretation.

## Tooling

Use available research tools according to their intended role:

* **Academic discovery** — `research_search_papers(query, sources="arxiv,crossref", max_results)`.
* **Paper metadata** — `research_get_paper(identifier, source="auto", ingest=false)`.
* **Legal open-access retrieval** — `research_download_paper(identifier)` only when a legal open-access PDF is available. Never use unlawful paper retrieval methods.
* **Web research** — `web_search` for current context, official information, non-academic material, and supplementary evidence.
* **Video research** — `youtube_search` for lectures, demonstrations, interviews, talks, and supplementary context. YouTube should generally remain supplementary to stronger evidence where applicable.
* **Rapid orientation** — `research_light(topic)` when a quick evidence landscape is useful.
* **Structured research skeleton** — `research_generate_brief(topic)` as a starting structure, then verify and deepen manually.

## Tool error handling

Interpret codes explicitly:

* `NOT_FOUND` — refine the query or identifier.
* `INVALID_INPUT` — correct arguments using the available validation hint.
* `NOT_CONFIGURED` — perform required setup/sync when supported.
* `POLICY_HELD` — stop and request approval.

Never retry blindly.

## Mutation safety

When a research tool changes persistent state:

* use a stable `idempotency_key` when supported,
* prevent duplicate ingestion,
* distinguish proposed mutation from completed mutation,
* verify the resulting state.

Examples: paper ingestion, knowledge-base writes, research checkpoint persistence.

## Evidence ledger

Maintain a structured ledger for important sources:

```text
source_id
citation
source_type
access_level
publication_date
research_question
subquestion
key_claims
evidence
limitations
conflicts
quality
status
```

The ledger is not the final answer; it is the audit layer beneath it.

## Claim ledger

For important claims, maintain:

```text
claim_id
claim
supporting_sources
contradicting_sources
evidence_strength
direct_or_inferred
scope
caveats
status
```

This prevents unsupported statements from entering the synthesis.

## Claim-source alignment

Audit every major conclusion for alignment. Ask:

> Does the cited source actually support the claim as written?

Common failures include source supports a narrower claim than the text, observational evidence presented as causality, one study generalized to all populations, source reports possibility presented as fact, abstract-only access treated as full evidence. When necessary, narrow the wording.

## Direct evidence vs inference

Mark the difference:

* **Direct evidence** — A study found X under conditions Y.
* **Inference** — These findings suggest X may also be useful in context Z.

Do not phrase the second as though the study directly tested context Z.

## Causal reasoning

Be particularly careful with causal language. Distinguish associated with, correlated with, predicts, is consistent with, suggests, may contribute to, causes. Do not upgrade association to causation without appropriate evidence.

## Research agents / workers

For complex research, divide work by evidence function rather than arbitrary topic duplication.

Example:

```text
Worker A: Foundational research
Worker B: Recent papers
Worker C: Official/institutional evidence
Worker D: Contradictory evidence
Worker E: Practical implementation evidence
Worker F: Context-specific evidence
```

Each worker should return sources, claims, evidence, uncertainties, and unresolved gaps. Avoid multiple workers independently searching the same broad query without a distinct purpose.

## Worker assignment contract

Each worker assignment should specify:

```yaml
objective:
subquestion:
source_priority:
time_range:
expected_evidence:
exclusions:
deliverable:
```

This makes parallel research combinable.

## Parallel research integration

When multiple workers contribute:

1. normalize source identities,
2. deduplicate sources,
3. merge compatible findings,
4. detect contradictions,
5. assess evidence strength,
6. identify gaps,
7. synthesize only after reconciliation.

Do not average conflicting conclusions mechanically.

## Personal context integration

When user-specific context matters:

```text
External Evidence
+
Personal / Project Context
↓
Contextual Interpretation
↓
Recommendation
```

Keep the distinction visible.

## Research-to-decision mapping

When research exists to support a decision, define decision, options, criteria, evidence, tradeoffs, uncertainty, and recommendation. The research should be judged by whether it enables a defensible decision.

## Research-to-roadmap integration

When connected to the Learning OS:

```text
Research Finding
   ↓
Concept / Principle
   ↓
Learning Need
   ↓
Roadmap Milestone
   ↓
Practice Task
   ↓
Evidence
```

Only make the relationship when explicitly justified.

## Research deliverables

Possible outputs:

* **Research brief** — question, findings, evidence, limitations, next decision.
* **Evidence review** — claim-by-claim source analysis.
* **Literature review** — structured synthesis of academic evidence.
* **Technical comparison** — alternatives, benchmarks, trade-offs, recommendation.
* **Decision memo** — question, options, criteria, evidence, recommendation.
* **Deep research report** — comprehensive synthesis with source and claim audit.

The deliverable should match the research objective.

## Citation integrity

For each external factual claim: provide an appropriate source, cite at the source at the claim level where practical, avoid citation dumping at the end of unrelated paragraphs, and do not cite a source that was not actually consulted. Preserve the required citation/provenance format.

## No invented metadata

Never invent DOI, title, author, publication date, journal, dataset name, URL, page number, quote, or study result. When metadata cannot be verified, label it unknown.

## Quote policy

Use direct quotations sparingly. Prefer paraphrasing unless exact wording is important. When quoting, preserve wording accurately, identify source, avoid taking statements out of context, and follow applicable quotation limits.

## Research gaps

Explicitly record unresolved gaps:

```text
gap_id
question
why_it_matters
evidence_attempted
current_status
next_research_action
```

A research gap is not a failure. It is a result that should be communicated honestly.

## Research confidence

For major conclusions, use qualitative confidence: high, moderate, low, unknown. Base confidence on evidence quality, source agreement, directness, relevance, recency, and reproducibility. Do not interpret confidence as statistical probability unless a quantitative model actually exists.

## Routing

* Learning continuity → `it-learning`.
* Research state persistence → `xninetzy-research-memory`.
* Graph relationships → `graph-rag`.
* Cross-session continuity → `xninetzy-memory`.
* Generic knowledge lookup → `xninetzy-knowledge-answer`.

## Reference map

* `references/rounds-and-tools.md` — search strategy, search rounds, research stopping rule, source hierarchy, source types, access labels, tooling, tool error handling, and mutation safety.
* `references/synthesis-and-audit.md` — source triage, evidence ledger, claim ledger, claim-source alignment, direct vs inference, causal reasoning, conflicting evidence, evidence weighting, recency, current-fact verification, video research, and research agents.
* `references/output-and-persistence.md` — research-to-decision mapping, research-to-roadmap, graph integration, deliverables, citation integrity, no invented metadata, quote policy, research gaps, confidence, audit, persistence, evidence matrix, research stopping test, completion contract, and operating rules.

## Operating rules

The system must:

* define the question before searching,
* decompose complex questions into subquestions,
* use multiple search rounds when warranted,
* prioritize primary and authoritative evidence,
* distinguish discovery from verified evidence,
* track access level,
* audit claim-source alignment,
* represent conflicting evidence,
* label inference as inference,
* separate personal context from external evidence,
* verify time-sensitive facts,
* never invent research metadata,
* use legal sources only,
* use idempotency for persistent mutations,
* persist enough state to resume without repeating completed work.

The objective is not to find the largest number of sources. It is to produce the **most defensible answer supported by the strongest available evidence, with uncertainty and reasoning made explicit enough for another person to audit and continue the research.**