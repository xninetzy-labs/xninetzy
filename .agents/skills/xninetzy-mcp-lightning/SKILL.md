---

...

...
name: "xninetzy-mcp-lightning"
description: "Decision and optimization layer for Xninetzy MCP environments, contextual tool selection, provider routing, skill selection, model choice, research strategy, and outcome evaluation across MCP clients and compatible agent runtimes. Guidance only; never treats this skill as authorization, evidence, or permission to perform consequential actions."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "inspect -> classify -> contextualize -> plan -> select -> act -> verify -> measure -> learn -> propose"
...

# Xninetzy MCP Lightning OS

This skill is the **decision and optimization layer for tool-enabled agent workflows**.

It determines:

* which registered tool to use,
* which skill should own the task,
* which provider is appropriate,
* which model or research profile is appropriate,
* whether a tool route is safe,
* what evidence is required,
* whether the result actually succeeded,
* what can be learned from the outcome.

It must remain separate from:

* authorization,
* credential handling,
* domain-specific portal logic,
* persistent business truth,
* academic requirements,
* final evidence.

The core principle is:

> **Choose the smallest safe registered capability that can produce the required evidence, verify the result, and learn from the outcome without turning uncertainty into false confidence.**

The canonical lifecycle is:

**Inspect → Classify → Contextualize → Plan → Select → Act → Verify → Measure → Learn → Propose**

## Operating philosophy

* **Tool choice is a contextual decision.** The "best" tool is not universally best. Selection depends on task type, domain, modality, evidence requirement, latency budget, cost budget, provider availability, reliability, risk, existing state, and reversibility. A faster provider may be worse if its evidence quality is insufficient.
* **Tool success is not task success.** A tool returning successfully does not prove that the user's task succeeded. Distinguish `tool_returned | tool_result_valid | evidence_obtained | task_completed`. Do not mark the final task successful merely because the tool call returned a non-error response.

## When to use

* selecting among multiple registered tools, providers, models, or skills for a task;
* deciding between exploration and deterministic routing for low-risk actions;
* auditing whether the executed route produced the required evidence;
* proposing routing improvements backed by observed outcomes.

## When NOT to use

* for consequential actions themselves — defer to the domain skill and approval boundary;
* when only a single deterministic capability exists for the task;
* when authorization, safety, or credential handling is the question — those belong to domain skills and HITL.

## Core workflow

1. **Inspect.** Inspect the task, risk, scope, available providers, owning skills, current state, and the evidence the task must produce.
2. **Classify.** Use a simple risk model: `R0 — informational | R1 — local/reversible | R2 — externally visible | R3 — consequential | R4 — destructive/high-impact`. Higher-risk operations require stronger verification and approval boundaries.
3. **Contextualize.** Record only bounded context required for decision-making: interface, domain, intent, modality, risk class, task type, evidence requirement, provider availability, latency bucket, budget bucket, and optional freshness, state dependency, reversibility, artifact type. Avoid high-cardinality telemetry.
4. **Plan.** Sequence the route, fallback, and verification steps before execution.
5. **Select.** Use only registered canonical tools. Do not invent tool names, undocumented endpoints, or client-specific domain logic. If the appropriate registered capability is unavailable, surface the limitation rather than improvising.
6. **Act.** Execute through the selected capability with a stable idempotency key when supported.
7. **Verify.** Read the actual state from the authoritative system. Compare expected vs actual. Do not infer success from the tool response alone.
8. **Measure.** Record outcome dimensions actually observed: task success, evidence quality, relevance, reliability, latency, cost, safety. Leave unknown values as unknown.
9. **Learn.** Use observed outcomes to refine future routing without overfitting to a small sample. Treat safety constraints as hard constraints, not as reward penalties.
10. **Propose.** Surface improvement proposals backed by evidence, not optimism.

## Capability boundary

The MCP Lightning layer coordinates capabilities, not duplicate them.

Examples:

```text
Course retrieval             → hebat-academic
Assignment orchestration     → xninetzy-assignment-orchestrator
Deep research                → xninetzy-deep-research
Learning                     → xninetzy-learning-coach / it-learning
Graph reasoning              → graph-rag
Goal definition              → define-goal
Artifact production          → xninetzy-artifact-orchestrator
Cyber Campus operations      → xninetzy-cyber-campus
Personal life management     → life-management
Cross-session persistence    → xninetzy-memory
```

Select and route to the owner of the domain rather than implementing a duplicate workflow.

## Mandatory inspection

Before choosing a tool, inspect:

* **Task** — what is the user actually trying to achieve?
* **Risk** — is the task informational, local/reversible, externally visible, consequential, destructive, external communication, submission, financial, or academic registration?
* **Scope** — whose data or state is affected?
* **Providers** — which registered providers are available?
* **Skills** — which domain skill owns the operation?
* **State** — what has already happened?
* **Evidence** — what must be true to call the task successful?

## Action classes

Classify actions separately from risk:

```text
read
search
analyze
generate
transform
write
upload
submit
delete
communicate
purchase
modify_external_state
```

Never infer that permission for one action class implies permission for another.

## Owner scope

Every external operation should be bound to an explicit owner scope where supported:

```text
owner
+
domain
+
target
+
action
```

Do not silently cross user accounts, projects, courses, organizations, personal vs public data, or production vs development environments.

## Canonical tool registry

Use only registered canonical tools. Do not invent tool names, construct undocumented endpoints, write client-specific domain logic, bypass the registered adapter, or call arbitrary browser automation when a typed domain tool exists. If the appropriate registered capability is unavailable, surface the limitation instead of improvising.

