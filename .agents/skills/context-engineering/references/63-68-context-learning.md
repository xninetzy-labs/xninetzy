# context-engineering — §63–68

Contents: 63. Context Learning; 64. Self-Improvement Guardrail; 65. Lightning Trace; 66. Standard Context Result; 67. Context Readiness States; 68. Standard Decision Gate

## 63. Context Learning

Record:

```text
successful context compositions
failed context compositions
missing-context incidents
wrong-layer incidents
stale-context incidents
redundant retrieval
contradiction events
```

Learning outputs may include:

```text
better routing tags
better skill selection
better cache keys
better memory queries
better repository query patterns
better budget allocation
better compaction rules
```

Never automatically modify:

```text
authorization
security policy
scope policy
credential policy
system-level safety controls
```

---

## 64. Self-Improvement Guardrail

Context self-improvement may optimize:

```text
retrieval
ranking
compression
routing
caching
recomputation
deduplication
```

It may not optimize by:

```text
dropping safety rules
dropping authorization evidence
suppressing contradictions
hiding tool failures
bypassing approval
removing audit events
```

---

## 65. Lightning Trace

Start:

```text
lightning_episode_start
```

Record:

```text
intent
selected layers
selected tools
retrieved memories
retrieved repository context
dropped items
compaction
contradictions
budget changes
recompute events
execution transitions
```

Use:

```text
lightning_record_action
```

for meaningful state transitions.

Do not log secrets.

---

## 66. Standard Context Result

Return:

```yaml
context_engineering:
  task_id:
  intent:

  layers:
    L0: []
    L1: []
    L2: []
    L3: []
    L4: []
    L5: []
    L6: []

  selected:
    skills: []
    tools: []

  evidence:
    sufficient:
    ledger: []

  conflicts: []

  budget:
    hard_limit:
    used_tokens:
    remaining_tokens:
    reserved_tokens:

  dropped:
    - item:
      layer:
      reason:

  stale:
    - item:

  recomputed:
    - layer:

  compacted:
    before_tokens:
    after_tokens:

  state:
    ready:
    blocked:
    uncertain:
```

---

## 67. Context Readiness States

#### READY

Enough trustworthy context exists to execute.

#### PARTIAL

Execution is possible with known limitations.

#### BLOCKED

Required context or authorization is missing.

#### UNCERTAIN

Evidence conflicts or confidence is insufficient.

#### DEGRADED

Execution can continue, but tool/context capability is reduced.

---

## 68. Standard Decision Gate

Before execution:

```text
1. Is the intent understood?
2. Is the target understood?
3. Are constraints known?
4. Are required skills selected?
5. Are required tools available?
6. Is context sufficiently fresh?
7. Are contradictions resolved?
8. Is evidence sufficient?
9. Is approval required?
10. Is the planned action within scope?
```

Only then:

```text
EXECUTE
```

---
