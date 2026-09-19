---

...

...
name: "xninetzy-memory"
description: "Durable memory operating system for retrieving, writing, consolidating, checkpointing, validating, and resuming scoped Xninetzy context across sessions. Use to preserve durable decisions, requirements, constraints, progress, sources, artifacts, blockers, and next actions while minimizing noise, maintaining provenance, detecting conflicts, preventing stale-state errors, and protecting sensitive information."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "scope -> retrieve -> rank -> validate -> resume -> execute -> checkpoint -> consolidate -> persist -> verify"
...

# Xninetzy Memory OS

This skill is the **durable continuity layer** for Xninetzy workflows. Its purpose is to preserve only the information that materially helps a future session continue work correctly.

The system should answer:

* What should I remember?
* Which memory is relevant now?
* Which memory is still valid?
* What changed?
* What must not be repeated?
* What is the exact next action?

The core principle is:

> **Persist durable state, preserve provenance, prefer current verified evidence, and resume from the smallest reliable context rather than replaying history.**

The canonical lifecycle is:

**Scope → Retrieve → Rank → Validate → Resume → Execute → Checkpoint → Consolidate → Persist → Verify**

## Memory philosophy

Memory is not a transcript archive. It is a **durable state layer**. Store information when it has future utility, especially:

* official requirements,
* explicit user decisions,
* stable constraints,
* meaningful progress,
* selected sources,
* important artifacts,
* blockers,
* corrections,
* next actions,
* resume instructions.

Avoid storing conversational noise.

## When to use

* retrieving relevant memory before continuing meaningful work;
* persisting durable state, decisions, checkpoints, artifacts, or corrections;
* consolidating or compressing accumulated memory;
* resolving stale or conflicting memory against current verified evidence.

## When NOT to use

* ephemeral reasoning without future utility;
* secrets, credentials, session tokens, or private personal data;
* every conversational turn — checkpoint only on state transitions.

## Memory state hierarchy

Treat information according to its durability:

* **Durable** — likely to remain relevant across sessions (approved design decisions, project architecture, stable formatting preferences, official requirements, canonical artifact locations).
* **Transitional** — relevant to an active project or milestone.
* **Ephemeral** — useful only for the current interaction.

Do not automatically persist ephemeral information.

## Core workflow

1. **Scope.** Build a scoped retrieval context from the current request, workspace, project, course, artifact, and active goal. Use the smallest relevant scope.
2. **Retrieve.** Pull the smallest relevant memory set using project, course, task, milestone, date range, or distinctive decision filters.
3. **Rank.** Prefer the latest verified checkpoint, then explicit user decisions, official requirements, stable constraints, current project state, selected sources, recent relevant progress, and older contextual memories.
4. **Validate.** Inspect provenance, timestamp, scope, supersession, and freshness. Determine whether current validation against external sources is required before relying on the memory.
5. **Resume.** Load the matching checkpoint, restore the manifest, inspect completed work, inspect unresolved items, revalidate stale current facts, reopen relevant local artifacts, compare actual vs remembered state, and continue from next actions.
6. **Execute.** Do the bounded next action from the resume hint.
7. **Checkpoint.** Persist a compact, self-contained summary using the canonical checkpoint structure.
8. **Consolidate.** When multiple memories contain overlapping information, deduplicate, preserve strongest provenance, merge compatible facts, mark older duplicates superseded, and retain important historical corrections.
9. **Persist.** Submit through the memory tool with a stable identity. Capture the returned memory ID only when actually returned.
10. **Verify.** After persistence, confirm the persistence result. Never invent a memory ID or successful write.

## Scoped retrieval

Before beginning meaningful work, construct a scoped retrieval context using:

* current request,
* workspace,
* project,
* course,
* artifact,
* active goal.

Use the smallest relevant scope. Do not load full historical memory unless explicitly required.

## Memory record structure

A durable memory record should contain:

```yaml
scope:
type:
content:
provenance:
confidence:
timestamp:
supersedes:
```

Recommended additional fields when supported: `status`, `project`, `course`, `artifact`, `goal`, `source_id`, `expires_at`. Do not add unsupported fields to a persistence tool schema.

## Memory types

Useful `type` values:

```text
decision
requirement
constraint
progress
source
artifact
blocker
next_action
correction
checkpoint
```

A type should describe the role of the information.

## Provenance and confidence

Every meaningful memory should answer: **Where did this information come from?**

Possible provenance: `user`, `official_portal`, `assignment_brief`, `course_material`, `research_source`, `artifact_inspection`, `tool_verified`, `derived`. When provenance is unavailable, set `provenance: unknown` rather than inventing an origin.

Confidence states: `high`, `moderate`, `low`, `unknown`. Do not use confidence to hide missing evidence. A memory with unknown provenance may need revalidation before being used for consequential work.

## Timestamps and supersession

Timestamp durable state when timing matters: deadlines, portal status, quota, software versions, financial records, project state, research findings, external actions. A historical fact should not be presented as current merely because it exists in memory.

