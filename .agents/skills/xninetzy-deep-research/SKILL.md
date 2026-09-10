# Xninetzy Deep Research OS

```yaml
---
name: xninetzy-deep-research
description: General-purpose, source-grounded deep-research operating system for complex research questions requiring multi-round discovery, evidence synthesis, academic papers, official sources, web research, videos, personal context, claim auditing, contradiction analysis, provenance tracking, and reusable research memory. Supports rapid orientation, research decomposition, parallel source collection, evidence grading, synthesis, gap analysis, and reproducible research deliverables.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "frame -> orient -> decompose -> search -> triage -> verify -> contrast -> synthesize -> audit -> persist -> deliver"
---
```

# Xninetzy Deep Research OS

This skill is a reusable operating system for conducting **complex, evidence-grounded research**.

It is designed for questions where a normal search or single-source answer is insufficient.

The system should produce research that is:

**traceable, source-aware, current when necessary, contradiction-sensitive, reproducible, and honest about uncertainty.**

The canonical lifecycle is:

**Frame → Orient → Decompose → Search → Triage → Verify → Contrast → Synthesize → Audit → Persist → Deliver**

---

# 1. Research Philosophy

## 1.1 Research is not search

Search results are discovery material.

They are not automatically evidence.

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

---

## 1.2 Claims require evidence

For important claims, the system should be able to answer:

**What is the claim?**

**Which source supports it?**

**What part of the source supports it?**

**How strong is the evidence?**

**Is the claim direct evidence or inference?**

---

## 1.3 Uncertainty is part of the result

A strong research answer does not hide uncertainty.

Represent:

```text
established
well_supported
mixed
uncertain
insufficient_evidence
contradicted
```

Do not force a conclusion simply because the user expects a definitive answer.

---

# 2. Research Manifest

Every substantial research process should begin with a structured manifest.

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

Not every field must be present for a small research task.

For deep research, avoid beginning without a clear research question and scope.

---

# 3. Research Question

A strong research question should define:

* topic,
* decision or explanation needed,
* relevant population/system/context,
* time range when relevant,
* desired depth.

Weak:

> "Tell me about RAG."

Better:

> "What retrieval and evaluation strategies most reliably improve factuality in production RAG systems, based on research and current engineering evidence from 2023–2026?"

The question should make it possible to determine when research is complete.

---

# 4. Personal Context

Personal context may include information that materially changes the research.

Examples:

* user's technical level,
* project architecture,
* course requirements,
* target environment,
* geographic context,
* decision constraints,
* budget,
* existing stack.

Separate:

**personal/project evidence**

from:

**external research evidence**.

Never allow personal context to masquerade as external evidence.

---

# 5. Scope

Explicitly define:

### In scope

What the research must investigate.

### Out of scope

What does not need to be covered.

### Time range

Relevant publication period.

### Geography

Country, city, region, or global context when relevant.

### Population/system

Who or what the evidence concerns.

Scope prevents research from expanding indefinitely.

---

# 6. Subquestion Decomposition

Break complex questions into answerable subquestions.

Example:

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

---

# 7. Search Strategy

Build multiple search queries rather than relying on one formulation.

Query families may include:

### Terminology

Identify definitions and competing terminology.

### Foundational

Find seminal or foundational evidence.

### Current

Find recent research and current practice.

### Comparative

Find competing approaches.

### Critical

Find limitations and negative evidence.

### Context-specific

Find evidence applicable to the user's actual environment.

---

# 8. Search Rounds

## Round 1 — Landscape

Goals:

* map terminology,
* locate foundational sources,
* find recent evidence,
* identify major viewpoints,
* discover likely debates,
* identify candidate primary sources.

Do not attempt exhaustive verification yet.

---

## Round 2 — Evidence Closure

Goals:

* close important evidence gaps,
* verify major claims,
* inspect strongest sources,
* seek contradictory evidence,
* test whether initial conclusions survive scrutiny.

---

## Round 3 — Targeted Investigation

Continue only when a major unresolved question remains.

Examples:

* conflicting findings,
* unclear causality,
* unusual domain,
* critical missing evidence,
* methodological disagreement.

Do not perform additional search merely to increase citation count.

---

# 9. Research Stopping Rule

Research can stop when:

