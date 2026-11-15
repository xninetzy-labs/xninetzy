# context-engineering — §54–62

Contents: 54. Context Merge; 55. Duplicate Suppression; 56. Staleness Detection; 57. Wrong-Layer Detection; 58. Context Anti-Patterns; 59. Recovery; 60. Context Budget Overflow; 61. Context Quality Metrics; 62. Context Efficiency

## 54. Context Merge

When multiple agents return results:

```text
result A
+
result B
+
result C
```

perform:

```text
normalize
↓
deduplicate
↓
detect contradiction
↓
rank evidence
↓
merge facts
```

Do not concatenate outputs blindly.

---

## 55. Duplicate Suppression

Detect duplicate context based on:

```text
semantic similarity
source
timestamp
identifier
content hash
```

If the same fact appears repeatedly:

```text
retain one canonical representation
```

and record:

```text
duplicate_count
```

---

## 56. Staleness Detection

Possible stale indicators:

```text
branch changed
commit changed
package version changed
API version changed
tool version changed
deadline changed
environment changed
authorization expired
```

When detected:

```text
mark stale
invalidate dependent context
recompute
```

---

## 57. Wrong-Layer Detection

A context item may belong to the wrong layer.

Examples:

```text
tool implementation details
  loaded into L1

large repository dump
  loaded into L2

historical memory
  treated as current fact

external webpage
  treated as authoritative project rule
```

Classify:

```text
WRONG_LAYER_RANKING
```

Record the correction opportunity.

---

## 58. Context Anti-Patterns

Never:

```text
dump entire tool catalog
dump every skill
load whole repository
load all memories
paste complete previous episodes
repeat full scanner output
mix stale and current state
treat model assumptions as facts
```

---

## 59. Recovery

### No tool matches

```text
broaden capability tags
↓
skill suggestion fallback
↓
manual metadata inspection
```

### No memory matches

```text
semantic search
↓
episodic search
↓
repository/project context
```

### No repository result

```text
broaden query
↓
search by symbol
↓
architecture inventory
```

### Insufficient evidence

```text
promote next evidence layer
```

Do not automatically broaden to the entire context surface.

---

## 60. Context Budget Overflow

When overflow occurs:

```text
1. remove duplicates
2. remove superseded observations
3. compress verbose outputs
4. reduce low-value history
5. reduce broad tool metadata
6. preserve critical constraints
7. preserve evidence references
8. preserve unresolved contradictions
```

Never drop:

```text
scope
authorization
critical user constraint
target identifier
required evidence
active error
approval state
```

without explicit state preservation.

---

## 61. Context Quality Metrics

Track:

```yaml
context_metrics:
  total_tokens:
  useful_tokens:
  duplicated_tokens:
  stale_tokens:
  evidence_tokens:
  instruction_tokens:
  tool_metadata_tokens:
  repository_tokens:
  memory_tokens:
  history_tokens:
  external_tokens:

  compression_ratio:
  evidence_density:
  context_reuse_ratio:
  recomputation_count:
  dropped_items:
```

Useful metrics:

```text
evidence_density
=
evidence_tokens / total_tokens

duplicate_ratio
=
duplicated_tokens / total_tokens

reuse_ratio
=
reused_context_tokens / total_context_tokens
```

These metrics are optimization signals, not quality guarantees.

---

## 62. Context Efficiency

The engine should continuously optimize:

```text
same task
less context
same or better decision quality
```

Never optimize toward:

```text
minimum tokens
```

when it reduces evidence sufficiency.

---
