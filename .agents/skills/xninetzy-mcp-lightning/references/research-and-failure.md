# Xninetzy MCP Lightning — Research Routing, Failure, and Verification

This reference expands research routing, deep research provider strategy, provider provenance, deduplication, ranking, evidence-only synthesis, failure handling, idempotency, action verification, state verification, fallback strategy, latency/budget buckets, model selection, skill selection, and the standard decision output. Read it when designing or auditing a routing decision.

## Research routing

For research tasks, use an evidence ladder. Default progression:

```text
local knowledge
↓
DDGS / broad web discovery
↓
arXiv
↓
Crossref
↓
configured specialist providers
↓
YouTube / supplementary sources
```

The exact route depends on topic, freshness, and provider availability. Do not invoke expensive providers merely because they exist.

## Deep research provider strategy

For large research tasks:

1. start with inexpensive orientation where appropriate,
2. map terminology,
3. identify candidate sources,
4. deduplicate,
5. rank,
6. inspect strongest evidence,
7. add providers only where a gap remains,
8. audit the final evidence set.

Potential providers may include DDGS, arXiv, Crossref, Tavily, Serper, YouTube, and local knowledge stores. Provider availability must be checked at runtime.

## Provider provenance

For every material research result, preserve:

```text
provider
raw_rank
canonical_url
source_id
evidence_level
relevance_score
retrieval_time
```

Do not erase raw rank before analysis. Raw rank is useful for evaluating provider performance.

## Deduplication

Before synthesis:

1. canonicalize URLs,
2. identify DOI/arXiv IDs where available,
3. normalize titles/authors,
4. detect syndicated copies,
5. merge duplicate records,
6. preserve original provider provenance.

Do not count the same article from five providers as five independent sources.

## Ranking

Rank candidate sources using multiple signals:

```text
source quality
+
direct relevance
+
recency
+
primary-source status
+
evidence accessibility
+
provider confidence
```

Avoid treating provider rank as truth. A source appearing first in search results is not automatically stronger evidence.

## Evidence-only synthesis

Before evidence-only synthesis:

* remove unsupported claims,
* remove duplicate sources,
* verify important source metadata,
* preserve contradictory findings,
* label inference,
* distinguish source types.

If evidence is insufficient:

> **Evidence status: insufficient**

Do not fill missing evidence with confidence or plausible text.

## Failure handling

Tool failures should follow the structured error contract:

```text
❌ [CODE] message
```

Interpret errors explicitly:

### NOT_FOUND

Refine identifier/query.

### INVALID_INPUT

Correct parameters.

### NOT_CONFIGURED

Run supported setup/sync.

### POLICY_HELD

Stop and request approval.

### AUTH_REQUIRED

Refresh or re-authenticate through the supported route.

### RATE_LIMITED

Respect the provider limit and select a valid alternative when permitted.

### TIMEOUT

Retry only when the action is safe and idempotent.

Never use blind retry loops.

## Idempotency

For mutating or retryable actions, use a stable `idempotency_key` when supported:

* artifact generation,
* research ingestion,
* task creation,
* upload,
* submission,
* external mutation.

The key should remain stable across safe retries of the same intended action. Never generate a new idempotency key for a retry of the exact same operation unless the underlying system explicitly requires it.

## Action verification

After execution:

```text
tool result
 ↓
read actual state
 ↓
compare expected vs actual
 ↓
classify outcome
```

Possible outcomes:

```text
success
partial_success
failed
unchanged
uncertain
```

Do not infer success from the tool response alone.

## State verification

Where possible, verify the resulting state from the authoritative system.

* **HEBAT** — read submission status.
* **Cyber Campus** — read current KRS after staging/submission.
* **Files** — check file existence and renderability.
* **Research** — inspect the source.
* **Spreadsheet** — recalculate/inspect formulas and values.
* **Artifact** — render and visually inspect.

The verification source should match the domain's authority.

## Fallback strategy

A fallback should be selected before execution when practical:

```yaml
primary:
  provider: arxiv
fallback:
  provider: crossref
verification:
  inspect_source: true
```

Fallbacks should preserve the required evidence level. Do not fall back from a primary source to an untrusted secondary source merely to avoid failure.

## Latency and budget buckets

Use coarse buckets instead of precise telemetry where possible:

```text
latency:
  fast
  medium
  slow

budget:
  low
  medium
  high
```

This is sufficient for most routing decisions and reduces unnecessary telemetry granularity.

## Model selection

When multiple models are available, select by task characteristics:

* **Reasoning-heavy** — prioritize reasoning reliability.
* **Long-context** — prioritize context capacity and stable synthesis.
* **Structured extraction** — prioritize schema adherence.
* **Creative generation** — prioritize generation quality.
* **Fast classification** — prioritize latency and cost.

Do not choose a model solely because it has the highest general benchmark score.

## Skill selection

When several skills appear applicable:

1. identify the skill that owns the domain,
2. use supporting skills only where they add value,
3. avoid duplicate workflows,
4. preserve one canonical owner for each operation.

Example: a HEBAT assignment should not independently implement Moodle retrieval, deep research, artifact generation, or memory persistence. Instead, the Assignment Orchestrator coordinates the relevant specialized skills.

## Standard decision output

```text
Task
Risk
Selected Skill
Selected Tool
Provider / Model
Strategy
Fallback
Verification
Result
Evidence
Reward Coverage
Uncertainty
Approval
Learning Signal
```

Use only the fields relevant to the current decision.

## Operating rules

The system must:

* inspect context before selecting tools,
* use canonical registered capabilities,
* route domain work to the correct skill,
* separate tool success from task success,
* require evidence appropriate to the task,
* preserve provider provenance,
* deduplicate research sources,
* keep unknown values neutral,
* use stable idempotency keys for safe retries,
* verify external state after consequential actions,
* treat safety constraints as hard constraints,
* never explore destructive or consequential actions automatically,
* learn from verified outcomes rather than tool-return optimism,
* avoid high-cardinality private telemetry,
* remain consistent across MCP clients and interfaces.

The canonical lifecycle is:

**Inspect → Classify → Contextualize → Plan → Select → Act → Verify → Measure → Learn → Propose**