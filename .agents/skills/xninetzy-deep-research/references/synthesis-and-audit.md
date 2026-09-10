# Xninetzy Deep Research — Synthesis and Audit

This reference expands source triage, evidence ledger, claim ledger, claim-source alignment, direct evidence vs inference, causal reasoning, conflicting evidence, evidence weighting, recency, and research agents. Read it when consolidating parallel findings or auditing a synthesis.

## Source triage

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

Possible claim states: supported, mixed, uncertain, insufficient, contradicted, superseded.

## Claim-source alignment

Audit every major conclusion for alignment. Ask:

> Does the cited source actually support the claim as written?

Common failures:

* source supports a narrower claim than the text,
* observational evidence presented as causality,
* one study generalized to all populations,
* source reports possibility presented as fact,
* abstract-only access treated as full evidence.

When necessary, narrow the wording.

## Direct evidence vs inference

Mark the difference.

### Direct evidence

> A study found X under conditions Y.

### Inference

> These findings suggest X may also be useful in context Z.

Do not phrase the second as though the study directly tested context Z.

## Causal reasoning

Be particularly careful with causal language. Distinguish:

* associated with,
* correlated with,
* predicts,
* is consistent with,
* suggests,
* may contribute to,
* causes.

Do not upgrade association to causation without appropriate evidence.

## Conflicting evidence

When credible sources disagree:

1. preserve both sides,
2. identify why they may differ,
3. inspect populations, methods, measurements, and dates,
4. assess source quality,
5. determine whether one conclusion is better supported,
6. retain residual uncertainty.

Do not hide disagreement simply to produce a cleaner narrative.

## Evidence weighting

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

## Research agents / workers

For complex research, divide work by evidence function rather than arbitrary topic duplication:

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

## Synthesis

The synthesis should answer the research question, not summarize the browsing process. A strong structure is:

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

Keep the distinction visible. Example:

> Research suggests X under these conditions. Given the project's current architecture, Y is the more practical implementation.

The second statement is a contextual recommendation, not a finding from the paper.