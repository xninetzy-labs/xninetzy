# Xninetzy Research Memory OS

```yaml
---
name: xninetzy-research-memory
description: General-purpose durable memory layer for deep-research sessions. Persists and resumes research manifests, source records, claims, counterevidence, worker results, synthesis state, unresolved questions, next queries, and research artifacts while preserving provenance, access status, deduplication, freshness, contradiction history, and reproducible continuation.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "initialize -> identify -> persist -> deduplicate -> audit -> checkpoint -> resume -> revalidate -> continue -> consolidate"
---
```

# Xninetzy Research Memory OS

This skill is the **durable continuity layer specifically for research workflows**.

It preserves enough research state for a future session to continue without:

* repeating completed searches,
* losing source provenance,
* forgetting unresolved claims,
* confusing worker results,
* treating outdated facts as current,
* rebuilding the research manifest from scratch.

The central principle is:

> **Persist the research state, not the browsing transcript. Preserve provenance and uncertainty, deduplicate aggressively, and resume only from unresolved evidence gaps.**

The canonical lifecycle is:

**Initialize → Identify → Persist → Deduplicate → Audit → Checkpoint → Resume → Revalidate → Continue → Consolidate**

---

# 1. Research Session Identity

Every substantial research effort should have **one stable research session ID**.

Conceptually:

```yaml
session_id:
question:
scope:
created_at:
status:
```

The session ID is the anchor for:

* sources,
* claims,
* worker results,
* synthesis,
* unresolved gaps,
* research artifacts,
* checkpoints.

Do not create a new session ID simply because the user changes interface or opens a new conversation.

Create a new session only when the research objective is materially different.

---

# 2. Canonical Research State

A research session should maintain:

```yaml
session_id:
question:
scope:
manifest:
sources:
claims:
counterevidence:
worker_results:
synthesis_status:
unresolved:
next_queries:
artifacts:
```

Recommended additional state when supported:

```yaml
status:
last_checkpoint:
last_verified:
source_count:
claim_count:
completed_rounds:
research_version:
```

Do not add fields to a persistence tool unless the tool supports them.

---

# 3. Manifest

Persist the research design:

```yaml
manifest:
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
  freshness_requirement:
  evidence_standard:
```

The manifest should remain stable enough to compare progress against the original research objective.

---

# 4. Research State vs Transcript

Do not persist every search result or conversational exchange.

Persist:

* research decisions,
* important sources,
* important claims,
* contradictions,
* worker conclusions,
* open gaps,
* next queries,
* artifacts,
* synthesis status.

The transcript remains transient context.

The research memory is the durable state model.

---

# 5. Source Records

Each important source should retain:

```yaml
source_id:
title:
authors:
publication_date:
source_type:
identifier:
canonical_url:
access_status:
provider:
relevance:
evidence_level:
used_for:
claims_supported:
claims_contradicted:
status:
```

Preserve only fields actually verified.

Never invent missing bibliographic metadata.

---

# 6. Access Status

Never discard access level.

Use:

```text
full_text
abstract
metadata
web_page
search_snippet
video
transcript
unavailable
```

This distinction is critical.

A future session must know whether:

* the paper was actually read,
* only the abstract was available,
* only metadata was inspected,
* the source was discovered but not verified.

---

# 7. Source Deduplication

Deduplicate sources using the strongest available identity signal.

Preferred order:

1. DOI
2. canonical URL
3. repository identifier
4. stable external source ID
5. normalized title/author/date
6. content hash where appropriate

Do not create separate research records for the same paper simply because it appeared through multiple providers.

---

# 8. Provider Provenance

Deduplication must not erase provider history.

A canonical source may have:

```yaml
providers:
  - provider: arxiv
    raw_rank: 2
  - provider: crossref
    raw_rank: 5
```

This preserves evidence about how the source was discovered while maintaining one canonical source record.

---

# 9. Content Hashing

Use content hashes when useful for:

* exact document identity,
* duplicate detection,
* downloaded artifacts,
* source snapshots.

A content hash should identify content, not replace bibliographic identity.

Do not assume two documents with different hashes are necessarily different research works; versions and formatting changes can produce different hashes.

---

# 10. Claim Memory

Persist important claims separately from sources.

Conceptually:

```yaml
claim_id:
claim:
scope:
supporting_sources:
counterevidence:
evidence_strength:
direct_or_inferred:
status:
```

Possible claim states:

```text
supported
mixed
uncertain
insufficient
contradicted
superseded
```

---

# 11. Claim-Source Relationships

A claim should preserve:

```text id="73y5mg"
Claim
  ├── supported_by → Source A
  ├── supported_by → Source B
  └── contradicted_by → Source C
```

Do not flatten conflicting evidence into a single source list.

The distinction between **support** and **counterevidence** must remain recoverable.

---

# 12. Counterevidence

Counterevidence should be stored as a first-class research object.

Record:

* conflicting source,
* conflicting claim,
* nature of disagreement,
* methodology/context when relevant,
* current interpretation,
* unresolved status.

Example:

```yaml
counterevidence:
  - claim_id: C12
    source_id: S31
    observation: "Finds no significant effect under the tested conditions."
    status: unresolved
```

Do not silently discard evidence that weakens the preferred conclusion.

---

# 13. Worker Results

When research is parallelized, store each worker result separately.

Conceptually:

```yaml
worker_results:
  - worker_id:
    assignment:
    completed:
    sources:
    findings:
    counterevidence:
    gaps:
    next_queries:
    status:
```

Worker results should remain attributable to their assigned subquestion.

---

# 14. Worker Completion

A worker should be considered complete only when its assignment is actually covered.

A worker result should distinguish:

```text id="xu0uwx"
completed
partial
blocked
insufficient_evidence
```

Do not interpret "returned a response" as equivalent to completed research.

---

# 15. Worker Deduplication

Before launching additional workers:

1. inspect existing worker assignments,
2. inspect completed worker results,
3. identify overlapping subquestions,
4. reuse completed findings where valid,
5. create new work only for remaining gaps.

Do not repeatedly assign the same question to additional workers without a reason.

---

# 16. Research Round State

Track rounds explicitly where useful:

```yaml
round_1:
  purpose: landscape
  status: complete

round_2:
  purpose: evidence closure
  status: active
```

Possible state:

```text
planned
active
complete
partial
blocked
```

---

# 17. Synthesis State

Track synthesis separately:

```yaml
synthesis_status:
  stage:
  claims_covered:
  unresolved_claims:
  contradictions_reviewed:
  draft_status:
```

Possible stages:

```text
not_started
outline
evidence_synthesis
conflict_analysis
drafting
auditing
final
```

Do not mark synthesis final while major evidence gaps remain hidden.

---

# 18. Unresolved Research Gaps

Persist unresolved questions explicitly.

Each gap may contain:

```yaml
gap_id:
question:
importance:
evidence_attempted:
current_status:
next_queries:
blocked_by:
```

Importance may be:

```text
critical
important
minor
```

This allows future sessions to focus only on evidence that still matters.

---

# 19. Next Queries

Store future search directions only when useful.

A next query should connect to a specific unresolved question.

Weak:

> "Search more about RAG."

Better:

> "Find controlled comparisons of hybrid BM25+dense retrieval versus dense-only retrieval for factual QA benchmarks published 2024–2026."

Avoid storing redundant queries that have already been exhausted without justification.

---

# 20. Resume Rule

On resume:

1. load the matching research session,
2. restore the manifest,
3. inspect completed worker results,
4. inspect unresolved questions,
5. inspect source and claim status,
6. verify stale current facts,
7. reopen relevant local artifacts,
8. continue only unresolved work.

Do not restart the entire research process.

---

# 21. Resume Freshness

Recent facts may become stale.

Before continuing, revalidate information that can change:

* software versions,
* policies,
* regulations,
* current product capabilities,
* current institutional information,
* current APIs,
* current market conditions.

Historical research does not necessarily need revalidation merely because it is old.

---

# 22. Resume Integrity

A resume should compare:

```text id="tmn0j4"
remembered state
vs
actual current state
```

Possible outcomes:

```text
unchanged
updated
superseded
missing
uncertain
```

Do not continue blindly when current state materially differs.

---

# 23. Avoid Repeated Searches

Before executing a query, inspect:

* exact previous query,
* semantically equivalent queries,
* existing sources,
* unresolved gaps.

Rerun a search only when there is a reason such as:

