# Xninetzy Memory — Checkpoints and Resume

This reference expands checkpoint structure, timing, content standard, failed attempts, artifact memory, source memory, decision memory, requirement memory, constraint memory, next-action memory, resume hint, consolidation, memory compression, retention, and expiration. Read it when creating or resuming from a checkpoint.

## Resume workflow

A resume should follow:

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

Create checkpoints at:

### Milestones

After meaningful progress.

### Before context compaction

When the active working context is becoming large.

### Before long generation

When a long artifact or analysis is about to begin.

### After consequential external actions

Examples: upload, submission, portal mutation, artifact publication.

### Session end

When unfinished work may need to continue later.

Do not checkpoint every conversational turn.

## Checkpoint content standard

A useful checkpoint should capture goal, scope, completed work, decisions, constraints, sources, artifacts, failed attempts, open questions, next actions, and resume hint.

## Failed attempts

Failed attempts are valuable when they prevent repeated mistakes. Record:

```text
attempt
result
reason
lesson
safe alternative
```

Example:

> Attempted automatic upload; portal required an additional confirmation step. No submission occurred. Do not retry the same route; re-enter through the staged submission workflow.

Do not record secret data associated with the failed attempt.

## Artifact memory

When a meaningful artifact exists, store:

* artifact type,
* exact path,
* version,
* associated project,
* QA state,
* status,
* next action.

Example:

```text
Artifact:
/mnt/data/final_report.pdf

Status:
visual QA passed

Version:
qa-final

Next:
prepare submission preview
```

Never claim an artifact exists without verifying its path or persistent record.

## Source memory

Persist selected sources that materially influence future work. Useful fields:

```text
source
why_selected
relevant_claim
access_status
date
research_scope
```

Do not turn memory into a duplicate literature database.

## Decision memory

An important decision should capture **decision**, **scope**, **reason**, **status**, and **what it supersedes**.

Example:

> Decision: Use PostgreSQL for the project datastore.
>
> Scope: Current backend prototype.
>
> Reason: Existing team familiarity and relational workload.
>
> Status: Approved.

## Requirement memory

Official requirements are especially valuable for cross-session continuity. Store:

* exact requirement meaning,
* official source,
* course/activity,
* version/date when relevant,
* known exceptions.

Do not store an interpretation as an official requirement unless the source explicitly supports it.

## Constraint memory

Persist stable constraints such as:

* required artifact format,
* fixed page size,
* submission channel,
* environment restriction,
* project architecture boundary,
* allowed resource restriction.

Do not persist temporary constraints without context.

## Next-action memory

The next action should be:

**concrete + bounded + observable**

Good:

> Inspect the final PDF pages 1–8 for overflow and verify the references section.

Weak:

> Continue working on the report.

## Resume hint

A resume hint should prevent duplicate work.

Good:

> Resume from visual QA. The report content and references are already integrated. Do not regenerate the document unless QA identifies a source-level defect.

Weak:

> Continue the report.

## Consolidation

When multiple memories contain overlapping information:

1. identify duplicates,
2. preserve the strongest provenance,
3. merge only compatible facts,
4. mark older duplicates superseded,
5. retain important historical corrections,
6. avoid creating a larger, noisier memory than necessary.

Consolidation should reduce entropy rather than accumulate summaries forever.

## Memory compression

Good consolidation should transform ten fragmented progress notes into:

```text
1 current checkpoint
+
important decisions
+
open blocker
+
next action
```

Do not discard a historical correction when it explains why the current state differs from earlier assumptions.

## Memory retention

Prefer retaining information that has one or more of these properties:

* future decision impact,
* durable requirement,
* current project state,
* reusable knowledge,
* important correction,
* artifact reference,
* unresolved blocker,
* explicit user decision.

Avoid retaining:

* small-talk,
* temporary phrasing,
* redundant explanations,
* failed irrelevant searches,
* unimportant intermediate calculations.

## Expiration

Some memories should be treated as time-sensitive:

* deadlines,
* quotas,
* schedules,
* current provider availability,
* current software versions,
* portal states.

When supported, use an expiration or freshness marker. If expired, revalidate before use. Do not automatically delete historical information simply because it expired.

## Sensitive information

Do not persist passwords, authentication cookies, access tokens, CAPTCHA answers, private verification tokens, API secrets, unnecessary browser state, or unnecessary sensitive personal data. Store only the minimum information needed to resume safely.