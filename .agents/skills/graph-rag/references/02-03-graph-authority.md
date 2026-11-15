# graph-rag — §2–3

## 2. Graph Authority

Maintain one canonical graph data source.

Recommended architecture:

```text id="q2m7v5"
CANONICAL GRAPH
       ↓
   projections
   ├── Neo4j
   ├── search index
   ├── vector index
   └── analytics cache
```

The canonical graph owns:

```text id="s8x1k4"
entity identity
edge semantics
edge provenance
edge status
temporal validity
confidence
```

Indexes and projections are derived representations.

They must never silently invent facts.

---

## 3. Projection Rule

Projection states:

```text id="g6n2p8"
SYNCED
PENDING
FAILED
UNKNOWN
```

A canonical write does not automatically imply that every projection is updated.

Therefore:

```text id="r3x7m1"
CANONICAL_WRITE_COMPLETE
≠
ALL_PROJECTIONS_SYNCED
```

Queries must report projection uncertainty when it materially affects the result.

---