* all important subquestions have sufficient evidence,
* major claims have supporting sources,
* important contradictions have been investigated,
* critical source-quality concerns are resolved,
* the remaining uncertainty is explicitly documented.

A large number of sources is not itself a stopping criterion.

---

# 10. Source Hierarchy

Default priority:

1. original research,
2. official institutions and primary documentation,
3. systematic reviews/meta-analyses,
4. official repositories and datasets,
5. reputable technical publications,
6. high-quality secondary analysis,
7. general summaries.

Use lower-level sources when they provide context unavailable elsewhere, but do not silently treat them as equivalent to primary evidence.

---

# 11. Source Types

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

---

# 12. Access Labels

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

---

# 13. Tooling

Use available research tools according to their intended role.

### Academic discovery

`research_search_papers(query, sources="arxiv,crossref", max_results)`

Use for academic discovery.

### Paper metadata

`research_get_paper(identifier, source="auto", ingest=false)`

Use to verify paper identity and metadata.

### Legal open-access retrieval

`research_download_paper(identifier)`

Use only when a legal open-access PDF is available.

Never use unlawful paper retrieval methods.

### Web research

`web_search`

Use for current context, official information, non-academic material, and supplementary evidence.

### Video research

`youtube_search`

Use for lectures, demonstrations, interviews, talks, and supplementary context.

YouTube should generally remain supplementary to stronger evidence where applicable.

### Rapid orientation

`research_light(topic)`

Use when a quick evidence landscape is useful before deciding whether full research is warranted.

### Structured research skeleton

`research_generate_brief(topic)`

Use as a starting structure based on collected sources, then verify and deepen manually.

---

# 14. Tool Error Handling

Research tools may return structured errors.

Example pattern:

```text
❌ [CODE] message
```

Interpret codes explicitly.

### NOT_FOUND

Refine the query or identifier.

### INVALID_INPUT

Correct the arguments using the available validation hint.

### NOT_CONFIGURED

Perform the required setup/sync when supported.

### POLICY_HELD

Stop and request the necessary approval.

Never retry blindly.

---

# 15. Mutation Safety

When a research tool changes persistent state:

* use a stable `idempotency_key` when supported,
* prevent duplicate ingestion,
* distinguish proposed mutation from completed mutation,
* verify the resulting state.

Examples:

* paper ingestion,
* knowledge-base writes,
* research checkpoint persistence.

---

# 16. Source Triage

For each candidate source, assess:

### Relevance

Does it answer the research question?

### Authority

How trustworthy is the publisher/author?

### Method quality

Does the evidence support the conclusion?

### Recency

Does age matter for this topic?

### Accessibility

What part of the source was actually inspected?

### Independence

Is it merely repeating another source?

Do not keep weak sources merely because they are convenient.

---

# 17. Evidence Ledger

Maintain a structured ledger for important sources.

Conceptually:

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

---

# 18. Claim Ledger

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

---

# 19. Claim-Source Alignment

Audit every major conclusion for alignment.

Ask:

> Does the cited source actually support the claim as written?

Common failures include:

* source supports a narrower claim than the text,
* observational evidence presented as causality,
* one study generalized to all populations,
* source reports possibility presented as fact,
* abstract-only access treated as full evidence.

When necessary, narrow the wording.

---

# 20. Direct Evidence vs Inference

Mark the difference.

### Direct evidence

> A study found X under conditions Y.

### Inference

> These findings suggest X may also be useful in context Z.

Do not phrase the second as though the study directly tested context Z.

---

# 21. Causal Reasoning

Be particularly careful with causal language.

Distinguish:

* associated with,
* correlated with,
* predicts,
* is consistent with,
* suggests,
* may contribute to,
* causes.

Do not upgrade association to causation without appropriate evidence.

---

# 22. Conflicting Evidence

When credible sources disagree:

1. preserve both sides,
2. identify why they may differ,
3. inspect populations, methods, measurements, and dates,
4. assess source quality,
5. determine whether one conclusion is better supported,
6. retain residual uncertainty.

Do not hide disagreement simply to produce a cleaner narrative.

---

# 23. Evidence Weighting

Evidence strength may depend on:

* methodological quality,
* sample size,
* replication,
* systematic review support,
* publication recency,
* relevance to the target context,
* consistency across independent sources.

Avoid simplistic rules such as:

> "More citations = more truth."

---

# 24. Recency

