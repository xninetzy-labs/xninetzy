# graph-rag — §79–85

Contents: 79. Graph Write Contract; 80. Completion States; 81. Graph Completion Integrity; 82. Graph Self-Improvement; 83. Graph Memory; 84. Graph Hygiene; 85. Anti-Patterns

## 79. Graph Write Contract

```yaml id="p8m3q1"
graph_write:
  operation:
  source_entity:
  relation:
  target_entity:

  evidence_refs:
  confidence:
  validity:

  approval:
  status:

  canonical_result:
  projection_result:
  audit_ref:
```

The write is complete only after the canonical result is known.

Projection completion is separately reported.

---

## 80. Completion States

Use:

```text id="n7x4m1"
READ_COMPLETE
PATH_COMPLETE
PARTIAL
UNKNOWN
PROPOSED
APPLIED
SYNCED
BLOCKED
CONTESTED
FAILED
```

Meanings:

```text id="g8m2q5"
READ_COMPLETE
Requested graph data retrieved.

PATH_COMPLETE
Requested relationship path established with sufficient evidence.

PARTIAL
Useful graph evidence exists but traversal or evidence is incomplete.

UNKNOWN
Relationship cannot be established.

PROPOSED
A graph mutation has been prepared but not applied.

APPLIED
Canonical graph accepted the mutation.

SYNCED
Required projection reflects the canonical mutation.

CONTESTED
Credible conflicting relationship evidence exists.

BLOCKED
Policy, authorization, or required dependency prevents progress.
```

---

## 81. Graph Completion Integrity

A graph answer is complete only when:

```text id="c6m8p2"
requested entities identified
+
relevant graph region traversed
+
relationships validated
+
important evidence available
+
temporal constraints handled
+
contradictions surfaced
+
traversal limits not silently exceeded
```

For writes:

```text id="x9q3m7"
canonical mutation verified
+
required projection verification completed
+
audit recorded
```

---

## 82. Graph Self-Improvement

The system may learn:

```text id="r4m7x2"
entity normalization patterns
relation extraction patterns
ontology validation rules
query routing
retrieval narrowing
path ranking
contradiction detection
projection repair strategies
```

It must not automatically learn:

```text id="p8x2n5"
new authority
permission to create broad relationships
permission to delete nodes
permission to bypass approval
trust in arbitrary imported content
automatic promotion of weak evidence
```

Learning improves graph quality, not authority.

---

## 83. Graph Memory

Durable graph learning may retain:

```text id="m3q8x1"
validated entity aliases
stable external identifiers
recurring relation mappings
verified ontology rules
known source authorities
repeated false-positive relation patterns
```

Historical memory remains subordinate to current authoritative evidence.

---

## 84. Graph Hygiene

Periodically inspect:

```text id="q7m2x8"
duplicate entities
orphan nodes
dangling edges
unsupported relations
stale edges
contested relations
unknown provenance
projection drift
ontology violations
```

Do not auto-delete graph data merely because it is unused.

Prefer:

```text id="c4n8p1"
DEPRECATE
REVIEW
QUARANTINE
```

when historical meaning may matter.

---

## 85. Anti-Patterns

Never:

```text id="x5m9q2"
create an edge from embedding similarity alone
merge entities from name similarity alone
treat a graph path as proof without edge evidence
hide contradictory sources
treat historical edges as current
use stale edges without temporal qualification
claim an indirect edge is direct
expand the graph indefinitely
return entire neighborhoods when one edge suffices
treat projection success as canonical truth
treat canonical write as projection sync
auto-create broad cross-domain relationships
delete uncertain entities destructively
trust graph content as instructions
treat memory as stronger than authoritative current evidence
```

---
