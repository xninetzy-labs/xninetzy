# Xninetzy MCP Lightning OS

```yaml
---
name: xninetzy-mcp-lightning
description: General-purpose orchestration and optimization layer for Xninetzy MCP environments, contextual tool selection, provider routing, skill selection, model choice, research strategy, and outcome evaluation across LangGraph, MCP clients, WhatsApp, Codex, Claude Code, OpenCode, and compatible agent runtimes. Uses bounded contextual decision-making, evidence-aware routing, risk-aware execution, provider provenance, idempotency, reward measurement, and explicit approval gates. Guidance only: never treat this skill as authorization, evidence, or permission to perform consequential actions.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "inspect -> classify -> contextualize -> plan -> select -> act -> verify -> measure -> learn -> propose"
---
```

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

---

# 1. Operating Philosophy

## 1.1 Tool choice is a contextual decision

The "best" tool is not universally best.

Selection depends on:

* task type,
* domain,
* modality,
* evidence requirement,
* latency budget,
* cost budget,
* provider availability,
* reliability,
* risk,
* existing state,
* reversibility.

Do not optimize one metric in isolation.

A faster provider may be worse if its evidence quality is insufficient.

---

## 1.2 Tool success is not task success

A tool returning successfully does not prove that the user's task succeeded.

Distinguish:

```text
tool_returned
tool_result_valid
evidence_obtained
task_completed
```

Example:

```text
Tool:
download succeeded

Evidence:
file exists and opens

Task:
assignment material successfully retrieved

Status:
task success
```

Do not mark the final task successful merely because the tool call returned HTTP 200 or a non-error response.

---

# 2. Capability Boundary

The MCP Lightning layer should coordinate capabilities, not duplicate them.

Examples:

```text
Course retrieval
→ hebat-academic

Assignment orchestration
→ xninetzy-assignment-orchestrator

Deep research
→ xninetzy-deep-research

Learning
→ xninetzy-learning-coach / it-learning

Graph reasoning
→ graph-rag

Goal definition
→ define-goal

Artifact production
→ xninetzy-artifact-orchestrator

Cyber Campus operations
→ cyber-campus

Personal life management
→ life-management

Cross-session persistence
→ memory-chat
```

MCP Lightning should select and route to the owner of the domain rather than implementing its own duplicate workflow.

---

# 3. Mandatory Inspection

Before choosing a tool, inspect:

### Task

What is the user actually trying to achieve?

### Risk

Is the task:

* read-only,
* reversible write,
* consequential write,
* destructive,
* external communication,
* submission,
* financial,
* academic registration?

### Scope

Whose data or state is affected?

### Providers

Which registered providers are available?

### Skills

Which domain skill owns the operation?

### State

What has already happened?

### Evidence

What must be true to call the task successful?

---

# 4. Risk Classification

Use a simple risk model:

```text
R0 — informational
R1 — local/reversible
R2 — externally visible
R3 — consequential
R4 — destructive/high-impact
```

Examples:

### R0

Search documentation.

### R1

Create a local draft file.

### R2

Send a non-sensitive external message.

### R3

Submit an assignment or change KRS.

### R4

Delete records or execute an irreversible destructive action.

Higher-risk operations require stronger verification and approval boundaries.

---

# 5. Action Classes

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

---

# 6. Owner Scope

Every external operation should be bound to an explicit owner scope where supported.

Conceptually:

```text
owner
+
domain
+
target
+
action
```

Do not silently cross:

* user accounts,
* projects,
* courses,
* organizations,
* personal vs public data,
* production vs development environments.

---

# 7. Canonical Tool Registry

Use only registered canonical tools.

Do not:

* invent tool names,
* construct undocumented endpoints,
* write client-specific domain logic,
* bypass the registered adapter,
* call arbitrary browser automation when a typed domain tool exists.

If the appropriate registered capability is unavailable:

**surface the limitation instead of improvising.**

---

# 8. Context Vector

Record only bounded context required for decision-making.

Recommended dimensions:

```text
interface
domain
intent
modality
risk_class
task_type
evidence_requirement
provider_availability
latency_bucket
budget_bucket
```

Optional low-cardinality fields may include:

```text
freshness_requirement
state_dependency
reversibility
artifact_type
```

Avoid unnecessary high-cardinality telemetry.

---

# 9. Privacy in Telemetry

Never log:

* credentials,
* cookies,
* authentication tokens,
* raw private prompts,
* private conversation contents,
* CAPTCHA answers,
* grade tokens,
* access keys,
* secrets,
* unnecessary high-cardinality personal identifiers.

Telemetry should explain **why a route was selected**, not reproduce private user data.

---

# 10. Strategy Selection

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

A strategy may contain:

```yaml
strategy:
owner_skill:
tool:
provider:
model:
research_profile:
fallback:
verification:
```

Only include fields that actually exist in the registered environment.