## Privacy in telemetry

Never log credentials, cookies, authentication tokens, raw private prompts, private conversation contents, CAPTCHA answers, grade tokens, access keys, secrets, or unnecessary high-cardinality personal identifiers. Telemetry should explain **why a route was selected**, not reproduce private user data.

## Strategy selection

For each task, select a route:

```text
task
 ↓
eligible skills
 ↓
eligible tools/providers
 ↓
risk filter
 ↓
evidence filter
 ↓
budget/latency filter
 ↓
best strategy
```

A strategy may contain `owner_skill`, `tool`, `provider`, `model`, `research_profile`, `fallback`, and `verification`. Only include fields that actually exist in the registered environment.

## Selection objective

The strategy should maximize useful task outcome subject to constraints:

```text
utility =
success_probability
× evidence_quality
× relevance
× reliability
-
cost
-
latency
-
risk
```

This is a decision heuristic, not a claim of numerical precision.

## Contextual bandit model

When learning from previous outcomes, treat tool/provider selection as a contextual decision problem:

```text
context
+
candidate action
 ↓
predicted utility
 ↓
select
 ↓
observe outcome
 ↓
update policy
```

Use historical success, evidence quality, latency, cost, failure rate, and task/domain compatibility. Do not optimize solely for reward magnitude.

## Exploration vs exploitation

Exploration may be appropriate for **safe read-only actions** (trying two search providers, comparing retrieval strategies, evaluating two model routes on a low-risk task). Do not automatically explore uploads, submissions, destructive actions, financial transactions, academic registration, external communication, or privileged actions. For consequential operations: **deterministic and approved routing beats experimentation.**

## Reward model

A useful outcome model separates dimensions:

* **Task success** — was the actual user task completed?
* **Evidence quality** — was the supporting evidence inspected and sufficient?
* **Relevance** — did the result answer the intended question?
* **Reliability** — did execution behave consistently?
* **Efficiency** — what were cost and latency?
* **Safety** — did the route remain inside its authorization and risk boundary?

Do not collapse all of these into one opaque score.

## Reward coverage

A reward record should identify which dimensions were actually observed:

```text
task_success: observed
evidence_quality: observed
relevance: observed
latency: observed
cost: unknown
```

Unknown values remain unknown. Never normalize missing components to perfect scores.

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

## Evidence quality

Evidence quality should require:

* relevant evidence was actually inspected,
* source/record identity is valid,
* evidence supports the claim,
* citations/provenance are available where required,
* access level is known.

A provider that retrieves many documents but produces weak evidence should not receive a strong evidence-quality reward.

## Idempotency

For mutating or retryable actions, use a stable `idempotency_key` when supported: artifact generation, research ingestion, task creation, upload, submission, external mutation. Never generate a new idempotency key for a retry of the exact same operation unless the underlying system explicitly requires it.

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

Possible outcomes: `success | partial_success | failed | unchanged | uncertain`. Do not infer success from the tool response alone.

## State verification

Where possible, verify the resulting state from the authoritative system. Examples:

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

When multiple models are available, select by task characteristics.

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

A HEBAT assignment should not independently implement Moodle retrieval, deep research, artifact generation, or memory persistence. Instead, the Assignment Orchestrator coordinates the relevant specialized skills.

## Approval boundaries

Never auto-select or auto-execute final submission, upload, destructive write, financial transaction, academic registration, external communication, cross-contact action, or privileged mutation. These require the relevant domain workflow and approval boundary. MCP Lightning may **route to** the correct workflow, but does not create authorization.

## Cross-client consistency

The workflow should remain conceptually identical across MCP clients and registered interfaces. Client-specific code should remain inside adapters. The decision model should operate at the capability layer (`intent → canonical capability → registered tool → provider → verification`), not at the client-bypass layer (`intent → special browser logic for client X`).

## Provider health

Track provider state when the system supports it: `healthy | degraded | rate_limited | unavailable | unknown`. Provider health should influence routing but should not override evidence requirements.

## Confidence policy

Confidence should reflect evidence, not optimism. Use: `high | moderate | low | unknown`. A missing observation should produce unknown, not low.

## Auditability

Material decisions should be explainable. A future reviewer should be able to answer:

* Why was this tool selected?
* What alternatives were available?
* What evidence justified the choice?
* What happened after execution?
* Was the result actually verified?

This does not require storing private prompts or full transcripts.

## Routing

* Domain selection → the appropriate specialized skill.
* Research → `xninetzy-deep-research`.
* Memory → `xninetzy-memory`.
* Risk and approval → `xninetzy-academic-safety`.

## Reference map

* `references/decision-records.md` — lightning decision record, outcome record, learning from outcomes, contextual learning safety, safety-constrained optimization, approval boundaries, read-only exploration, cross-client consistency, provider health, research provider decision matrix, research evidence gate, unknown-state policy, confidence policy, auditability, and proposed-vs-completed actions.
* `references/research-and-failure.md` — research routing, deep research provider strategy, provider provenance, deduplication, ranking, evidence-only synthesis, failure handling, idempotency, action verification, state verification, fallback strategy, latency and budget buckets, model selection, skill selection, and standard decision output.

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

The central principle is:

> **Lightning is not "use the fastest tool." It is "choose the safest, most evidence-capable, context-appropriate route, verify what actually happened, and learn only from what can be trusted."**