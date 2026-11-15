# context-engineering — §12–23

Contents: 12. Candidate Tool Ranking; 13. Tool Set Compression; 14. L3 — Memory; 15. Memory Admission; 16. Memory Conflict; 17. Memory Freshness; 18. L4 — Repository Context; 19. Repository Context Budget; 20. Context Expansion; 21. L5 — Historical Episodes; 22. Historical Episode Ranking; 23. L6 — External Evidence

## 12. Candidate Tool Ranking

Rank tools by:

```text
task relevance
specificity
required capability
risk compatibility
availability
latency
dependency readiness
```

Avoid selecting tools only because they are semantically related.

A tool should be promoted when it can materially contribute to the current task.

---

## 13. Tool Set Compression

Represent many tools as a capability summary when exact schemas are unnecessary.

Instead of:

```text
tool A full schema
tool B full schema
tool C full schema
...
```

use:

```text
Repository:
  search
  symbol
  architecture

Security:
  scope
  SAST
  DAST
  finding validation
```

Load exact tool schemas only immediately before invocation.

---

## 14. L3 — Memory

Memory retrieval should distinguish:

```text
semantic memory
episodic memory
project memory
preference memory
technical constraints
```

Use:

```text
memory_search
memory_get_context
```

Rank by:

```text
relevance
recency
confidence
project affinity
explicitness
```

---

## 15. Memory Admission

A memory item enters active context only if it:

```text
materially changes execution
resolves ambiguity
prevents repeated work
preserves an important constraint
explains current state
```

Do not load memory simply because it is related.

---

## 16. Memory Conflict

If two memories conflict:

```text
memory A:
  framework = X

memory B:
  framework = Y
```

do not choose silently.

Classify:

```text
CONFLICTING_MEMORY
```

Then resolve using:

```text
current repository evidence
current user statement
current tool output
fresh authoritative source
```

Historical memory must not override current verified state.

---

## 17. Memory Freshness

Every memory should be treated as:

```text
CURRENT
RECENT
STALE
UNKNOWN
```

Stale memory may remain useful as historical context, but must not be presented as
current fact without verification.

---

## 18. L4 — Repository Context

Use:

```text
repo_search
repo_symbol
repo_architecture
repo_diff
```

Retrieve only the minimum code required to answer the task.

Preferred sequence:

```text
search
 ↓
identify file
 ↓
identify symbol
 ↓
read narrow surrounding range
 ↓
expand only if unresolved
```

Never begin by loading an entire repository.

---

## 19. Repository Context Budget

Default:

```text
≤ 200 source lines
```

But preserve:

```text
imports
function signature
relevant branch
error path
type definition
call site
tests
configuration
```

A smaller contiguous section is preferable to many unrelated snippets.

---

## 20. Context Expansion

Expand repository context when:

```text
call graph unresolved
type meaning unclear
implementation depends on helper
authorization behavior unclear
configuration changes behavior
test contract unclear
```

Expansion should be causal:

```text
symbol
↓
direct dependency
↓
relevant caller
↓
relevant configuration
```

not exploratory dumping.

---

## 21. L5 — Historical Episodes

Use Lightning episodes for:

```text
previous attempts
prior failures
successful workflows
known regressions
previous decisions
tool limitations
```

Retrieve:

```text
most relevant recent episodes
```

not merely:

```text
most recent episodes
```

---

## 22. Historical Episode Ranking

Rank by:

```text
task similarity
repository similarity
failure similarity
tool similarity
recency
outcome quality
```

A recent failed attempt can be more valuable than an old successful attempt.

---

## 23. L6 — External Evidence

Use `knowledge_search` only when internal evidence cannot sufficiently answer the
question.

Triggers:

```text
current external fact
missing documentation
unknown API behavior
version-sensitive behavior
standards/reference requirement
independent confirmation
```

Do not browse simply because external sources exist.

---
