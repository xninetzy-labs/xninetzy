# graph-rag — §15–24

Contents: 15. Phase 04 — VALIDATE; 16. Relation Schema; 17. Typed Relationship Vocabulary; 18. Relationship Direction; 19. Symmetric Relations; 20. Inverse Relations; 21. Evidence and Provenance; 22. Evidence Strength; 23. Evidence vs Confidence; 24. Provenance Chain

## 15. Phase 04 — VALIDATE

Before promoting a relationship:

```text id="x4n7m1"
validate source
validate target
validate relation type
validate evidence
validate temporal context
validate authority
validate contradiction state
```

The question is:

> **Does the evidence actually support this exact relation?**

Not:

> **Are these two entities semantically similar?**

---

## 16. Relation Schema

Canonical edge:

```yaml id="q6m1v9"
relation:
  relation_id:
  source_entity:
  relation_type:
  target_entity:

  evidence_refs: []

  confidence:
  evidence_strength:

  valid_from:
  valid_until:

  status:

  created_at:
  updated_at:
```

---

## 17. Typed Relationship Vocabulary

Prefer precise relations:

```text id="k4x8p2"
PREREQUISITE_OF
DEPENDS_ON
SUPPORTS
DERIVED_FROM
REFERENCES
IMPLEMENTS
PART_OF
CONTAINS
PRODUCES
EVALUATES
BLOCKS
CONTRADICTS
EXTENDS
CAUSES
USED_BY
APPLIES_TO
SATISFIES
MEASURES
RELATED_TO
```

Use:

```text id="m9c5w3"
RELATED_TO
```

only when no more precise semantic relation is justified.

Avoid meaningless edges such as:

```text id="a8q2r6"
IMPORTANT_TO
CONNECTED_TO
RELEVANT_TO
SIMILAR_TO
```

when the actual relation can be modeled more precisely.

---

## 18. Relationship Direction

Every relation must have explicit direction.

For example:

```text id="r7m3q1"
Course A
  ── PREREQUISITE_OF ──>
Course B
```

must not be interpreted interchangeably with:

```text id="e4x8n6"
Course B
  ── PREREQUISITE_OF ──>
Course A
```

When a reverse traversal is useful, derive the reverse query rather than
creating an incorrect reverse edge.

---

## 19. Symmetric Relations

Some relations may be symmetric.

For example:

```text id="y3k9m4"
A CONTRADICTS B
```

may imply:

```text id="x1p6q8"
B CONTRADICTS A
```

only when the ontology explicitly defines the relation as symmetric.

Do not infer symmetry for every relation.

---

## 20. Inverse Relations

Where ontology defines inverses:

```text id="n7c4w2"
PREREQUISITE_OF
↔
HAS_PREREQUISITE

DEPENDS_ON
↔
DEPENDENCY_OF

SUPPORTED_BY
↔
SUPPORTS
```

Prefer deriving inverse views at query time or maintaining them through the
canonical graph policy.

Never let projections disagree about inverse semantics.

---

## 21. Evidence and Provenance

Every factual relationship should answer:

```text id="v4m8q1"
Where did this relationship come from?

What exactly supports it?

When was it observed?

Who or what is authoritative?
```

Evidence may come from:

```text id="j2x7m5"
canonical records
official documentation
academic papers
course materials
verified project artifacts
source repositories
user-provided information
learning-session evidence
```

---

## 22. Evidence Strength

Use:

```text id="r8c3n6"
STRONG
MODERATE
WEAK
UNCERTAIN
CONTRADICTED
```

Definitions:

```text id="x2m7q4"
STRONG
directly stated or independently verified

MODERATE
supported by multiple contextual sources

WEAK
indirect or partially supported

UNCERTAIN
insufficient evidence

CONTRADICTED
credible evidence directly conflicts
```

Do not promote:

```text id="t5q1p8"
WEAK
```

into:

```text id="g3m9x2"
STRONG
```

without additional evidence.

---

## 23. Evidence vs Confidence

Keep separate:

```text id="p4x8m1"
EVIDENCE_STRENGTH
How directly the source supports the relation.

CONFIDENCE
How confident the system is that the normalized interpretation is correct.
```

A relationship may have:

```text id="q7n2c5"
strong source evidence
but medium confidence because entity identity is ambiguous.
```

---

## 24. Provenance Chain

For important graph claims, preserve:

```text id="n5k8r3"
ENTITY
  ↓
RELATION
  ↓
EVIDENCE
  ↓
SOURCE
```

Example:

```yaml id="c1v7m4"
provenance:
  relation: PREREQUISITE_OF
  source_entity:
  target_entity:
  source_type: official_curriculum
  evidence_ref:
  observed_at:
```

This makes graph reasoning inspectable.

---
