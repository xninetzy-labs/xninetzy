---
name: xninetzy-memory
description: Retrieve, write, consolidate, checkpoint, and resume durable Xninetzy memory across sessions.
metadata:
  owner: xninetzy
  version: "1.0.0"
---

# Xninetzy Memory

## Start

Retrieve a scoped context bundle using:

* current request;
* workspace;
* project;
* course;
* artifact;
* active goal.

Prefer latest checkpoint, approved decisions, constraints, deadlines, and
relevant memories.

Do not load full history.

## Write

Persist only durable information:

* approved decision;
* official requirement;
* stable constraint;
* progress;
* selected source;
* artifact;
* blocker;
* next action.

Include:

```yaml
scope:
type:
content:
provenance:
confidence:
timestamp:
supersedes:
```

## Checkpoint

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

Create checkpoint at milestones, before compaction, before long generation, and
at session end.

## Resume

1. retrieve latest matching checkpoint;
2. verify stale external facts;
3. reopen local files;
4. continue from `next_actions`;
5. do not repeat completed work without reason.

## Conflict handling

* preserve provenance;
* prefer explicit user approval;
* prefer newer official portal data;
* mark older record superseded;
* never silently merge incompatible facts.