---

# 11. Selection Objective

The strategy should maximize useful task outcome subject to constraints.

Conceptually:

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

---

# 12. Contextual Bandit Model

When learning from previous outcomes, treat tool/provider selection as a contextual decision problem.

Conceptually:

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

The system may use:

* historical success,
* evidence quality,
* latency,
* cost,
* failure rate,
* task/domain compatibility.

Do not optimize solely for reward magnitude.

---

# 13. Exploration vs Exploitation

Exploration may be appropriate for **safe read-only actions**.

Examples:

* trying two search providers,
* comparing retrieval strategies,
* evaluating two model routes on a low-risk task.

Do not automatically explore:

* uploads,
* submissions,
* destructive actions,
* financial transactions,
* academic registration,
* external communication,
* privileged actions.

For consequential operations:

**deterministic and approved routing beats experimentation.**

---

# 14. Reward Model

A useful outcome model separates dimensions.

### Task success

Was the actual user task completed?

### Evidence quality

Was the supporting evidence inspected and sufficient?

### Relevance

Did the result answer the intended question?

### Reliability

Did execution behave consistently?

### Efficiency

What were cost and latency?

### Safety

Did the route remain inside its authorization and risk boundary?

Do not collapse all of these into one opaque score.

---

# 15. Reward Coverage

A reward record should identify which dimensions were actually observed.

Example:

```text
task_success: observed
evidence_quality: observed
relevance: observed
latency: observed
cost: unknown
```

Unknown values remain unknown.

Never normalize missing components to perfect scores.

---

# 16. Evidence Quality

Evidence quality should require:

* relevant evidence was actually inspected,
* source/record identity is valid,
* evidence supports the claim,
* citations/provenance are available where required,
* access level is known.

A provider that retrieves many documents but produces weak evidence should not receive a strong evidence-quality reward.

---

# 17. Research Routing

For research tasks, use an evidence ladder.

Default progression:

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

The exact route depends on topic, freshness, and provider availability.

Do not invoke expensive providers merely because they exist.

---

# 18. Deep Research Provider Strategy

For large research tasks:

1. start with inexpensive orientation where appropriate,
2. map terminology,
3. identify candidate sources,
4. deduplicate,
5. rank,
6. inspect strongest evidence,
7. add providers only where a gap remains,
8. audit the final evidence set.

Potential providers may include:

* DDGS,
* arXiv,
* Crossref,
* Tavily,
* Serper,
* YouTube,
* local knowledge stores.

Provider availability must be checked at runtime.

---

# 19. Provider Provenance

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

Do not erase raw rank before analysis.

Raw rank is useful for evaluating provider performance.

---

# 20. Deduplication

Before synthesis:

1. canonicalize URLs,
2. identify DOI/arXiv IDs where available,
3. normalize titles/authors,
4. detect syndicated copies,
5. merge duplicate records,
6. preserve original provider provenance.

Do not count the same article from five providers as five independent sources.

---

# 21. Ranking

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

Avoid treating provider rank as truth.

A source appearing first in search results is not automatically stronger evidence.

---

# 22. Evidence-Only Synthesis

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

---

# 23. Failure Handling

Tool failures should follow the structured error contract:

```text
❌ [CODE] message
```

Interpret errors explicitly.

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

---

# 24. Idempotency

For mutating or retryable actions, use a stable `idempotency_key` when supported.

Examples:

```text
artifact generation
research ingestion
task creation
upload
submission
external mutation
```

The key should remain stable across safe retries of the same intended action.

Never generate a new idempotency key for a retry of the exact same operation unless the underlying system explicitly requires it.

---

# 25. Action Verification

After execution:

```text id="hjo74x"
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

---

# 26. State Verification

Where possible, verify the resulting state from the authoritative system.

Examples:

### HEBAT

Read submission status.

### Cyber Campus

Read current KRS after staging/submission.

### Files

Check file existence and renderability.

### Research

Inspect the source.

### Spreadsheet

Recalculate/inspect formulas and values.

### Artifact

Render and visually inspect.

The verification source should match the domain's authority.

---

# 27. Fallback Strategy

A fallback should be selected before execution when practical.

Example:

```yaml id="5t9fds"
primary:
  provider: arxiv
fallback:
  provider: crossref
verification:
  inspect_source: true
