---
name: "memory-management"
description: "Lifecycle governance for Xninetzy memory layers. Restricts what gets stored, where it lives (working / episodic / semantic / procedural / failure / tool / skill / security / research), when it gets promoted across layers, and when it retires. Avoids memory pollution from speculation, temporary noise, raw tool dumps, redundant facts, or unsupported claims. Use on every `memory_add`, after every successful or failed complex episode, and on a periodic cadence to retire stale entries."
metadata:
  author: "xninetzy"
  version: "1.0.0"
  scope: "harness"
  priority: "P0"
  required_tools:
    - memory_add
    - memory_search
    - memory_forget
    - memory_list
    - memory_update_tool
    - lightning_record_action
    - lightning_record_outcome
    - lightning_episode_finish
  optional_tools:
    - action_policy_evaluate
    - os_inbox
    - hitl_request_approval
  trigger_conditions:
    - a complex episode completes (success or failure)
    - the operator asks to capture a preference, rule, or fact
    - a periodic retention sweep runs (default weekly)
    - a memory retrieval returns results that look stale
  prerequisites:
    - storage layer is identified
    - policy table for memory scoping is loaded (in `xninetzy/os/memory/`)
---

# memory-management

Memory is only valuable when it survives scrutiny. This skill enforces
a measured lifecycle so the harness learns from real evidence, not
from noise.

## Layer taxonomy

| Layer          | Scope                                  | Storage                        |
|----------------|----------------------------------------|--------------------------------|
| `working`      | current task only                      | in-memory / ephemeral SQLite   |
| `episodic`     | one episode, one tool sequence         | `lightning` episode log         |
| `semantic`     | stable fact about the project          | `memory` table                  |
| `procedural`   | reusable procedure that worked         | `memory_procedure_store`        |
| `failure`      | known failure mode + recovery          | `memory_failure_store`          |
| `tool`         | per-tool historical performance        | `memory_tool_store`             |
| `skill`        | which skills worked for which intent   | `memory_skill_store`            |
| `security`     | authorized assets + blocked actions    | `memory_security_store`         |
| `research`     | cited sources + confidence + contradictions | `memory_research_store`     |

Each observation gets a structured envelope:

```
MemoryEntry {
    content: <string>
    type: <layer>
    source: <tool_name | skill_name | episode_id | owner>
    timestamp: <ISO8601>
    provenance: <sha256 or URL>
    confidence: 0.0..1.0
    scope: <chat_id | owner | global>
    freshness_ttl: <seconds>
    verification_status: unverified | verified | contested
    usefulness: 0.0..1.0
    related_task: <task_id | None>
    related_tools: [<tool_name>, ...]
}
```

## Operating procedure

```
OBSERVE
   ↓
CLASSIFY
   ↓
VERIFY
   ↓
PROMOTE_OR_SKIP
   ↓
PERSIST
   ↓
REEVALUATE
```

### 1. OBSERVE

The skill is invoked from three sources:

- **post-episode**: at the end of every Lightning episode, the harness
  offers a structured observation envelope; the skill decides whether
  it survives
- **owner-direct**: the operator explicitly says "remember this", then
  the skill classifies, verifies, persists
- **sweep**: a periodic retention job scans entries past their TTL and
  either retires or downgrades them

### 2. CLASSIFY

Map the observation to a single layer:

- `working` for current-task short-lived state, never persisted beyond
  episode
- `episodic` for a tool-call sequence that worked; persisted to
  Lightning, not user-visible
- `semantic` for a stable fact about the project (a path, a convention,
  a constant); only promoted when reproduced or verified at least once
- `procedural` for a multi-step recipe that completed and was verified
  end-to-end
- `failure` for any task that hit a non-recoverable failure mode
- `tool` for runtime observations about an individual MCP tool
  (latency, success rate, schema oddness)
- `skill` for "skill X worked / did not work on intent Y"
- `security` for "asset Z is in scope", "action A is permanently blocked"
- `research` for "source P supports claim C with confidence K"

### 3. VERIFY

Promote a candidate to a non-`working` layer only with evidence:

- `semantic` requires either a stable test result, a manual owner
  confirmation, or appearance in ≥ 2 independent episodes
- `procedural` requires a successful execution + an evidence note
- `failure` requires a reproducible failure mode
- `security` requires an explicit owner approval; the gate is
  `hitl_request_approval`
- `research` requires a citation source; confidence must be explicit

No promotion without evidence.

### 4. PROMOTE_OR_SKIP

Skips (do not store):

- speculation ("this might be true")
- temporary noise (single-episode signals with no reproduction)
- raw tool dumps (decompose first into `failure` or `procedural`)
- redundant facts (already in `semantic` or higher)
- unsupported claims (no source, no verification)

Promotes only when the layer is correct AND verification passed.

### 5. PERSIST

Dispatch to the appropriate MCP tool:

- `memory_add` for `semantic` and `skill`
- `memory_procedure_store` for `procedural`
- `memory_failure_store` for `failure`
- `memory_tool_store` for `tool`
- `memory_security_store` for `security` (after approval)
- `memory_research_store` for `research`

Always include `confidence`, `source`, `freshness_ttl`, and
`verification_status` in the persisted entry.

### 6. REEVALUATE

A periodic sweep:

- entries past `freshness_ttl` → downgrade to `monitoring` tier
- entries with `usefulness < 0.2` after N reads → retire
- entries contradicted by later evidence → mark `contested`
- entries no longer invoked for 30+ days → retire

Sweep logs every retire / downgrade to durable store.

## Output contract

A memory-management invocation returns:

```
memory-management verdict
entry: <preview>
target_layer: <layer>
verification_path: <list>
action: store | skip | retire | downgrade
ttl_seconds: <int>
related_artifacts: <list>
```

## Failure classification

| Class                          | Action                                |
|--------------------------------|---------------------------------------|
| `UNVERIFIED_PROMOTION`        | refuse; require verification          |
| `DUPLICATE_ENTRY`             | merge into existing entry             |
| `STORAGE_LIMIT`                | retire oldest before storing          |
| `CONTRADICTED_FACT`           | mark contested; escalate             |

## Recovery

- failed persist → retry once with backoff; second failure → log to
  Lightning and continue without storage
- verification failed → revert to `unverified`, schedule re-verification
- sweep detects inconsistency → escalate via `os_inbox`

## See also

- `skill-creator` — promotes skill-level memories through the
  eval / benchmark gate
- `skill-improvement-opportunity-logger` — uses `failure` and `tool`
  memories to surface proposals
- `skill-security-review` — gates any `security` memory addition
- `context-engineering` — L3 layer pulls semantic + episodic memories
