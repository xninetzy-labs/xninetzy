# Xninetzy Memory — State, Records, and Conflicts

This reference expands memory philosophy, durability tiers, memory record structure, types, provenance, confidence, timestamps, supersession, conflict handling, and current-state overrides. Read it when designing the durable state layer.

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

## Memory state hierarchy

Treat information according to its durability:

### Durable

Likely to remain relevant across sessions.

Examples:

* approved design decision,
* project architecture,
* stable formatting preference,
* official requirement,
* canonical artifact location.

### Transitional

Relevant to an active project or milestone.

Examples:

* current research state,
* pending review,
* current implementation stage.

### Ephemeral

Useful only for the current interaction.

Examples:

* temporary reasoning,
* intermediate wording,
* transient tool output.

Do not automatically persist ephemeral information.

## Scoped retrieval

Before beginning meaningful work, construct a scoped retrieval context using:

* current request,
* workspace,
* project,
* course,
* artifact,
* active goal.

Use the smallest relevant scope. Do not load full historical memory unless explicitly required.

## Retrieval priority

Prefer memory in this order:

1. latest verified checkpoint,
2. explicit user decisions,
3. official requirements,
4. stable constraints,
5. current project state,
6. selected sources,
7. recent relevant progress,
8. older contextual memories.

When a newer verified memory conflicts with older information, the newer state generally wins.

## Relevance filtering

A memory is relevant when it materially affects current decisions, current constraints, next action, artifact state, deadline, architecture, learning state, or external action state. Do not retrieve memories merely because they share keywords.

## Memory record

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

Recommended additional fields when supported:

```yaml
status:
project:
course:
artifact:
goal:
source_id:
expires_at:
```

Do not add unsupported fields to a persistence tool schema.

## Memory types

Useful `type` values include:

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

## Provenance

Every meaningful memory should answer:

**Where did this information come from?**

Possible provenance:

```text
user
official_portal
assignment_brief
course_material
research_source
artifact_inspection
tool_verified
derived
```

When provenance is unavailable, `provenance = unknown`. Do not invent an origin.

## Confidence

Confidence describes how strongly the memory is supported. Suggested states:

```text
high
moderate
low
unknown
```

Do not use confidence to hide missing evidence. A memory with unknown provenance may need revalidation before being used for consequential work.

## Timestamp

Timestamp durable state when timing matters. Especially important for:

* deadlines,
* portal status,
* quota,
* software versions,
* financial records,
* project state,
* research findings,
* external actions.

A historical fact should not be presented as current merely because it exists in memory.

## Supersession

When a durable fact changes:

```text
old record
   ↓
new verified record
   ↓
old record marked superseded
```

Example:

```yaml
supersedes:
  - memory_id: "<verified id>"
    reason: "official portal deadline changed"
```

Never silently overwrite history when knowing the previous state matters.

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
Memory A:
Deadline = Friday
Source = old conversation

Memory B:
Deadline = Monday
Source = current official portal

Result:
Use Monday.
Mark Friday as superseded.
```

## Current external state overrides memory

Memory is historical context. Current external systems are authoritative for volatile state:

```text
HEBAT deadline
Cyber Campus KRS
course quota
submission status
software version
current API behavior
```

Before consequential work, revalidate these facts.