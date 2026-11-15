# graph-rag — §48–58

Contents: 48. Phase 07 — REASON; 49. Reasoning Provenance; 50. No Silent Graph Completion; 51. Derived Relations; 52. Relation Semantics; 53. Ontology Validation; 54. Orphan Detection; 55. Missing-Link Detection; 56. Contradiction Detection; 57. Graph Consistency; 58. Graph Health Output

## 48. Phase 07 — REASON

Reason over:

```text id="k1x6m8"
retrieved nodes
retrieved edges
edge evidence
entity evidence
temporal state
contradictions
query constraints
```

Separate:

```text id="z5m2q9"
RETRIEVED FACT
DERIVED CONCLUSION
INFERRED INTERPRETATION
```

---

## 49. Reasoning Provenance

For each important conclusion:

```yaml id="q7m3n1"
conclusion:
  statement:
  source_edges: []
  evidence_refs: []
  derivation:
  confidence:
```

Example:

```text id="a8x2p5"
Conclusion:
Course B should precede Course C.

Supporting path:
Course A prerequisite_of Course C
Course B prerequisite_of Course A

Confidence:
derived from two validated prerequisite edges.
```

The conclusion is derived; the edges remain the factual evidence.

---

## 50. No Silent Graph Completion

Do not invent missing edges because the graph "looks incomplete."

For example:

```text id="c4m8q1"
Course A
Course B
Course C

A → prerequisite_of → B
B → prerequisite_of → C
```

does not justify:

```text id="n7x2p5"
A → prerequisite_of → C
```

unless transitive prerequisite semantics are explicitly defined for the domain.

---

## 51. Derived Relations

Some relationships may be derivable.

Example:

```text id="m3q8v1"
A PART_OF B
B PART_OF C
```

may support:

```text id="x6n2k4"
A INDIRECTLY_PART_OF C
```

only when ontology explicitly permits transitive derivation.

Mark derived edges as:

```text id="p9m4x7"
DERIVED
```

not:

```text id="h2q8n5"
DIRECT
```

---

## 52. Relation Semantics

Every relation should have defined semantics:

```yaml id="r3x7m2"
relation_definition:
  type:
  direction:
  inverse:
  symmetric:
  transitive:
  allowed_source_types: []
  allowed_target_types: []
  evidence_requirements: []
```

This provides ontology validation.

---

## 53. Ontology Validation

Reject an edge when:

```text id="k5n1m8"
relation type is invalid
source type is invalid
target type is invalid
direction is invalid
required provenance is missing
domain ownership is violated
temporal semantics are inconsistent
```

Example:

```text id="s8q2x6"
DOCUMENT
→ PREREQUISITE_OF
→ COURSE
```

should be rejected unless the ontology explicitly allows it.

---

## 54. Orphan Detection

Graph health should identify:

```text id="m2x7q4"
orphan entities
dangling edges
unresolved identifiers
isolated concepts
dead references
unsupported relationships
projection drift
```

An orphan is not automatically an error.

A source/document node may legitimately have no relationship yet.

---

## 55. Missing-Link Detection

Missing relationship analysis should be evidence-based.

Example:

```text id="a4m8q1"
Course B
requires Concept X
Course A teaches Concept X

Potential missing relationship:
Course A → supports → Concept X
```

This remains:

```text id="v6q3m9"
CANDIDATE
```

until evidence validates it.

---

## 56. Contradiction Detection

Look for:

```text id="w8m2k5"
same source-target pair
opposite relations
incompatible attributes
temporal conflicts
source disagreement
duplicate canonical identities
```

Do not automatically delete conflicting information.

Surface the conflict.

---

## 57. Graph Consistency

Useful invariants:

```text id="n3q7x1"
no orphaned target IDs
no invalid relation types
no impossible entity-type combinations
no duplicate canonical identities
no unresolved destructive merges
no projection references to missing canonical nodes
```

Domain-specific invariants should remain in owning skills.

---

## 58. Graph Health Output

```yaml id="p7x2m8"
graph_health:
  entity_count:
  edge_count:
  orphan_count:
  dangling_edge_count:
  contradiction_count:
  contested_edge_count:
  unknown_provenance_count:
  projection_sync:
  ontology_violations:
```

Health statistics describe graph state; they do not prove semantic correctness.

---
