# graph-rag — §88–90

## 88. Golden Hybrid Retrieval Workflow

```text id="q8m3x5"
USER QUERY
   ↓
VECTOR / SEMANTIC DISCOVERY
   ↓
CANDIDATE ENTITIES
   ↓
CANONICALIZE
   ↓
GRAPH FILTER
   ↓
NARROW TRAVERSAL
   ↓
EVIDENCE RETRIEVAL
   ↓
PATH REASONING
   ↓
ANSWER
```

Vector retrieval discovers candidates.

The graph establishes explicit relationships.

Evidence supports the resulting claim.

---

## 89. Golden Mutation Workflow

```text id="m7x2q4"
PROPOSE RELATION
      ↓
IDENTITY CHECK
      ↓
ONTOLOGY CHECK
      ↓
EVIDENCE CHECK
      ↓
TEMPORAL CHECK
      ↓
CONTRADICTION CHECK
      ↓
AUTHORIZATION
      ↓
APPLY CANONICAL WRITE
      ↓
VERIFY CANONICAL STATE
      ↓
UPDATE PROJECTIONS
      ↓
VERIFY PROJECTION
      ↓
AUDIT
```

Broad or destructive operations must not skip authorization.

---

## 90. Golden Path Explanation

For important multi-hop answers:

```text id="x3m8q1"
QUESTION
 ↓
ENTITY A
 ↓
RELATION 1 + EVIDENCE
 ↓
ENTITY B
 ↓
RELATION 2 + EVIDENCE
 ↓
ENTITY C
 ↓
DERIVED CONCLUSION
 ↓
CONFIDENCE / GAPS
```

This is the preferred explanation format for inspectable graph reasoning.

---