* new publication window,
* updated current facts,
* better provider,
* changed scope,
* missing evidence,
* previous retrieval failure.

---

# 24. Search Coverage

Track coverage by subquestion.

Example:

| Subquestion      | Evidence          | Status   |
| ---------------- | ----------------- | -------- |
| Definition       | 3 strong sources  | complete |
| Effectiveness    | 4 studies         | complete |
| Limitations      | 2 studies         | partial  |
| Current practice | 1 official source | weak     |

This makes missing evidence visible.

---

# 25. Research Artifact Memory

Persist research artifacts such as:

* downloaded papers,
* evidence matrices,
* source ledgers,
* claim ledgers,
* generated briefs,
* charts,
* datasets,
* notes,
* interim reports,
* final reports.

Store:

```yaml
artifact:
  path:
  type:
  version:
  purpose:
  status:
  created_at:
```

Verify paths before storing them.

---

# 26. Artifact Status

Possible states:

```text
planned
created
verified
superseded
missing
invalid
```

Do not assume a path in memory still exists.

On resume, reopen or verify referenced artifacts.

---

# 27. Source Freshness

Where relevant, distinguish:

```text
current
historical
stale
unknown
```

A source can be historically authoritative without being current.

For example:

> A 2024 paper can remain valid research evidence even when it is not current documentation.

Do not conflate age with invalidity.

---

# 28. Evidence Freshness

The **fact** may be stale even when the source itself remains valid.

Example:

```text
Source:
2025 API documentation

Claim:
"Current API supports feature X"

Current date:
2026

Result:
Revalidate current API behavior.
```

Do not rewrite historical source metadata simply because the claim needs current verification.

---

# 29. Research Checkpoint

At meaningful milestones, persist:

```yaml
goal:
scope:
completed:
decisions:
constraints:
sources:
artifacts:
failed_attempts:
open_questions:
next_actions:
resume_hint:
```

Add research-specific context through the session record rather than duplicating all data inside every checkpoint.

---

# 30. Checkpoint Timing

Checkpoint:

* after major search rounds,
* after source discovery milestones,
* after worker completion,
* after evidence synthesis,
* before long synthesis,
* after artifact generation,
* after major contradiction resolution,
* before context compaction,
* at session end.

Do not checkpoint every single search.

---

# 31. Failed Research Attempts

Persist failures when they prevent future repetition.

Record:

```yaml
attempt:
query:
provider:
result:
reason:
lesson:
next_strategy:
```

Example:

> Crossref query failed because the identifier was incomplete. Retry with the verified DOI rather than the previous malformed identifier.

Do not preserve irrelevant failure noise.

---

# 32. Research Decision Memory

Persist important decisions such as:

* selected evidence threshold,
* chosen source hierarchy,
* scope reduction,
* excluded population,
* accepted definition,
* preferred methodological interpretation.

Example:

```yaml
decision:
  content: "Use peer-reviewed studies and official documentation as the primary evidence set."
  reason: "Research question concerns both empirical effectiveness and current implementation."
```

---

# 33. Research Scope Changes

If the research scope changes:

1. preserve the original manifest,
2. record the change,
3. identify affected workers/sources/claims,
4. mark superseded plans,
5. update the active manifest.

Do not silently rewrite the historical research question.

---

# 34. Research Versioning

For major changes, keep a logical research version:

```text
v1 — original scope
v2 — scope narrowed
v3 — current synthesis
```

The exact mechanism may depend on the persistence system.

Versioning is especially useful when the research becomes a reusable report or publication.

---

# 35. Consolidation

When a research session becomes large:

1. deduplicate sources,
2. merge equivalent claims,
3. retain strongest provenance,
4. preserve counterevidence,
5. close resolved gaps,
6. promote important conclusions,
7. compress completed worker results,
8. retain unresolved work,
9. create a current checkpoint.

Do not delete the evidence needed to audit important claims.

---

# 36. Source Promotion

Not every discovered source deserves durable retention.

Promote sources when they are:

* directly relevant,
* primary/authoritative,
* used in synthesis,
* evidence for an important claim,
* useful for future continuation.

Demote or omit sources that were:

* irrelevant,
* duplicate,
* weak,
* superseded,
* only exploratory.

---

# 37. Claim Promotion

Promote claims into durable research memory when they:

