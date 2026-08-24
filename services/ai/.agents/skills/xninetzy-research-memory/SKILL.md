---
name: xninetzy-research-memory
description: Persist and resume research manifests, sources, claims, worker results, synthesis, and unresolved gaps.
metadata:
  owner: xninetzy
  version: "1.0.0"
---

# Research Memory

Create one research session ID.

Store:

```yaml
session_id:
question:
scope:
manifest:
sources:
claims:
counterevidence:
worker_results:
synthesis_status:
unresolved:
next_queries:
artifacts:
```

Deduplicate sources by DOI, canonical URL, repository ID, or content hash.

Do not lose access status.

On resume:

1. load manifest;
2. inspect completed worker results;
3. verify whether recent facts became stale;
4. continue only unresolved subquestions;
5. avoid rerunning identical searches without justification.
