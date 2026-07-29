---
name: graph-rag
description: Model and query relationships among knowledge, learning concepts, goals, tasks, notes, research, and projects. Use for concept maps, prerequisite reasoning, explaining why entities are connected, linking verified research to a roadmap, and Graph RAG context that requires relationships rather than plain text similarity.
---

# Graph RAG workflow

Use graph behavior only when relationships materially improve the answer.

1. Search existing nodes and edges before adding anything.
2. Reuse canonical entities instead of creating near-duplicates.
3. Add an edge only when its source, target, relation, and evidence are explicit.
4. Keep learning prerequisites inside the typed concept graph when that domain owns the relation.
5. Use Graph RAG for cross-domain links such as research-to-roadmap or note-to-topic.
6. Explain the path supporting a conclusion.

Do not turn retrieval similarity into a factual relationship. Do not write broad graph changes without approval.

Return:

- relevant nodes;
- relationship path;
- supporting evidence;
- missing or uncertain links;
- proposed write actions separately from completed reads.
