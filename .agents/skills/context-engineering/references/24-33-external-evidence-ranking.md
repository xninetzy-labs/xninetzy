# context-engineering — §24–33

Contents: 24. External Evidence Ranking; 25. Provenance; 26. Evidence Ledger; 27. Contradiction Detection; 28. Source-of-Truth Priority; 29. Freshness Model; 30. Cache Awareness; 31. Branch-Aware Context; 32. Scope-Aware Context; 33. Context Compaction

## 24. External Evidence Ranking

Prefer:

```text
primary documentation
official specifications
official source repository
authoritative standards
high-quality technical references
```

Rank by:

```text
authority
freshness
directness
consistency
```

Preserve source identity and timestamp.

---

## 25. Provenance

Every promoted item should carry:

```yaml
provenance:
  source:
  retrieved_at:
  evidence_type:
  confidence:
  freshness:
  reference:
```

Example:

```text
repo_search:
  source = repository
  evidence_type = code
```

or:

```text
knowledge_search:
  source = official documentation
  evidence_type = external
```

Do not collapse different evidence types into a generic "context" bucket.

---

## 26. Evidence Ledger

Maintain a lightweight evidence ledger:

```yaml
evidence:
  - id:
    claim:
    source:
    confidence:
    freshness:
    status:
      supports
      contradicts
      unresolved
```

This allows the harness to reason about:

```text
what is known
what is assumed
what is disputed
what is missing
```

---

## 27. Contradiction Detection

Before execution, compare promoted evidence for contradictions.

Examples:

```text
memory says Node 20
repository says Node 22

OpenAPI says GET
implementation exposes POST

previous episode says tool available
doctor says tool missing
```

Classify:

```text
CONTRADICTION
```

Do not silently merge contradictory facts.

Resolve using source-of-truth priority.

---

## 28. Source-of-Truth Priority

Generic priority:

```text
current explicit user instruction
    >
current authoritative tool/repository evidence
    >
current official documentation
    >
current project state
    >
recent trusted memory
    >
historical episodes
    >
generic assumptions
```

Domain-specific skills may establish a stricter hierarchy.

---

## 29. Freshness Model

Every context item gets:

```text
observed_at
retrieved_at
expires_at
freshness_class
```

Possible freshness:

```text
LIVE
FRESH
RECENT
STALE
EXPIRED
UNKNOWN
```

Time-sensitive facts should be revalidated rather than inherited from memory.

---

## 30. Cache Awareness

Before retrieving data:

```text
check whether useful cached context exists
```

Use cache only when:

```text
fresh enough
same target
same scope
same repository state
same task family
```

Do not reuse context across incompatible:

```text
branch
environment
account
tenant
authorization state
```

---

## 31. Branch-Aware Context

For repository work, cache keys should include:

```text
repository
branch
commit
merge_base
working_tree_state
```

A cached analysis from:

```text
main@abc123
```

must not silently become evidence for:

```text
feature@def456
```

unless the relevant graph/context is known unchanged.

---

## 32. Scope-Aware Context

Security-sensitive context must include:

```text
scope_id
target
environment
authorization session
```

Do not reuse:

```text
staging authorization
```

as:

```text
production authorization
```

---

## 33. Context Compaction

When context approaches budget:

```text
raw context
 ↓
facts
 ↓
constraints
 ↓
decisions
 ↓
evidence
 ↓
open questions
 ↓
compact state
```

Preserve:

```text
identifiers
paths
constraints
errors
evidence references
unresolved contradictions
```

Remove:

```text
repeated prose
duplicate tool descriptions
superseded observations
verbose scanner output
already-summarized history
```

---
