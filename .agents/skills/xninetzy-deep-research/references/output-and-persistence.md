# Xninetzy Deep Research — Output, Persistence, and Operating Rules

This reference expands research-to-decision mapping, research-to-roadmap integration, graph integration, deliverables, citation integrity, no invented metadata, quote policy, research gaps, confidence, audit, persistence, evidence matrix, stopping test, and completion contract. Read it when finalizing or persisting research state.

## Research-to-decision mapping

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

## Graph integration

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

Do not turn semantic similarity into a factual graph edge. All important graph links should remain evidence-backed.

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

For each external factual claim:

* provide an appropriate source,
* cite at the claim level where practical,
* avoid citation dumping at the end of unrelated paragraphs,
* do not cite a source that was not actually consulted.

When web sources are used, preserve the required web citation format. When files or research artifacts are used, preserve their applicable citation/provenance format.

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

For major conclusions, use qualitative confidence: high, moderate, low, unknown. Base confidence on:

* evidence quality,
* source agreement,
* directness,
* relevance,
* recency,
* reproducibility.

Do not interpret confidence as statistical probability unless a quantitative model actually exists.

## Audit procedure

Before final delivery, perform an evidence audit. Verify:

* **Claim-source alignment** — does each important claim have appropriate support?
* **Metadata** — are all bibliographic details verified?
* **Contradictions** — are important conflicts represented?
* **Inference** — are recommendations and deductions clearly distinguished from source findings?
* **Source quality** — are weak sources being overused?
* **Personal vs external evidence** — are they clearly separated?
* **Freshness** — are current facts still current?

## Final research QA

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

## Persistence

For substantial research, persist:

* **Manifest** — original research design.
* **Source ledger** — sources consulted and their status.
* **Claim ledger** — important claims and evidence.
* **Unresolved gaps** — questions still open.
* **Synthesis** — current evidence-based conclusion.
* **Checkpoint** — exact state needed to resume.

## Research checkpoint

Use:

```yaml
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

## Evidence matrix

For complex research, maintain an internal matrix:

| Question | Claim | Source | Evidence Type | Strength | Conflict | Status |
| -------- | ----- | ------ | ------------- | -------- | -------- | ------ |

This exposes weak parts of the research before synthesis.

## Research stopping test

Before finalizing, ask:

* **Coverage** — are all high-priority subquestions answered?
* **Evidence** — are major claims supported?
* **Quality** — are primary/authoritative sources sufficiently represented?
* **Conflict** — were credible opposing findings checked?
* **Freshness** — were time-sensitive facts verified?
* **Decision utility** — can the user act on the result?

If yes, stop. Do not continue searching merely because more sources exist.

## Completion contract

Every deep research completion should return the relevant subset of:

**Research question** — what was investigated.

**Scope** — what was included and excluded.

**Evidence status** — what source types and access levels were actually used.

**Key findings** — the strongest conclusions.

**Conflicts / limitations** — important disagreements and evidence weaknesses.

**Confidence** — how strongly the evidence supports major conclusions.

**Research gaps** — what remains unresolved.

**Recommendation / decision** — when the research is decision-oriented.

**Persistence status** — manifest, ledger, synthesis, and checkpoint status when persistence was requested or required.

**Next action** — the smallest useful follow-up.

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

The canonical lifecycle is:

**Frame → Orient → Decompose → Search → Triage → Verify → Contrast → Synthesize → Audit → Persist → Deliver**