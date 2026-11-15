# graph-rag — §7–14

Contents: 7. Phase 01 — DETECT; 8. Phase 02 — DISCOVER; 9. Candidate Set; 10. Phase 03 — CANONICALIZE; 11. Entity Identity; 12. Identity Confidence; 13. Entity Schema; 14. Domain Ownership

## 7. Phase 01 — DETECT

Classify the query:

```text id="c6p1n5"
FACT_LOOKUP
RELATION_QUERY
PATH_QUERY
DEPENDENCY_QUERY
PREREQUISITE_QUERY
NEIGHBORHOOD_QUERY
CROSS_DOMAIN_QUERY
CONTRADICTION_QUERY
GRAPH_HEALTH_QUERY
GRAPH_MUTATION
```

Examples:

```text id="w4k9q2"
"What is normalization?"
→ FACT_LOOKUP

"What does this course require?"
→ PREREQUISITE_QUERY

"How does this paper support my project?"
→ PATH_QUERY

"What depends on this service?"
→ DEPENDENCY_QUERY
```

Only relational queries require graph traversal.

---

## 8. Phase 02 — DISCOVER

Identify candidate entities.

Discovery sources may include:

```text id="m9q3x7"
graph search
semantic/vector search
document retrieval
repository search
memory
user-provided identifiers
official sources
```

Vector/semantic retrieval is:

```text id="p6w1k8"
CANDIDATE GENERATION
```

not:

```text id="z4x8m2"
RELATIONSHIP PROOF
```

---

## 9. Candidate Set

Construct the smallest useful candidate set.

```yaml id="c3n7r5"
candidate_set:
  entities: []
  source_refs: []
  query_intent:
```

Avoid loading the entire graph when the question concerns:

```text id="g1m5q9"
one node
one relationship
one path
one dependency chain
```

---

## 10. Phase 03 — CANONICALIZE

Before creating or reasoning over entities:

```text id="k8r2v6"
search existing identity
→ compare canonical names
→ inspect aliases
→ inspect identifiers
→ reuse canonical entity
```

Never create duplicate entities simply because:

```text id="j5x9q1"
names differ slightly
abbreviations differ
language differs
documents use different capitalization
```

---

## 11. Entity Identity

Strong identity signals:

```text id="f3m8n4"
stable external ID
canonical URI
repository path
course code
document ID
DOI
official identifier
database key
```

Weak identity signals:

```text id="b7q2x5"
name similarity
embedding similarity
shared words
contextual resemblance
```

Weak identity signals may generate candidates but should not silently merge
entities.

---

## 12. Identity Confidence

Possible:

```text id="u6p1r9"
EXACT
HIGH
MEDIUM
LOW
UNKNOWN
```

Only:

```text id="d4m7x2"
EXACT
```

or a policy-approved equivalent should automatically support canonical reuse for
consequential graph writes.

---

## 13. Entity Schema

Canonical conceptual schema:

```yaml id="n8q4w7"
entity:
  entity_id:
  entity_type:
  canonical_name:
  aliases: []
  external_ids: []
  attributes: {}
  source_refs: []
  status:
  created_at:
  updated_at:
```

Possible entity types:

```text id="z5m2k8"
CONCEPT
COURSE
CLASS
GOAL
PROJECT
TASK
RESEARCH
PAPER
CLAIM
NOTE
DOCUMENT
SOURCE
SKILL
LEARNING_ACTIVITY
COMPONENT
SERVICE
API
DATASET
DECISION
```

Domain-specific schemas remain owned by their domain skills.

---

## 14. Domain Ownership

Graph RAG should not redefine domain semantics.

Examples:

```text id="p7c3m9"
academic semantics
→ cyber-campus

HEBAT/Moodle semantics
→ hebat-academic

durable personal memory
→ xninetzy-memory

research methodology
→ xninetzy-deep-research
```

Graph RAG stores and traverses relationships.

Owning domains define what those relationships mean operationally.

---
