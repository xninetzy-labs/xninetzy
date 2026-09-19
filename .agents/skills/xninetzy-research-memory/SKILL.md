---

...

...
name: "xninetzy-research-memory"
description: "Durable memory layer for deep-research sessions. Use to persist and resume research manifests, source records, claims, counterevidence, worker results, synthesis state, unresolved questions, next queries, and research artifacts while preserving provenance, access status, deduplication, freshness, contradiction history, and reproducible continuation."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "initialize -> identify -> persist -> deduplicate -> audit -> checkpoint -> resume -> revalidate -> continue -> consolidate"
...

# Xninetzy Research Memory OS

This skill is the **durable continuity layer specifically for research workflows**. It preserves enough research state for a future session to continue without:

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

## When to use

* persisting or resuming a deep-research session;
* checkpointing between research rounds;
* deduplicating sources across providers;
* preserving counterevidence and unresolved gaps;
* continuing an interrupted multi-session research project.

## When NOT to use

* generic cross-session continuity — use `xninetzy-memory`;
* small one-shot lookups — no persistence needed;
* research execution logic — that belongs to `xninetzy-deep-research`.

## Core workflow

1. **Initialize.** Create a stable research session ID, manifest, scope, and freshness requirement.
2. **Identify.** Search for an existing matching session before creating a duplicate.
3. **Persist.** Persist the manifest, source records, claims, counterevidence, worker results, synthesis status, unresolved gaps, next queries, and artifacts.
4. **Deduplicate.** Collapse sources by DOI, canonical URL, repository identifier, stable external source ID, normalized title/author/date, or content hash. Preserve provider provenance.
5. **Audit.** Verify claim-source alignment, source metadata, contradictions, inference vs finding, source quality, freshness, and personal-vs-external evidence separation.
6. **Checkpoint.** Persist a compact, self-contained checkpoint with the canonical structure.
7. **Resume.** Load the matching session, restore the manifest, inspect completed work, revalidate stale current facts, reopen referenced local artifacts, and continue from unresolved gaps.
8. **Revalidate.** Refresh time-sensitive facts (software versions, policies, regulations, current product capabilities, current institutional information, current APIs, current market conditions) before relying on prior claims.
9. **Continue.** Run additional research rounds only where gaps remain. Avoid repeating identical searches without justification.
10. **Consolidate.** As the session grows, deduplicate, merge equivalent claims, retain strongest provenance, preserve counterevidence, close resolved gaps, compress completed worker results, retain unresolved work, and create a current checkpoint.

## Research state shape

The canonical state contains:

```text
session_id
question
scope
manifest
sources
claims
counterevidence
worker_results
synthesis_status
unresolved
next_queries
artifacts
```

Detailed field shapes live in `references/state-schemas.md`.

## Manifest

Persist the research design: question, personal context, scope, subquestions, queries, databases, year range, inclusion, exclusion, source hierarchy, worker assignments, deliverable, freshness requirement, and evidence standard. The manifest should remain stable enough to compare progress against the original research objective.

## Research state vs transcript

Do not persist every search result or conversational exchange. Persist research decisions, important sources, important claims, contradictions, worker conclusions, open gaps, next queries, artifacts, and synthesis status. The transcript remains transient context. The research memory is the durable state model.

## Source records

Each important source should retain identity metadata, bibliographic fields, source type, identifier, canonical URL, access status, provider, relevance, evidence level, used_for, claims_supported, claims_contradicted, and status. Preserve only fields actually verified. Never invent missing bibliographic metadata.

## Access status

Never discard access level. Use `full_text | abstract | metadata | web_page | search_snippet | video | transcript | unavailable`. A future session must know whether the paper was actually read, only the abstract was available, only metadata was inspected, or the source was discovered but not verified.

## Source deduplication

Deduplicate using the strongest available identity signal. Preferred order:

1. DOI
2. canonical URL
3. repository identifier
4. stable external source ID
5. normalized title/author/date
6. content hash where appropriate

Do not create separate research records for the same paper simply because it appeared through multiple providers.

## Provider provenance

Deduplication must not erase provider history. A canonical source may have multiple provider entries with raw ranks. This preserves evidence about how the source was discovered while maintaining one canonical source record.

## Claim memory

Persist important claims separately from sources. A claim record contains claim, scope, supporting sources, counterevidence, evidence strength, direct_or_inferred, and status (`supported | mixed | uncertain | insufficient | contradicted | superseded`).

## Claim-source relationships

A claim should preserve `supported_by → Source A`, `supported_by → Source B`, `contradicted_by → Source C`. Do not flatten conflicting evidence into a single source list. The distinction between **support** and **counterevidence** must remain recoverable.

## Counterevidence

Counterevidence is a first-class research object. Record conflicting source, conflicting claim, nature of disagreement, methodology/context when relevant, current interpretation, and unresolved status. Do not silently discard evidence that weakens the preferred conclusion.

## Worker results

When research is parallelized, store each worker result separately with worker ID, assignment, completed, sources, findings, counterevidence, gaps, next_queries, and status. Worker results should remain attributable to their assigned subquestion.

## Worker completion and deduplication

A worker is complete only when its assignment is actually covered. Distinguish `completed | partial | blocked | insufficient_evidence`. Before launching additional workers, inspect existing assignments, identify overlapping subquestions, reuse completed findings, and create new work only for remaining gaps.

