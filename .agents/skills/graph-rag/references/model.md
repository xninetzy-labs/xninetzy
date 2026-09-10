# Graph RAG — Typed Model

This reference expands the typed entity model, relationship semantics, prerequisite graphs, cross-domain links, and graph hygiene. Read it when designing or maintaining a graph schema.

## Graph philosophy

### Graphs represent relationships, not similarity

A graph should capture meaningful semantic relations such as:

* prerequisite,
* part_of,
* supports,
* derived_from,
* references,
* related_to,
* implements,
* depends_on,
* blocks,
* produces,
* evaluates,
* contradicts,
* extends,
* applied_to.

Do not create an edge merely because two items have similar text.

### Evidence precedes assertion

A factual relationship should have `source → relation → target` plus sufficient provenance. Example:

```text
Python Fundamentals
      ── prerequisite_of ──>
Data Structures
```

This edge should be supported by an explicit source such as learning material, roadmap dependency, documented curriculum structure, project architecture, research evidence, or verified user statement. Vector similarity alone is not sufficient evidence.

## Source of truth

Maintain one canonical graph data source. If SQLite is the canonical source, then SQLite is the source of truth. Other systems may act as projections or indexes:

* Neo4j,
* graph databases,
* FAISS/vector indexes,
* search indexes,
* caches,
* embeddings,
* materialized views.

A projection must never silently introduce facts that do not exist in the canonical model.

## Graph domains

The graph may contain multiple knowledge domains. Keep cross-domain relationships evidence-backed.

### Learning

* Concept
* Skill
* Prerequisite
* Learning Goal
* Study Session
* Evidence
* Mastery State

### Research

* Paper
* Claim
* Dataset
* Method
* Finding
* Source
* Topic

### Academic

* Course
* Assignment
* Material
* Lecturer Instruction
* Deadline
* Submission

### Project

* Project
* Requirement
* Module
* Component
* Decision
* Milestone
* Artifact

### Knowledge

* Note
* Topic
* Document
* Entity
* Definition
* Example

The graph should support cross-domain relationships without collapsing domain-specific semantics.

## Typed entity model

Every graph node should have a stable identity and type. A conceptual node record:

```text
id
type
canonical_name
description
owner_scope
source
created_at
updated_at
status
```

Optional fields:

```text
aliases
external_id
url
version
metadata
confidence
```

Do not create duplicate nodes when an existing canonical entity represents the same thing.

## Entity canonicalization

Before creating a node:

1. search existing entities,
2. compare canonical names,
3. check aliases,
4. inspect relevant metadata,
5. verify ownership/domain,
6. reuse the existing entity when appropriate.

Example: `PostgreSQL`, `Postgres`, `PostgreSQL Database` may refer to one canonical entity.

Do not merge entities only because their names look similar. When identity remains uncertain, keep the entities separate and mark the relationship as uncertain or require clarification.

## Relationship model

Each edge should be typed:

```text
source_node
relation
target_node
owner_scope
evidence
confidence
created_at
updated_at
status
```

Possible edge statuses:

```text
proposed
verified
active
deprecated
rejected
uncertain
```

## Relationship semantics

Use precise relation names. Prefer:

```text
prerequisite_of
depends_on
supports
derived_from
references
part_of
implements
blocks
produces
evaluates
contradicts
extends
related_to
```

Avoid ambiguous relations such as `connected_to`, `important_to`, `associated_with`, `linked_to` unless the semantics truly cannot be made more precise.

## Prerequisite graph

Prerequisite relationships belong primarily to the learning domain. Example:

```text
Variables
   ↓
Functions
   ↓
Data Structures
   ↓
Algorithms
   ↓
Backend Engineering
```

Do not infer prerequisite relationships merely from course ordering. A prerequisite edge should describe a genuine dependency in understanding or capability.

## Cross-domain links

Cross-domain edges are useful when they provide additional reasoning value. Examples:

```text
Research Paper
   ── supports ──>
Learning Concept

Learning Concept
   ── enables ──>
Project Module

HEBAT Material
   ── grounds ──>
Assignment Requirement

Project Milestone
   ── produces ──>
Learning Evidence

Research Finding
   ── informs ──>
Roadmap Decision
```

Cross-domain edges should include provenance.

## Ownership and scope

Graph data should preserve ownership boundaries. Possible scopes:

```text
personal
course
project
organization
public
research
system
```

Do not leak or merge relationships across scopes without authorization. An identically named node in two scopes may still represent different entities.

## Temporal awareness

Relationships may change over time. Preserve effective date, source date, observed date, version, and superseded state when relevant. For example, `Framework Version 1 — used_by → Project` may become invalid after migration to Version 2. Do not treat historical relationships as permanently current.

## Graph hygiene

Periodically check for:

* duplicate entities,
* ambiguous entities,
* unsupported relationships,
* stale edges,
* inconsistent relation direction,
* contradictory ownership,
* broken references,
* orphan nodes,
* projection drift.

Do not automatically "fix" uncertain graph structure without evidence.

## Orphan and missing-link analysis

Useful graph reasoning includes identifying:

* orphan concepts,
* goals without prerequisites,
* research without a destination,
* projects without requirements,
* tasks without evidence,
* assignments without mapped concepts.

However, missing edges are not automatically errors. A missing link may simply mean "not yet established."

## Statistics

Graph statistics can support diagnosis:

* node counts,
* edge counts,
* orphan nodes,
* disconnected components,
* high-degree nodes,
* stale relationships,
* pending projections,
* uncertain edges.

Statistics should support graph maintenance and retrieval decisions, not be treated as semantic evidence by themselves.