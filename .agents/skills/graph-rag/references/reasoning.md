# Graph RAG — Reasoning and Retrieval

This reference expands narrowest-useful-query patterns, hybrid retrieval, path reasoning, contradiction handling, and projection verification. Read it when designing queries or interpreting results.

## Graph search

Before constructing an answer:

1. search relevant nodes,
2. inspect relevant edges,
3. inspect graph statistics when useful,
4. retrieve supporting evidence,
5. determine whether graph traversal materially improves the answer.

Do not traverse the entire graph unnecessarily.

## Narrowest useful query

Use the smallest graph query that answers the request.

### Exact relation

```text
A → prerequisite_of → B
```

### Neighborhood

```text
A → all relevant adjacent nodes
```

### Path

```text
A → ... → B
```

### Dependency chain

```text
Goal → required skill → prerequisite → foundational concept
```

### Reverse dependency

```text
Concept → projects / goals / tasks that depend on it
```

### Hybrid retrieval

```text
semantic search
+
graph traversal
```

Prefer focused retrieval over broad graph expansion.

## Hybrid graph + vector retrieval

Use vector search to discover potentially relevant items. Use graph relationships to establish structured context:

```text
Query
 ↓
Semantic candidates
 ↓
Canonical entity resolution
 ↓
Graph expansion
 ↓
Evidence filtering
 ↓
Relationship-aware answer
```

Do not turn vector similarity into a factual relationship automatically. Similarity is a candidate-generation signal, not proof.

## Path reasoning

When a graph path is relevant, explain it explicitly:

```text
Goal:
Deploy a production backend

Path:
Backend Fundamentals
 → HTTP / API Concepts
 → REST API
 → Authentication
 → Containerization
 → Deployment
```

Explain why each edge exists when it materially supports the conclusion.

## Path confidence

Do not assign one blanket confidence score to an entire path without considering its edges. A path may contain:

```text
verified
→ verified
→ uncertain
→ verified
```

Therefore the conclusion is constrained by the uncertain edge. Surface the weakest meaningful link.

## Neighborhood analysis

For a node with many relationships, distinguish:

* direct neighbors,
* second-order neighbors,
* prerequisite ancestors,
* dependent descendants,
* cross-domain references.

Avoid treating all neighbors as equally relevant. Prioritize relationships by:

1. semantic relevance,
2. evidence strength,
3. query intent,
4. graph distance.

## Research-to-roadmap reasoning

Connect research to learning plans:

```text
Research Paper
      ↓ supports
Concept
      ↓ enables
Skill
      ↓ required_by
Roadmap Milestone
      ↓ practiced_by
Project Task
```

This enables questions such as "Which research supports the next roadmap milestone?" or "What evidence justifies putting this concept before that one?"

## Project graph reasoning

For software or technical projects, model relationships such as:

```text
Requirement
 ↓
Module
 ↓
Component
 ↓
Interface
 ↓
Test
 ↓
Artifact
```

Also model:

* `Module A depends_on Module B`
* `Requirement R implemented_by Module A`
* `Test T validates Component C`
* `Decision D affects Module M`
* `Milestone M produces Artifact A`

This allows graph reasoning to support architecture and project planning.

## Academic graph reasoning

Connect academic artifacts:

```text
Course
 ↓
Assignment
 ↓
Requirement
 ↓
Material
 ↓
Concept
 ↓
Practice Task
 ↓
Evidence
```

Useful for answering which concepts are required by an assignment, which materials support a requirement, which learning gaps may block the assignment, and which evidence has already been produced.

## Contradictions

The graph should be able to represent contradictory claims without forcing premature resolution:

```text
Source A
   ── supports ──> Claim X

Source B
   ── contradicts ──> Claim X
```

When contradictions exist:

1. preserve both sources,
2. identify the conflicting claim,
3. compare source authority and context,
4. avoid silently selecting one,
5. surface unresolved disagreement when relevant.

## Temporal awareness

Relationships may change over time. When important, preserve effective date, source date, observed date, version, and superseded state. For example, `Framework Version 1 — used_by → Project` may become invalid after migration to Version 2. Do not treat historical relationships as permanently current.

## Write safety

Reads and writes must be clearly separated.

* **Read** can return nodes, edges, evidence, paths, and statistics.
* **Write** can create or update nodes, create or modify edges, deprecate relationships, or rebuild projections.

Do not present a proposed write as a completed write.