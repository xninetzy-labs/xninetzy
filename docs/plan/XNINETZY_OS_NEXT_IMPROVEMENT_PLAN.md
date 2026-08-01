# Xninetzy OS Next Improvement Plan

Last updated: 2026-08-02

This is the canonical forward plan for the single-owner Xninetzy OS. Older
roadmaps remain useful historical references, but implementation status and
acceptance criteria are tracked here.

## Operating contract

Every interface uses the same domain and tool registry:

`WhatsApp / LangGraph / MCP / Codex / Claude Code / OpenCode -> Xninetzy OS`

The OS closes:

`Capture -> Understand -> Plan -> Execute -> Review -> Adapt`

A request must be grounded in selected evidence when it asks about the vault,
course material, academic data, or learning knowledge. Raw vector chunks are
never a final answer.

## Action policy

The shared action policy classifies each tool action as `read`, `draft`,
`write`, or `final`, then selects `auto`, `approval`, or `manual`.

- Read and draft actions run automatically.
- Write actions default to approval and can be overridden per action.
- A kill switch forces manual handling.
- Final actions can never be changed to auto. KRS finalization, KRS War execution,
  HEBAT final submission, and questionnaire submission remain owner-gated.
- Existing explicit confirmations remain valid guardrails. HEBAT upload requires
  its confirmation token; KRS War requires admin arming and allowlist checks.
- Approval requests carry an expiry and an action hash. A changed plan, resource,
  or payload invalidates the old approval. Re-approving an already approved request
  is idempotent and never executes it twice.

Configuration:

```env
ACTION_POLICY_DEFAULT_MODE=approval
ACTION_POLICY_OVERRIDES=
ACTION_POLICY_TTL_SECONDS=300
ACTION_POLICY_MAX_WRITES_PER_RUN=30
ACTION_POLICY_KILL_SWITCH=false
```

Example override:

```env
ACTION_POLICY_OVERRIDES=obsidian_append=auto,portal_krs_war_arm=approval
```

## Milestone 1  -  Foundation and trust

Outcome: all impactful actions have a deterministic policy decision, replay-safe
approval record, owner authorization, and observable execution result.

Acceptance tests:

- policy tests cover read/draft auto, write override, manual kill switch, and
  final hard gate;
- approval expiry rejects stale requests;
- action hash mismatch rejects a changed action;
- duplicate approval does not repeat the handler;
- all policy decisions are available through `action_policy_evaluate` in LangGraph
  and MCP.

Status: implemented in `os/policy`, HITL approval storage, and the canonical
registry.

Remaining work:

- add a durable execution ledger for external browser actions;
- add metrics for policy denials, approval latency, and execution failures.

## Milestone 2  -  Adaptive Learning OS

Outcome: the daily plan selects the next ready concept, due recall, active session,
mastery reinforcement, available minutes, and energy in deterministic order.

Acceptance tests:

- active sessions are resumed first;
- due recall is selected before new study;
- low energy shortens the plan;
- available time caps the duration without changing the evidence contract;
- unmet prerequisites never become the next focus;
- weekly review and Personal Context expose weak concepts and due recall.

Status: implemented in the shared progress tracker. The learning tool accepts
`available_minutes` and `energy` without breaking existing callers.

Next:

- attach explicit deadline priority from HEBAT assignments and shared tasks;
- add a small owner-scoped benchmark set for focus selection and mastery outcomes.

## Milestone 3  -  Grounded retrieval quality

Outcome: retrieval quality is measurable without turning raw chunks into answers.

Acceptance tests:

- evaluation cases report recall@k, sufficiency, term support, and citation
  identifier validity;
- duplicate or invalid citation identifiers fail the case;
- `knowledge_answer` remains the only final synthesis path;
- insufficient evidence is disclosed.

Status: implemented through `os/knowledge/evaluation.py` and
`knowledge_evaluate_retrieval`.

Run:

```bash
cd services/ai
uv run pytest tests/os/knowledge tests/os/policy -q
```

## Milestone 4  -  Academic and HEBAT action workflow

Outcome: portal reads, draft plans, uploads, and final actions share one policy
and remain safe across WhatsApp, LangGraph, and MCP.

Acceptance tests:

- HEBAT login, assignment detail, and material reads are automatic when the
  session is valid;
- upload requires the existing confirmation token and policy kill switch;
- Cyber Campus reads remain read-only and session/CAPTCHA state is never exposed;
- KRS War arming requires admin identity, allowlist, explicit disarm, and a
  policy check;
- final KRS or submission actions require owner approval and revalidation of
  the current portal snapshot.

Status: policy checks are connected to HEBAT upload and KRS War arming. The
portal adapter still needs a dedicated approval-backed final-submit adapter
before any code may submit final KRS.

## Milestone 5  -  Provider-flexible, CPU-only deployment

Outcome: a clean local install works on Linux, Windows, and macOS without a GPU,
while paid providers remain optional accelerators.

Defaults:

- local Sentence Transformers/Hugging Face embeddings on CPU;
- local FAISS/SQLite retrieval;
- Flaz or another configured OpenAI-compatible chat endpoint;
- web research provider keys are optional and deployment-scoped.

Optional integrations:

- Tavily or Serper for higher quality web search;
- YouTube Data API for YouTube metadata;
- OpenAI-compatible paid models;
- Hugging Face private models only when a token is required.

Acceptance tests:

- CPU guard rejects CUDA/GPU runtime;
- blank optional keys do not prevent startup;
- provider selection changes only deployment-scoped model settings;
- credentials never enter prompts, MCP payloads, or approval summaries.

## Milestone 6  -  Adaptive web intelligence

Outcome: public web analysis, portal route catalogs, visual capture, knowledge
ingestion, and GraphRAG form one traceable research path.

Status: dynamic public discovery and HEBAT/Cyber/QA safe route catalogs are
implemented. Remaining work is supervised PixelRAG local serving and automatic
web-page node/edge projection with replay-safe leases.

## Verification gate

```bash
cd services/ai
uv run ruff check app tests
uv run pytest
cd ../../services/wa-enggine
yarn lint
yarn test
yarn build
cd ../../apps/docs
yarn check
yarn build
```

Known environment-only caveat: the host virtualenv may contain forbidden NVIDIA
packages from outside this repository. The CPU guard tests should run in the
clean container image; a host venv with CUDA packages is a failed deployment
condition, not a code-path fallback.