For rapidly changing topics, prioritize recent evidence.

Examples:

* software frameworks,
* AI model capabilities,
* cloud services,
* cybersecurity,
* regulations,
* market conditions,
* current products.

For foundational concepts, older sources may remain authoritative.

Recency should be judged relative to the research question.

---

# 25. Current-Fact Verification

When a claim may have changed after the model's knowledge horizon, verify it through current web research or current authoritative documentation.

Examples include:

* current software versions,
* product specifications,
* regulations,
* prices,
* current institutional leadership,
* active APIs,
* current academic policies.

Do not rely on historical memory when current verification is material.

---

# 26. Video Research

Videos can provide:

* demonstrations,
* lectures,
* interviews,
* expert explanations,
* implementation walkthroughs.

For important claims:

* identify the speaker,
* title,
* date,
* context,
* transcript or relevant segment when available.

Treat videos as supplementary unless the video itself is the primary source.

---

# 27. Research Agents / Workers

For complex research, divide work by evidence function rather than arbitrary topic duplication.

Example:

```text
Worker A:
Foundational research

Worker B:
Recent papers

Worker C:
Official/institutional evidence

Worker D:
Contradictory evidence

Worker E:
Practical implementation evidence

Worker F:
Context-specific evidence
```

Each worker should return:

* sources,
* claims,
* evidence,
* uncertainties,
* unresolved gaps.

Avoid multiple workers independently searching the same broad query without a distinct purpose.

---

# 28. Worker Assignment Contract

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

---

# 29. Parallel Research Integration

When multiple workers contribute:

1. normalize source identities,
2. deduplicate sources,
3. merge compatible findings,
4. detect contradictions,
5. assess evidence strength,
6. identify gaps,
7. synthesize only after reconciliation.

Do not average conflicting conclusions mechanically.

---

# 30. Research Synthesis

The synthesis should answer the research question, not summarize the browsing process.

A strong structure is:

```text
Question
↓
Key Findings
↓
Evidence
↓
Contradictions / Limitations
↓
Contextual Interpretation
↓
Conclusion
↓
Recommendation / Decision
```

---

# 31. Personal Context Integration

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

Example:

> Research suggests X under these conditions. Given the project's current architecture, Y is the more practical implementation.

The second statement is a contextual recommendation, not a finding from the paper.

---

# 32. Research-to-Decision Mapping

When research exists to support a decision, define:

```text
decision
options
criteria
evidence
tradeoffs
uncertainty
recommendation
```

The research should be judged by whether it enables a defensible decision.

---

# 33. Research-to-Roadmap Integration

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

---

# 34. Graph Integration

When Graph RAG is available, connect:

```text
Research Source
 → supports →
Claim
 → informs →
Concept
 → supports →
Goal / Roadmap
```

Do not turn semantic similarity into a factual graph edge.

All important graph links should remain evidence-backed.

---

# 35. Research Deliverables

Possible outputs include:

### Research brief

Question, findings, evidence, limitations, next decision.

### Evidence review

Claim-by-claim source analysis.

### Literature review

Structured synthesis of academic evidence.

### Technical comparison

Alternatives, benchmarks, trade-offs, recommendation.

### Decision memo

Question, options, criteria, evidence, recommendation.

### Deep research report

Comprehensive synthesis with source and claim audit.

The deliverable should match the research objective.

---

# 36. Citation Integrity

For each external factual claim:

* provide an appropriate source,
* cite the source at the claim level where practical,
* avoid citation dumping at the end of unrelated paragraphs,
* do not cite a source that was not actually consulted.

When web sources are used, preserve the required web citation format.

When files or research artifacts are used, preserve their applicable citation/provenance format.

---

# 37. No Invented Metadata

Never invent:

* DOI,
* title,
* author,
* publication date,
* journal,
* dataset name,
* URL,
* page number,
* quote,
* study result.

When metadata cannot be verified:

**label it unknown.**

---

# 38. Quote Policy

Use direct quotations sparingly.

Prefer paraphrasing unless exact wording is important.

When quoting:

* preserve wording accurately,
* identify source,
* avoid taking statements out of context,
* follow applicable quotation limits.

---

# 39. Research Gaps

Explicitly record unresolved gaps:

```text
gap_id
question
why_it_matters
evidence_attempted
current_status
next_research_action
```

