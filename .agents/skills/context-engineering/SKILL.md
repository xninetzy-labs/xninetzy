---
name: context-engineering
description: Layered context construction for the Xninetzy MCP harness. Avoids the "232-tool schema dump every turn" antipattern that wastes prompt cache tokens. Routes user intent to the smallest correct subset of skills + tools + memory + repo context + historical episodes, ordered by L0-L6 priority. Use on every non-trivial request so the harness reasons on minimal evidence instead of the full capability surface.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: harness
  priority: P0
  required_tools:
    - tool_catalog
    - meta_for
    - skill_suggest_for_request
    - skill_list
    - skill_get
    - memory_search
    - memory_get_context
    - lightning_episode_start
    - lightning_record_action
  optional_tools:
    - os_inbox
    - repo_search
    - knowledge_search
    - todo_tool
  trigger_conditions:
    - any request that may involve multiple tool families
    - any request whose previous attempt produced context blow-up
    - recompute-layer threshold crossed (default L2 every turn)
  prerequisites:
    - target intent
    - XNINETZY_TOOL_TIMEOUT_SECONDS set
    - tool_catalog metadata available via `meta_for`
---

# context-engineering

The 232-tool catalog dominates every prompt if dumped naively. This
skill enforces a layered construction so each turn only loads what
the intent actually needs.

## Layered model

| Layer | Source                                  | Budget             |
|-------|-----------------------------------------|--------------------|
| L0    | user intent (free text)                  | 1 item             |
| L1    | immediate observations / last messages   | ≤ 10 items         |
| L2    | relevant tool metadata                   | ≤ 12 candidates    |
| L3    | relevant memories (semantic + episodic) | ≤ 5 items          |
| L4    | relevant repository / code context       | ≤ 200 lines        |
| L5    | relevant historical episodes             | ≤ 5 episodes       |
| L6    | external evidence (web, knowledge base) | ≤ 5 sources        |

The skill promotes information only when it increases decision quality.
It deprioritizes duplicates, stale observations, low-value verbose
output, and irrelevant tool descriptions.

## Operating procedure

```
INTENT
   ↓
DECOMPOSE
   ↓
TAG_QUERY
   ↓
LAYER_BUILD
   ↓
BUDGET_ENFORCE
   ↓
PROMOTE_OR_TRUNCATE
```

### 1. INTENT

State the user's intent in one sentence. If the intent is too vague to
be useful (`"do the thing"`), refuse to proceed and ask the owner for
a measurable intent.

### 2. DECOMPOSE

Convert the intent into a structured Task object:

```
Task {
    goal: <string>
    context: <string>
    constraints: <list of strings>
    assumptions: <list of strings>
    required_evidence: <list of strings>
    candidate_tools: <list of strings>
    candidate_skills: <list of strings>
    dependencies: <list of strings>
    execution_steps: <list of strings>
    verification_steps: <list of strings>
    rollback_strategy: <string>
    risk_level: low|medium|high|critical
    approval_requirement: bool
}
```

The harness stores this and uses it as the spine of every subsequent
state transition.

### 3. TAG_QUERY

Ask `tool_catalog(tags=<derived>, risk=<derived>, limit=<bounded>)` for a
filtered slice. Tags come from candidate task families — for example,
"modify code" implies tags=`{"repo","learning","security"}`.

Prefer the **filtered slice** over the entire catalog. Default limit
matches the L2 budget (12).

### 4. LAYER_BUILD

Pull each layer in order, only as far as needed:

- **L0**: parse the user message, isolate intent, constraints, expected
  evidence
- **L1**: most recent 10 messages / observations only
- **L2**: tag-filtered tools + selected skills (progressive disclosure:
  body unless body > budget, in which case references only)
- **L3**: `memory_search` over semantic + episodic with relevance × recency
  ranking
- **L4**: `repo_search` for relevant symbols and files; cap at 200 lines
- **L5**: most recent 5 relevant Lightning episodes
- **L6**: `knowledge_search` for external evidence when L3-L5 are
  insufficient

### 5. BUDGET_ENFORCE

Each layer has a hard budget. If a layer overflows:

- truncate to budget
- prefer newest first for time-sensitive layers (L1, L3, L5)
- prefer highest-confidence for evidence layers (L6)
- never silently drop on overflow; record the drop in the Lightning trace

### 6. PROMOTE_OR_TRUNCATE

A layer is promoted to the harness only if:

- it strictly informs the current task
- it is more recent or more relevant than alternatives already promoted
- the cost of including it (token count) is justified by the gain in
  decision quality

Truncate aggressively; never lose identifiers, constraints, errors, or
unresolved evidence.

## Output contract

A context-engineering invocation returns:

```
context-engineering result
intent: <string>
layers: {
    L0: [...], L1: [...], L2: [...],
    L3: [...], L4: [...], L5: [...], L6: [...]
}
budget_used: {
    L0: <int>, L1: <int>, L2: <int>, ...
    total_tokens: <int>
}
dropped: <list of dropped items with reason>
```

## Failure classification

| Class                          | Action                                |
|--------------------------------|---------------------------------------|
| `INTENT_TOO_VAGUE`             | refuse; require measurable intent     |
| `TOOL_NOT_FOUND`                | failover to `skill_suggest_for_request` |
| `CONTEXT_BUDGET_EXCEEDED`      | truncate; log in Lightning trace      |
| `EVIDENCE_INSUFFICIENT`         | promote L6 layer; require explicit owner approval for high-stakes |
| `WRONG_LAYER_RANKING`           | escalate to `skill-improvement-opportunity-logger` |

## Recovery

- tool returns 0 results → re-issue with broader tag filter, default
  no filter for read-only tools
- memory search returns 0 results → fallback to episodic search, then
  to `repo_search`
- budget exhaustion → drop lowest-priority layer first, never L6

## See also

- `memory-management` — L3 layer construction
- `repo-context-packaging` — L4 layer construction
- `structured-project-execution` — durable spine for the Task object
- `multi-agent-orchestration` — how to delegate sub-context construction
  to sub-agents