When a durable fact changes, mark the previous record superseded rather than silently overwriting history. Record previous state, what superseded it, and the reason. This is especially useful for deadlines, filenames, architectural decisions, requirements, submission state, and roadmap decisions.

## Conflict handling

When two memories conflict:

1. preserve provenance,
2. compare timestamps,
3. identify source authority,
4. prefer explicit user approval where applicable,
5. prefer newer official portal data for portal state,
6. mark the older record superseded,
7. do not silently merge incompatible facts.

Example:

```text
Memory A: Deadline = Friday (source = old conversation)
Memory B: Deadline = Monday (source = current official portal)
Result: Use Monday. Mark Friday as superseded.
```

## Current external state overrides memory

Memory is historical context. Current external systems are authoritative for volatile state: HEBAT deadline, Cyber Campus KRS, course quota, submission status, software version, current API behavior.

Before consequential work, revalidate these facts.

## Resume workflow

```text
retrieve latest matching checkpoint
        ↓
validate current external state
        ↓
reopen referenced local files
        ↓
compare actual vs remembered state
        ↓
continue from next_actions
```

Do not repeat completed work unless validation shows it is no longer valid, the artifact changed, the user explicitly requests repetition, or the previous result was defective.

## Checkpoint structure

For active work:

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

A checkpoint should be self-contained, compact, current, and actionable.

## Checkpoint timing

Create checkpoints at milestones, before context compaction, before long generation, after consequential external actions, and at session end. Do not checkpoint every conversational turn.

## Failed attempts

Failed attempts are valuable when they prevent repeated mistakes. Record `attempt`, `result`, `reason`, `lesson`, and `safe alternative`. Do not record secret data associated with the failed attempt.

## Decision, requirement, constraint, and source memory

Persist important decisions with `decision`, `scope`, `reason`, `status`, and `what it supersedes`. Persist official requirements with the exact meaning, official source, course/activity, version/date when relevant, and known exceptions. Persist stable constraints such as required artifact format, fixed page size, submission channel, environment restriction, project architecture boundary, and allowed resource restriction. Persist selected sources that materially influence future work.

## Next action and resume hint

The next action should be concrete, bounded, and observable:

> Inspect the final PDF pages 1–8 for overflow and verify the references section.

Avoid:

> Continue working on the report.

A resume hint should prevent duplicate work:

> Resume from visual QA. The report content and references are already integrated. Do not regenerate the document unless QA identifies a source-level defect.

## Consolidation

When multiple memories contain overlapping information, identify duplicates, preserve the strongest provenance, merge only compatible facts, mark older duplicates superseded, retain important historical corrections, and avoid creating a larger, noisier memory than necessary.

Good consolidation should transform ten fragmented progress notes into one current checkpoint plus important decisions plus open blocker plus next action. Do not discard a historical correction when it explains why the current state differs from earlier assumptions.

## Expiration

Some memories should be treated as time-sensitive: deadlines, quotas, schedules, current provider availability, current software versions, portal states. When supported, use an expiration or freshness marker. If expired, revalidate before use. Do not automatically delete historical information simply because it expired.

## Sensitive information

Do not persist passwords, authentication cookies, access tokens, CAPTCHA answers, private verification tokens, API secrets, unnecessary browser state, or unnecessary sensitive personal data. Store only the minimum information needed to resume safely.

## Routing

* Specialized persistence (research state, learning state, etc.) → `xninetzy-research-memory` and `xninetzy-learning-coach`.
* Domain systems remain the authoritative owner of their state: HEBAT, Cyber Campus, Learning, Graph RAG, Deep Research, Artifact Orchestrator, Life Management.
* Memory stores the continuity state necessary to resume.

## Reference map

* `references/state-and-records.md` — memory philosophy, durability tiers, record structure, types, provenance, confidence, timestamps, supersession, conflict handling, and current-state overrides.
* `references/checkpoints-and-resume.md` — checkpoint structure, timing, content standard, failed attempts, artifact memory, source memory, decision memory, requirement memory, constraint memory, next-action memory, resume hint, consolidation, memory compression, retention, and expiration.
* `references/integration-and-safety.md` — integration with other Xninetzy skills, graph integration, learning integration, academic integration, artifact integration, memory search strategy, retrieval safety, memory quality test, standard memory record, standard checkpoint, completion contract, and operating rules.

## Operating rules

The system must:

* retrieve scoped context before meaningful continuation,
* prefer the latest verified checkpoint,
* prioritize explicit user decisions and official requirements,
* persist only durable information,
* preserve provenance and confidence,
* mark superseded records rather than silently merging incompatible facts,
* revalidate stale external state,
* reopen local artifacts before resuming artifact work,
* preserve failed attempts when they prevent repetition,
* keep sensitive secrets out of memory,
* avoid full-history retrieval by default,
* avoid duplicate memories through consolidation,
* continue from `next_actions` rather than repeating completed work.

The central objective is:

> **Remember enough to continue correctly, not enough to recreate the entire past.**