## Research round state

Track rounds explicitly where useful:

```yaml
round_1:
  purpose: landscape
  status: complete

round_2:
  purpose: evidence closure
  status: active
```

Possible state: `planned | active | complete | partial | blocked`.

## Synthesis state

Track synthesis separately: stage, claims covered, unresolved claims, contradictions reviewed, draft status. Possible stages: `not_started | outline | evidence_synthesis | conflict_analysis | drafting | auditing | final`. Do not mark synthesis final while major evidence gaps remain hidden.

## Unresolved research gaps

Persist unresolved questions explicitly. Each gap contains gap_id, question, importance, evidence_attempted, current_status, next_queries, blocked_by. Importance: `critical | important | minor`. This allows future sessions to focus only on evidence that still matters.

## Next queries

Store future search directions only when useful. A next query should connect to a specific unresolved question.

Weak: `Search more about RAG.`

Better: `Find controlled comparisons of hybrid BM25+dense retrieval versus dense-only retrieval for factual QA benchmarks published 2024–2026.`

Avoid storing redundant queries that have already been exhausted without justification.

## Resume rule

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

## Resume freshness

Recent facts may become stale. Before continuing, revalidate information that can change: software versions, policies, regulations, current product capabilities, current institutional information, current APIs, current market conditions. Historical research does not necessarily need revalidation merely because it is old.

## Avoid repeated searches

Before executing a query, inspect exact previous query, semantically equivalent queries, existing sources, and unresolved gaps. Rerun a search only when there is a reason such as new publication window, updated current facts, better provider, changed scope, missing evidence, or previous retrieval failure.

## Research artifact memory

Persist research artifacts: downloaded papers, evidence matrices, source ledgers, claim ledgers, generated briefs, charts, datasets, notes, interim reports, and final reports. Verify paths before storing them.

Artifact states: `planned | created | verified | superseded | missing | invalid`. Do not assume a path in memory still exists. On resume, reopen or verify referenced artifacts.

## Source freshness

Where relevant, distinguish `current | historical | stale | unknown`. A source can be historically authoritative without being current. For example, a 2024 paper can remain valid research evidence even when it is not current documentation. Do not conflate age with invalidity.

## Evidence freshness

The **fact** may be stale even when the source itself remains valid. Revalidate current API behavior rather than rewriting historical source metadata.

## Research decision memory

Persist important decisions: selected evidence threshold, chosen source hierarchy, scope reduction, excluded population, accepted definition, preferred methodological interpretation.

## Research scope changes

If the research scope changes:

1. preserve the original manifest,
2. record the change,
3. identify affected workers/sources/claims,
4. mark superseded plans,
5. update the active manifest.

Do not silently rewrite the historical research question.

## Research versioning

For major changes, keep a logical research version: `v1 — original scope`, `v2 — scope narrowed`, `v3 — current synthesis`. Versioning is especially useful when the research becomes a reusable report or publication.

## Consolidation

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

## Source and claim promotion

Promote sources when they are directly relevant, primary/authoritative, used in synthesis, evidence for an important claim, or useful for future continuation. Demote or omit sources that were irrelevant, duplicate, weak, superseded, or only exploratory.

Promote claims into durable research memory when they affect the final synthesis, inform a decision, identify a critical caveat, resolve a research question, or reveal a material contradiction. Do not persist every intermediate interpretation.

## Contradiction preservation

Never `resolve` contradictions by overwriting the weaker side. Preserve both support and contradiction edges, then store the current interpretation separately.

## Evidence confidence

A useful claim-level confidence state: `high | moderate | low | unknown`. Confidence should depend on source quality, directness, consistency, relevance, replication, and freshness where relevant. Do not treat source count as the sole measure.

## Research integrity

Never persist as verified: invented metadata, unsupported conclusions, fabricated quotes, guessed publication dates, guessed DOI, guessed URLs, or inferred study results. When uncertain: `status: unknown` or `confidence: unknown`.

## Personal context separation

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

## Reference map

* `references/state-schemas.md` — detailed field shapes for session, source, claim, counterevidence, worker result, gap, artifact, and checkpoint.
* `references/integration.md` — integration with Deep Research, Graph RAG, and general memory, plus the standard research resume output and operating rules.

## Routing

* Research execution → `xninetzy-deep-research`.
* Graph relationships → `graph-rag`.
* General cross-session memory → `xninetzy-memory`.

## Operating rules

The system must:

* create one stable research session ID,
* preserve the original manifest,
* store important sources and claims separately,
* retain source access status,
* deduplicate by authoritative identifiers,
* preserve provider provenance,
* retain counterevidence,
* store worker results independently,
* track synthesis status,
* make unresolved questions explicit,
* avoid repeating identical searches without justification,
* revalidate stale current facts on resume,
* verify local research artifacts before continuing,
* preserve important research decisions and corrections,
* never fabricate metadata or evidence.

The canonical lifecycle is:

**Initialize → Identify → Persist → Deduplicate → Audit → Checkpoint → Resume → Revalidate → Continue → Consolidate**

The central objective is:

> **A future research session should be able to open one session ID, understand exactly what has already been investigated, trust the provenance of the evidence, see what remains unresolved, and continue without repeating completed research.**