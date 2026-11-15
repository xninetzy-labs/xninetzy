# graph-rag — §38–47

Contents: 38. Phase 06 — INDEX; 39. Retrieval Modes; 40. Exact Relation Query; 41. Neighborhood Query; 42. Multi-Hop Path Query; 43. Path Selection; 44. Path Confidence; 45. Unsupported Bridge Detection; 46. Hybrid Retrieval; 47. Retrieval Budget

## 38. Phase 06 — INDEX

After canonical graph changes:

```text id="n6m3w8"
canonical write
→ projection update
→ verify projection
```

Possible projection states:

```text id="q2x7p5"
SYNCED
PENDING
FAILED
UNKNOWN
```

Do not claim index freshness without verification.

---

## 39. Retrieval Modes

Use the narrowest appropriate mode:

```text id="v8m1q4"
EXACT_RELATION
NEIGHBORHOOD
ONE_HOP
MULTI_HOP_PATH
DEPENDENCY_CHAIN
REVERSE_DEPENDENCY
SUBGRAPH
TEMPORAL_PATH
HYBRID_VECTOR_GRAPH
```

---

## 40. Exact Relation Query

Example:

```text id="m7q2x5"
Course A
→ PREREQUISITE_OF
→ ?
```

Return only the relevant edges and evidence.

Do not expand the graph unnecessarily.

---

## 41. Neighborhood Query

Example:

```text id="p4x8n2"
What concepts are connected to X?
```

Return:

```text id="q9m3v7"
direct neighbors
relation types
evidence
confidence
```

Consider edge direction explicitly.

---

## 42. Multi-Hop Path Query

Example:

```text id="c5r8m1"
Goal
→ requires
→ Skill
→ supported_by
→ Course
```

The path should be represented as:

```text id="x7n2q4"
NODE
→ EDGE
→ NODE
→ EDGE
→ NODE
```

Every important edge should remain individually inspectable.

---

## 43. Path Selection

Prefer paths with:

```text id="k6m3x9"
strong evidence
high identity confidence
fewer unsupported assumptions
shorter length when equally informative
current temporal validity
fewer contradictions
```

Do not choose a longer path merely because it returns more nodes.

More graph traversal is not automatically better reasoning.

---

## 44. Path Confidence

A path is only as strong as its weakest critical link.

Conceptually:

```text id="r5x9m2"
PATH_CONFIDENCE
≈
minimum(
  edge confidence,
  entity identity confidence,
  temporal validity confidence
)
```

A production implementation may use a richer formula, but it must not hide a weak
edge behind many strong edges.

---

## 45. Unsupported Bridge Detection

If a path requires:

```text id="j3m7q8"
A → X → B
```

but the `X → B` relationship is unsupported:

```text id="w2n8c5"
do not present A → B as established.
```

Instead:

```text id="p6m4x1"
PATH_INCOMPLETE
```

or:

```text id="y7q3n9"
RELATIONSHIP_UNSUPPORTED
```

---

## 46. Hybrid Retrieval

Use:

```text id="c8m1x5"
vector search
+
graph retrieval
```

when:

```text id="q4n8m2"
semantic discovery identifies candidates
and
explicit relationships determine the answer
```

Pipeline:

```text id="m7x3p9"
VECTOR SEARCH
      ↓
CANDIDATES
      ↓
CANONICALIZE
      ↓
GRAPH TRAVERSAL
      ↓
EVIDENCE
      ↓
REASON
```

Never replace graph validation with vector similarity.

---

## 47. Retrieval Budget

Bound:

```text id="x2m8q4"
max nodes
max edges
max path length
max candidate entities
max source expansion
```

Prefer:

```text id="r9c3m6"
smallest subgraph that answers the question
```

over:

```text id="h5n7p2"
entire graph retrieval
```

This protects context and improves reasoning precision.

---
