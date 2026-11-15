# graph-rag — §31–37

Contents: 31. Phase 05 — CONNECT; 32. Graph Write Classification; 33. Approval Boundary; 34. Entity Merge Safety; 35. Entity Deprecation; 36. Edge Lifecycle; 37. Proposed vs Applied Edge

## 31. Phase 05 — CONNECT

Create a relation only after:

```text id="q8m3w6"
source identity verified
target identity verified
relation semantics verified
evidence attached
```

Minimum edge:

```text id="v2x7n4"
source
relation
target
evidence
```

Recommended edge:

```text id="a1m8q5"
source
relation
target
evidence
confidence
validity
status
```

---

## 32. Graph Write Classification

Classify writes:

```text id="p7m4x2"
SMALL_AUTHORIZED_UPDATE
BULK_EDGE_CREATION
BULK_NODE_CREATION
ENTITY_MERGE
ENTITY_DELETE
EDGE_DELETE
ONTOLOGY_CHANGE
PROJECTION_REBUILD
```

Broad or destructive changes require explicit approval according to policy.

---

## 33. Approval Boundary

Require approval for:

```text id="c5n8m1"
bulk node creation
bulk edge creation
destructive merges
entity deletion
relationship deletion
ontology changes
large projection rebuilds
cross-domain mass linking
```

Small clearly authorized updates may follow the available policy.

When authorization is uncertain:

```text id="r4x7q2"
STOP
```

---

## 34. Entity Merge Safety

Never merge entities solely because:

```text id="y8m2k5"
names are similar
embeddings are similar
documents co-occur
aliases look related
```

Before merge:

```text id="q1n6v9"
identity evidence
external IDs
source compatibility
attribute consistency
relationship compatibility
temporal compatibility
```

A destructive merge must preserve provenance and be reversible when possible.

---

## 35. Entity Deprecation

Prefer deprecation over deletion when historical references matter.

Example:

```yaml id="m8x3p7"
entity:
  status: DEPRECATED
  replaced_by:
```

Historical edges may remain valid for past periods.

---

## 36. Edge Lifecycle

A relationship may move through:

```text id="g2m7x4"
PROPOSED
VALIDATED
ACTIVE
CONTESTED
DEPRECATED
REVOKED
```

Definitions:

```text id="a5p8n1"
PROPOSED
Candidate relationship not yet promoted.

VALIDATED
Evidence satisfies graph policy.

ACTIVE
Currently usable.

CONTESTED
Conflicting evidence exists.

DEPRECATED
No longer preferred but retained for historical reasons.

REVOKED
Relationship is known to be invalid.
```

---

## 37. Proposed vs Applied Edge

Never present:

```text id="z4x6m2"
PROPOSED
```

as:

```text id="k8p1q7"
ACTIVE
```

A proposed write is not graph state.

The final state must be verified from the canonical graph.

---
