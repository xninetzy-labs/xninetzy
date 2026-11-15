# graph-rag — §76–77

## 76. Path Limits

Use bounded traversal:

```text id="w7m2x4"
MAX_HOPS
MAX_NODES
MAX_EDGES
MAX_BRANCHING
MAX_SOURCES
```

If bounds are reached:

```text id="q1n8p6"
TRAVERSAL_LIMIT_REACHED
```

Do not silently truncate and present the result as exhaustive.

---

## 77. Incomplete Graph Results

Use:

```text id="m3x7q2"
COMPLETE
PARTIAL
UNKNOWN
```

Example:

```text id="k8p2v5"
PARTIAL:
The first two dependency levels were resolved, but a third-party package source
could not be verified.
```

This is more trustworthy than pretending graph traversal was complete.

---
