# context-engineering — §70–78

Contents: 70. Progressive Expansion; 71. Example — Simple Code Question; 72. Example — Architecture Review; 73. Example — Security Assessment; 74. Example — Debugging After Failure; 75. Example — Large Refactor; 76. Context Handoff; 77. Context Reference Pointers; 78. Context Materialization

## 70. Progressive Expansion

When the minimum context is insufficient:

```text
MSC
 ↓
+ highest-value missing evidence
 ↓
re-evaluate
 ↓
+ next evidence if still necessary
```

This creates:

```text
bounded expansion
```

rather than:

```text
full-context fallback
```

---

## 71. Example — Simple Code Question

User:

```text
Why does function X fail?
```

Likely context:

```text
L0 intent
L1 current error
L2 repo_search + repo_symbol
L4 function + caller
```

Do not load:

```text
L3 full memory
L5 entire history
L6 web
```

unless needed.

---

## 72. Example — Architecture Review

User:

```text
Is this module allowed to import that module?
```

Context:

```text
L0 intent
L1 current files
L2 architecture skill
L4 import graph
L5 previous architecture decision if relevant
```

Need:

```text
declared architecture
dependency edge
source location
```

No full repository dump.

---

## 73. Example — Security Assessment

User:

```text
Scan my staging API.
```

Context:

```text
L0 intent
L1 current environment
L2 security skill + tools
L3 relevant project security constraints
L4 API/repository context
L5 prior security assessment
L6 current external documentation when necessary
```

Required before active execution:

```text
scope
authorization
target
profile
tool readiness
```

---

## 74. Example — Debugging After Failure

Initial:

```text
tool A
```

fails.

Do not rebuild everything.

Instead:

```text
existing context
+
new error
+
tool metadata
```

Then recompute only affected layers.

Example:

```text
L2 recompute
```

without invalidating unrelated:

```text
L3 memory
L4 repository
```

unless the failure changes their relevance.

---

## 75. Example — Large Refactor

For architecture-sensitive work:

```text
L0 intent
L1 active branch state
L2 architecture/refactor skills
L3 prior decisions
L4 repository architecture
L5 historical refactor episodes
L6 official framework migration docs when applicable
```

Preserve:

```text
base
head
merge_base
architecture contract
dependency graph
changed modules
```

---

## 76. Context Handoff

When another skill takes over:

```text
context-engineering
    ↓
selected skill
    ↓
minimal handoff
```

Handoff contains:

```yaml
handoff:
  intent:
  constraints:
  target:
  required_evidence:
  selected_context:
  unresolved:
  approval_state:
  relevant_references:
```

Do not resend all raw retrieval results.

---

## 77. Context Reference Pointers

Prefer compact references:

```text
repo:
  src/api/users.ts:42-87

memory:
  mem_123

episode:
  ep_456

evidence:
  ev_789

tool:
  security_run_zap
```

rather than duplicating complete source content.

---

## 78. Context Materialization

Only materialize full content when needed for:

```text
exact code reasoning
exact quote
exact configuration
exact payload construction
exact schema interpretation
```

Otherwise retain:

```text
pointer
summary
evidence metadata
```

---