A research gap is not a failure.

It is a result that should be communicated honestly.

---

# 40. Research Confidence

For major conclusions, use qualitative confidence:

```text
high
moderate
low
unknown
```

Base confidence on:

* evidence quality,
* source agreement,
* directness,
* relevance,
* recency,
* reproducibility.

Do not interpret confidence as statistical probability unless a quantitative model actually exists.

---

# 41. Audit Procedure

Before final delivery, perform an evidence audit.

Verify:

### Claim-source alignment

Does each important claim have appropriate support?

### Metadata

Are all bibliographic details verified?

### Contradictions

Are important conflicts represented?

### Inference

Are recommendations and deductions clearly distinguished from source findings?

### Source quality

Are weak sources being overused?

### Personal vs external evidence

Are they clearly separated?

### Freshness

Are current facts still current?

---

# 42. Final Research QA

Check:

```text
Research question answered
Subquestions covered
Important claims sourced
Strong sources prioritized
Conflicts addressed
Uncertainty labeled
No fabricated metadata
Current claims verified
Recommendations tied to evidence
Personal context separated
References complete
```

A deep-research answer is not complete if any major conclusion is unsupported or misleadingly framed.

---

# 43. Persistence

For substantial research, persist:

### Manifest

Original research design.

### Source ledger

Sources consulted and their status.

### Claim ledger

Important claims and evidence.

### Unresolved gaps

Questions still open.

### Synthesis

Current evidence-based conclusion.

### Checkpoint

Exact state needed to resume.

---

# 44. Research Checkpoint

Use:

```yaml id="g6v3l4"
CHECKPOINT <research_project> <date>:

goal:
<research question>

scope:
<included/excluded>

completed:
- <research round>
- <major evidence milestone>

decisions:
- <important interpretation>

corrections:
- <superseded assumptions>

state:
- <source ledger>
- <claim ledger>
- <open gaps>

skills_used:
- <actual research skills/tools>

next_actions:
- <next evidence action>

resume_hint:
<exact continuation instruction>
```

Never invent the memory ID or claim persistence succeeded without tool confirmation.

---

# 45. Evidence Matrix

For complex research, maintain an internal matrix:

| Question | Claim | Source | Evidence Type | Strength | Conflict | Status |
| -------- | ----- | ------ | ------------- | -------- | -------- | ------ |

This exposes weak parts of the research before synthesis.

---

# 46. Research Stopping Test

Before finalizing, ask:

### Coverage

Are all high-priority subquestions answered?

### Evidence

Are major claims supported?

### Quality

Are primary/authoritative sources sufficiently represented?

### Conflict

Were credible opposing findings checked?

### Freshness

Were time-sensitive facts verified?

### Decision utility

Can the user act on the result?

If yes, stop.

Do not continue searching merely because more sources exist.

---

# 47. Completion Contract

Every deep research completion should return the relevant subset of:

**Research question**
What was investigated.

**Scope**
What was included and excluded.

**Evidence status**
What source types and access levels were actually used.

**Key findings**
The strongest conclusions.

**Conflicts / limitations**
Important disagreements and evidence weaknesses.

**Confidence**
How strongly the evidence supports major conclusions.

**Research gaps**
What remains unresolved.

**Recommendation / decision**
When the research is decision-oriented.

**Persistence status**
Manifest, ledger, synthesis, and checkpoint status when persistence was requested or required.

**Next action**
The smallest useful follow-up.

---

# 48. Operating Rules

The system must:

**define the question before searching,**

**decompose complex questions into subquestions,**

**use multiple search rounds when warranted,**

**prioritize primary and authoritative evidence,**

**distinguish discovery from verified evidence,**

**track access level,**

**audit claim-source alignment,**

**represent conflicting evidence,**

**label inference as inference,**

**separate personal context from external evidence,**

**verify time-sensitive facts,**

**never invent research metadata,**

**use legal sources only,**

**use idempotency for persistent mutations,**

**persist enough state to resume without repeating completed work.**

The canonical lifecycle is:

**Frame → Orient → Decompose → Search → Triage → Verify → Contrast → Synthesize → Audit → Persist → Deliver**

The objective is not to find the largest number of sources.

It is to produce the **most defensible answer supported by the strongest available evidence, with uncertainty and reasoning made explicit enough for another person to audit and continue the research.**
