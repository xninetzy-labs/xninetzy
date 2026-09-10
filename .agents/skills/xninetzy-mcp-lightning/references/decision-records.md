# Xninetzy MCP Lightning — Decision Records and Operating Policies

This reference expands lightning decision records, outcome records, learning from outcomes, contextual learning safety, safety-constrained optimization, approval boundaries, read-only exploration, cross-client consistency, provider health, and auditability. Read it when designing decision logging or proposing routing improvements.

## Lightning decision record

For material route decisions, record a compact decision:

```yaml
task:
risk:
context:
candidates:
selected:
reason:
fallback:
verification:
```

Do not store private prompts or secrets.

## Outcome record

After execution:

```yaml
task:
strategy:
tool:
provider:
result:
task_success:
evidence_quality:
relevance:
latency_bucket:
budget_bucket:
uncertainty:
verification:
```

Unknown fields should remain unknown.

## Learning from outcomes

Use outcome history to improve future selection.

A route becomes more attractive when it repeatedly demonstrates:

* high task success,
* high evidence quality,
* low failure rate,
* acceptable cost,
* acceptable latency.

A route should become less attractive when it repeatedly produces:

* unsupported claims,
* irrelevant results,
* failed execution,
* unstable state,
* poor evidence.

Do not overfit on a tiny number of observations.

## Contextual learning safety

The optimization system must not learn unsafe behavior merely because it increases reward. Examples of unacceptable optimization pressure:

* skipping verification to become faster,
* avoiding citations to reduce latency,
* choosing destructive actions because they complete tasks faster,
* bypassing approval to increase completion rate.

Safety constraints are **hard constraints**, not reward penalties that can be traded away.

## Safety-constrained optimization

Conceptually:

```text
maximize utility
subject to:
  authorization = valid
  risk <= allowed
  evidence >= required threshold
  verification = available
  approval = satisfied where required
```

A high-reward route that violates a safety constraint is ineligible.

## Approval boundaries

Never auto-select or auto-execute:

* final submission,
* upload,
* destructive write,
* financial transaction,
* academic registration,
* external communication,
* cross-contact action,
* privileged mutation.

These require the relevant domain workflow and approval boundary. MCP Lightning may **route to** the correct workflow, but does not create authorization.

## Read-only exploration

Safe exploration can include:

* alternate search providers,
* retrieval methods,
* model comparison,
* source ranking,
* evidence extraction strategies.

For read-only exploration, the system may compare strategies without changing external state. Record the route and result so future decisions can learn from the experiment.

## Cross-client consistency

The workflow should remain conceptually identical across MCP clients and registered interfaces. Client-specific code should remain inside adapters. The decision model should operate at the capability layer:

```text
intent
→ canonical capability
→ registered tool
→ provider
→ verification
```

not:

```text
intent
→ special browser logic for client X
```

## Provider health

Track provider state when the system supports it:

```text
healthy
degraded
rate_limited
unavailable
unknown
```

Provider health should influence routing but should not override evidence requirements.

## Research provider decision matrix

| Requirement              | Preferred Route                 |
| ------------------------ | ------------------------------- |
| Fast orientation         | Lightweight web/search provider |
| Academic discovery       | arXiv / Crossref                |
| Primary paper metadata   | Crossref / arXiv                |
| Current web facts        | Current web provider            |
| Specialist web retrieval | Configured specialist provider  |
| Lecture/demo context     | YouTube                         |
| Deep synthesis           | Multi-source evidence workflow  |

Use only providers actually configured and available.

## Research evidence gate

Before final evidence synthesis:

```text
candidate sources
↓
deduplicate
↓
rank
↓
inspect
↓
validate
↓
evidence set
↓
synthesis
```

Never synthesize from search snippets alone when stronger source inspection is possible.

## Unknown-state policy

Unknown remains unknown. Examples:

```text
cost: unknown
provider quality: unknown
submission state: unknown
evidence: insufficient
```

Do not convert unknown into:

* zero,
* success,
* high confidence,
* low risk.

This is especially important in reward calculations.

## Confidence policy

Confidence should reflect evidence, not optimism. Use:

```text
high
moderate
low
unknown
```

A missing observation should produce **unknown**, not low.

## Auditability

Material decisions should be explainable. A future reviewer should be able to answer:

* Why was this tool selected?
* What alternatives were available?
* What evidence justified the choice?
* What happened after execution?
* Was the result actually verified?

This does not require storing private prompts or full transcripts.

## Proposed vs completed actions

Clearly separate:

### ** proposed
> Use provider X for the next research round.

### ** selected
> Provider X was selected.

### ** executed
> Search was performed.

### ** verified
> Returned sources were inspected and relevant.

### ** persisted
> Outcome was recorded in the optimization state.

Do not collapse these states.

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