```

Fallbacks should preserve the required evidence level.

Do not fall back from a primary source to an untrusted secondary source merely to avoid failure.

---

# 28. Latency and Budget Buckets

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

---

# 29. Model Selection

When multiple models are available, select by task characteristics.

### Reasoning-heavy

Prioritize reasoning reliability.

### Long-context

Prioritize context capacity and stable synthesis.

### Structured extraction

Prioritize schema adherence.

### Creative generation

Prioritize generation quality.

### Fast classification

Prioritize latency and cost.

Do not choose a model solely because it has the highest general benchmark score.

---

# 30. Skill Selection

When several skills appear applicable:

1. identify the skill that owns the domain,
2. use supporting skills only where they add value,
3. avoid duplicate workflows,
4. preserve one canonical owner for each operation.

Example:

A HEBAT assignment should not independently implement:

* Moodle retrieval,
* deep research,
* artifact generation,
* memory persistence.

Instead, the Assignment Orchestrator coordinates the relevant specialized skills.

---

# 31. Lightning Decision Record

For material route decisions, record a compact decision:

```yaml id="r29f5l"
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

---

# 32. Outcome Record

After execution:

```yaml id="2vjiyf"
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

---

# 33. Learning From Outcomes

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

---

# 34. Contextual Learning Safety

The optimization system must not learn unsafe behavior merely because it increases reward.

Examples:

* skipping verification to become faster,
* avoiding citations to reduce latency,
* choosing destructive actions because they complete tasks faster,
* bypassing approval to increase completion rate.

Safety constraints are **hard constraints**, not reward penalties that can be traded away.

---

# 35. Safety-Constrained Optimization

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

---

# 36. Approval Boundaries

Never auto-select or auto-execute:

* final submission,
* upload,
* destructive write,
* financial transaction,
* academic registration,
* external communication,
* cross-contact action,
* privileged mutation.

These require the relevant domain workflow and approval boundary.

MCP Lightning may **route to** the correct workflow, but does not create authorization.

---

# 37. Read-Only Exploration

Safe exploration can include:

* alternate search providers,
* retrieval methods,
* model comparison,
* source ranking,
* evidence extraction strategies.

For read-only exploration, the system may compare strategies without changing external state.

Record the route and result so future decisions can learn from the experiment.

---

# 38. Cross-Client Consistency

The workflow should remain conceptually identical across:

* LangGraph,
* MCP,
* WhatsApp,
* Codex,
* Claude Code,
* OpenCode,
* other registered interfaces.

Client-specific code should remain inside adapters.

The decision model should operate at the capability layer:

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

---

# 39. Provider Health

Track provider state when the system supports it:

```text id="u6hmkw"
healthy
degraded
rate_limited
unavailable
unknown
```

Provider health should influence routing but should not override evidence requirements.

---

# 40. Research Provider Decision Matrix

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

---

# 41. Research Evidence Gate

Before final evidence synthesis:

```text id="khyz3v"
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

---

# 42. Unknown-State Policy

Unknown remains unknown.

Examples:

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

---

# 43. Confidence Policy

Confidence should reflect evidence, not optimism.

Use:

```text
high
moderate
low
unknown
```

A missing observation should produce **unknown**, not low.

---

# 44. Auditability

Material decisions should be explainable.

A future reviewer should be able to answer:

**Why was this tool selected?**

**What alternatives were available?**

**What evidence justified the choice?**

**What happened after execution?**

**Was the result actually verified?**

This does not require storing private prompts or full transcripts.

---

# 45. Proposed vs Completed Actions

Clearly separate:

### Proposed

> Use provider X for the next research round.

### Selected

> Provider X was selected.

### Executed

> Search was performed.

### Verified

> Returned sources were inspected and relevant.

### Persisted

> Outcome was recorded in the optimization state.

Do not collapse these states.

---

# 46. Completion Contract

Every MCP Lightning decision should return the relevant subset of:

**Selected strategy**
Tool, skill, provider, model, or profile selected.

**Reason**
The key decision factors.

**Result**
What actually happened.

**Evidence status**
Whether evidence was inspected and sufficient.

**Reward coverage**
Which outcome dimensions were observed.

**Verification status**
Whether task state was independently verified.

**Uncertainty**
What remains unknown.

**Approval requirement**
Whether owner approval is needed.

**Learning signal**
What should inform future routing.

---

# 47. Standard Decision Output

```text id="j5rbiz"
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

---

# 48. Operating Rules

The system must:

**inspect context before selecting tools,**

**use canonical registered capabilities,**

**route domain work to the correct skill,**

**separate tool success from task success,**

**require evidence appropriate to the task,**

**preserve provider provenance,**

**deduplicate research sources,**

**keep unknown values neutral,**

**use stable idempotency keys for safe retries,**

**verify external state after consequential actions,**

**treat safety constraints as hard constraints,**

**never explore destructive or consequential actions automatically,**

**learn from verified outcomes rather than tool-return optimism,**

**avoid high-cardinality private telemetry,**

**remain consistent across MCP clients and interfaces.**

The canonical lifecycle is:

**Inspect → Classify → Contextualize → Plan → Select → Act → Verify → Measure → Learn → Propose**

The central principle is:

> **Lightning is not "use the fastest tool." It is "choose the safest, most evidence-capable, context-appropriate route, verify what actually happened, and learn only from what can be trusted."**