* affect the final synthesis,
* inform a decision,
* identify a critical caveat,
* resolve a research question,
* reveal a material contradiction.

Do not persist every intermediate interpretation.

---

# 38. Contradiction Preservation

Never "resolve" contradictions by overwriting the weaker side.

Preserve:

```text
Claim A
Source A
↓
supports

Claim A
Source B
↓
contradicts
```

Then store the current interpretation separately.

Example:

```yaml
interpretation:
  conclusion: "Evidence favors A under conditions X, but is mixed under Y."
  confidence: moderate
```

---

# 39. Evidence Confidence

A useful claim-level confidence state:

```text
high
moderate
low
unknown
```

Confidence should depend on:

* source quality,
* directness,
* consistency,
* relevance,
* replication,
* freshness where relevant.

Do not treat source count as the sole measure.

---

# 40. Research Integrity

Never persist as verified:

* invented metadata,
* unsupported conclusions,
* fabricated quotes,
* guessed publication dates,
* guessed DOI,
* guessed URLs,
* inferred study results.

When uncertain:

```text
status: unknown
```

or:

```text
confidence: unknown
```

---

# 41. Personal Context Separation

Research memory may contain user/project context, but keep it separate from external evidence.

Example:

```text
External evidence:
"Study X found Y."

Project context:
"Our current system uses PostgreSQL."

Interpretation:
"Y may influence the decision in this project."
```

Do not store the interpretation as though Study X directly established it.

---

# 42. Integration With Deep Research

`xninetzy-deep-research` owns the research process.

`xninetzy-research-memory` owns durable continuity.

Recommended relationship:

```text
Deep Research
 ↓
sources / claims / synthesis
 ↓
Research Memory
 ↓
future session
 ↓
Deep Research resumes unresolved work
```

Do not duplicate research execution logic inside the memory layer.

---

# 43. Integration With Graph RAG

Useful research relationships may include:

```text
Source
 → supports →
Claim
 → informs →
Concept
 → supports →
Goal / Decision
```

Research Memory preserves the evidence state.

Graph RAG manages the relationship layer.

---

# 44. Integration With General Memory

General memory may store:

> "Research project is active; current focus is evaluating retrieval strategies."

Research Memory should store the richer research-specific state:

* session ID,
* source ledger,
* claim ledger,
* unresolved gaps,
* worker results,
* next queries.

This avoids polluting general memory with large research state.

---

# 45. Completion Contract

Every meaningful research-memory operation should return the relevant subset of:

**Research session ID**
Stable identifier for the research state.

**Persistence status**
What was created, updated, consolidated, or skipped.

**Source state**
Relevant source records and deduplication status.

**Claim state**
Supported, mixed, uncertain, or unresolved claims.

**Worker state**
Completed, partial, or blocked worker results.

**Synthesis state**
Current research synthesis stage.

**Open gaps**
What still requires investigation.

**Next queries**
The next unresolved evidence-producing searches.

**Artifacts**
Verified research files and paths.

**Resume action**
The exact next step.

If persistence is not confirmed:

> **Research memory status: unverified.**

Never invent a session ID, source record, artifact, or persistence result.

---

# 46. Standard Research Resume Output

```text
Research Session
Question
Current Scope
Completed Research
Verified Sources
Important Claims
Counterevidence
Synthesis Status
Open Gaps
Next Queries
Artifacts
Resume Action
```

Keep the output proportional to the size of the research session.

---

# 47. Operating Rules

The system must:

**create one stable research session ID,**

**preserve the original manifest,**

**store important sources and claims separately,**

**retain source access status,**

**deduplicate by authoritative identifiers,**

**preserve provider provenance,**

**retain counterevidence,**

**store worker results independently,**

**track synthesis status,**

**make unresolved questions explicit,**

**avoid repeating identical searches without justification,**

**revalidate stale current facts on resume,**

**verify local research artifacts before continuing,**

**preserve important research decisions and corrections,**

**never fabricate metadata or evidence.**

The canonical lifecycle is:

**Initialize → Identify → Persist → Deduplicate → Audit → Checkpoint → Resume → Revalidate → Continue → Consolidate**

The central objective is:

> **A future research session should be able to open one session ID, understand exactly what has already been investigated, trust the provenance of the evidence, see what remains unresolved, and continue without repeating completed research.**
