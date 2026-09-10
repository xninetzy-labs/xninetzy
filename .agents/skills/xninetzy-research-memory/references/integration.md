# Xninetzy Research Memory — Integration, Output, and Operating Rules

This reference expands integration with Deep Research, Graph RAG, and general memory, the standard research resume output, the checkpoint structure, and the completion contract. Read it when integrating research memory with other skills or producing the closing report.

## Integration with Deep Research

`xninetzy-deep-research` owns the research process. `xninetzy-research-memory` owns durable continuity.

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

## Integration with Graph RAG

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

Research Memory preserves the evidence state. Graph RAG manages the relationship layer.

## Integration with general memory

General memory may store:

> "Research project is active; current focus is evaluating retrieval strategies."

Research Memory should store the richer research-specific state: session ID, source ledger, claim ledger, unresolved gaps, worker results, and next queries.

This avoids polluting general memory with large research state.

## Research checkpoint

Use:

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

## Checkpoint timing

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

## Failed research attempts

Persist failures when they prevent future repetition. Record:

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

## Standard research resume output

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

## Completion contract

Every meaningful research-memory operation should return the relevant subset of:

**Research session ID** — stable identifier for the research state.

**Persistence status** — what was created, updated, consolidated, or skipped.

**Source state** — relevant source records and deduplication status.

**Claim state** — supported, mixed, uncertain, or unresolved claims.

**Worker state** — completed, partial, or blocked worker results.

**Synthesis state** — current research synthesis stage.

**Open gaps** — what still requires investigation.

**Next queries** — the next unresolved evidence-producing searches.

**Artifacts** — verified research files and paths.

**Resume action** — the exact next step.

If persistence is not confirmed: **Research memory status: unverified.** Never invent a session ID, source record, artifact, or persistence result.

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