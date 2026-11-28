# Full context contract

Preserved entrypoint guidance. Paths below are relative to the skill root; load only needed sections.

# context-engineering

The Xninetzy harness must never dump the full tool, skill, memory, repository,
and historical surface into every prompt.

The core problem is:

```text
large capability surface
        ↓
large irrelevant context
        ↓
high token cost
        ↓
lower signal density
        ↓
worse reasoning
```

The solution is:

```text
intent
  ↓
minimal sufficient context
  ↓
evidence-aware execution
  ↓
incremental expansion only when justified
```

Core principle:

> **Load the smallest sufficient context that can support the current decision.**

Second principle:

> **Context is evidence, not decoration.**

Third principle:

> **More context is not automatically better context.**

---

# 1. Context Objectives

The context engine optimizes for:

```text
relevance
freshness
confidence
coverage
provenance
token efficiency
decision value
```

Subject to:

```text
hard token budget
tool latency
execution risk
task complexity
evidence requirements
```

Do not optimize only for token minimization.

A missing critical constraint is more expensive than several extra relevant lines.

---

# 2. Context Layers

Use seven logical layers.

| Layer | Source                       |        Default Budget | Purpose                |
| ----- | ---------------------------- | --------------------: | ---------------------- |
| L0    | Current user intent          |       1 semantic unit | task objective         |
| L1    | Immediate state/observations |            ≤ 10 items | active local state     |
| L2    | Tools + skills metadata      |       ≤ 12 candidates | capability routing     |
| L3    | Memory                       |    ≤ 5 promoted items | durable context        |
| L4    | Repository/code              |           ≤ 200 lines | implementation context |
| L5    | Historical episodes          | ≤ 5 promoted episodes | precedent              |
| L6    | External evidence            |  ≤ 5 promoted sources | unresolved facts       |

Budgets are defaults.

The engine may adapt them within the global budget when task complexity requires it.

---

# 3. Global Context Budget

Maintain:

```yaml
context_budget:
  hard_token_limit:
  reserved_tokens:
    system_safety:
    user_intent:
    output:
  available_tokens:
  used_tokens:
  remaining_tokens:
```

Never spend the full theoretical prompt budget blindly.

Reserve capacity for:

```text
tool outputs
new evidence
errors
verification
final response
```

Recommended behavior:

```text
reserve 15-25%
```

of the active context window for newly arriving evidence.

---

# 11. Progressive Disclosure

For skills:

```text
Level 1:
name + description + triggers

Level 2:
relevant metadata + core instructions

Level 3:
relevant references

Level 4:
specific reference section only
```

For tools:

```text
Level 1:
name + capability

Level 2:
input schema

Level 3:
detailed parameter metadata

Level 4:
implementation/reference details only when necessary
```

Only promote deeper information when required.

---

# 40. Evidence Sufficiency

Before execution ask:

```text
Do we know enough to safely perform this action?
```

Possible:

```text
SUFFICIENT
PARTIAL
INSUFFICIENT
CONTRADICTED
```

Examples:

```text
code formatting
  -> L0-L2 may be sufficient

architecture review
  -> L4 required

security active test
  -> scope + authorization + relevant target context required

production write
  -> target + authorization + action + approval + verification path required
```

---

# 41. Context Gate

Before tool execution:

```text
IF required context missing
    -> retrieve

IF context contradictory
    -> resolve

IF scope missing
    -> block action

IF evidence insufficient for requested risk
    -> retrieve more

IF still insufficient
    -> return PARTIAL / BLOCKED
```

Never compensate for missing context by increasing model confidence.

---

# 69. Minimal Context Principle

For each task, the engine should seek:

```text
Minimum Sufficient Context (MSC)
```

defined as:

> The smallest context set that allows the current task to execute or make its
> next decision without violating correctness, evidence, or safety requirements.

The engine should not load the next layer simply because it exists.

---

# 79. Final Completion Contract

A context-engineering cycle is complete when:

```text
[ ] intent normalized
[ ] task object created
[ ] candidate skills identified
[ ] candidate tools identified
[ ] required layers determined
[ ] relevant memories ranked
[ ] repository context bounded
[ ] historical context bounded
[ ] external evidence evaluated where necessary
[ ] provenance attached
[ ] contradictions checked
[ ] freshness checked
[ ] context budget enforced
[ ] critical constraints preserved
[ ] redundant context removed
[ ] evidence sufficiency evaluated
[ ] approval requirement evaluated
[ ] minimal sufficient context assembled
[ ] Lightning trace updated
```

---

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/04-10-context-value-model.md` — §4–10: Context Value Model, Criticality Override, L0 — Intent, Intent Normalization, L1 — Immediate State, State Classification, L2 — Tool and Skill Routing
- `references/12-23-candidate-tool-ranking.md` — §12–23: Candidate Tool Ranking, Tool Set Compression, L3 — Memory, Memory Admission, Memory Conflict, Memory Freshness, L4 — Repository Context, Repository Context Budget, Context Expansion, L5 — Historical Episodes, Historical Episode Ranking, L6 — External Evidence
- `references/24-33-external-evidence-ranking.md` — §24–33: External Evidence Ranking, Provenance, Evidence Ledger, Contradiction Detection, Source-of-Truth Priority, Freshness Model, Cache Awareness, Branch-Aware Context, Scope-Aware Context, Context Compaction
- `references/34-39-compaction-record.md` — §34–39: Compaction Record, Context Debt, Context Recompute Threshold, Recompute Levels, Context Invalidation, Risk-Adaptive Context
- `references/42-53-execution-spine.md` — §42–53: Execution Spine, Tool Call Context, Tool Output Reintegration, Output Compression, Scanner / Log Context, Context Isolation, Secret Isolation, Context Firewall, Memory vs Evidence, Historical Episode vs Current State, Multi-Agent Context, Sub-Agent Return Contract
- `references/54-62-context-merge.md` — §54–62: Context Merge, Duplicate Suppression, Staleness Detection, Wrong-Layer Detection, Context Anti-Patterns, Recovery, Context Budget Overflow, Context Quality Metrics, Context Efficiency
- `references/63-68-context-learning.md` — §63–68: Context Learning, Self-Improvement Guardrail, Lightning Trace, Standard Context Result, Context Readiness States, Standard Decision Gate
- `references/70-78-progressive-expansion.md` — §70–78: Progressive Expansion, Example — Simple Code Question, Example — Architecture Review, Example — Security Assessment, Example — Debugging After Failure, Example — Large Refactor, Context Handoff, Context Reference Pointers, Context Materialization
- `references/80-final-principle.md` — §80: Final Principle
