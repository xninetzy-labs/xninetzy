---
layout: ../../layouts/DocsLayout.astro
title: Action policy and CPU providers
description: Automatic, approval, manual, and final hard gates across local and paid providers.
section: Operations
---

Xninetzy uses one action policy across WhatsApp, LangGraph, MCP, Codex,
Claude Code, and OpenCode. The policy does not grant new permissions; it keeps
safety decisions consistent across every interface.

## Action modes

| Risk | Default | Behavior |
|---|---|---|
| read | auto | Read data without changing state |
| draft | auto | Create a plan or preview without external side effects |
| write | approval | Require owner or administrator approval before a change |
| final | approval | Enforce a hard gate that cannot be changed to automatic |

`ACTION_POLICY_KILL_SWITCH=true` changes write and final actions to manual.
Approvals include a TTL and a content hash. Changing the payload, plan, class,
file, or portal snapshot invalidates the previous approval. Replaying an
approved request does not repeat execution.

~~~env
ACTION_POLICY_DEFAULT_MODE=approval
ACTION_POLICY_OVERRIDES=
ACTION_POLICY_TTL_SECONDS=300
ACTION_POLICY_MAX_WRITES_PER_RUN=30
ACTION_POLICY_KILL_SWITCH=false
~~~

Use overrides only for actions that are safe in the owner's deployment:

~~~env
ACTION_POLICY_OVERRIDES=obsidian_append=auto,portal_krs_war_arm=approval
~~~

KRS finalization, KRS War execution, final HEBAT submission, and questionnaire
submission always require owner approval, even if an override attempts to
change their mode.

## HEBAT and Cyber Campus

HEBAT uploads keep their confirmation token and policy kill switch. KRS War
requires administrator identity, a plan allowlist, arm and disarm controls, and
revalidation. Cyber Campus read tools never accept cookies or tokens from an
MCP caller; the server injects trusted owner identity.

The final Cyber Campus adapter must revalidate the session, capacity, schedule,
action hash, and portal snapshot immediately before submission. Agents never
solve CAPTCHA or OTP challenges.

## CPU-only and flexible providers

Xninetzy is designed to run without a GPU:

~~~env
XNINETZY_DEVICE=cpu
EMBEDDING_DEVICE=cpu
CUDA_VISIBLE_DEVICES=
NVIDIA_VISIBLE_DEVICES=void
~~~

Default retrieval uses SQLite, FAISS, and a Sentence Transformers model
downloaded and executed locally on the CPU. Select a public Hugging Face model
with `EMBEDDING_MODEL`; a token is only required for private models.

Paid providers are optional and scoped to the deployment:

- Tavily or Serper for web search;
- YouTube Data API for YouTube metadata;
- Flaz, OpenAI-compatible, OpenRouter, or another chat provider;
- a private Hugging Face embedding model when it is genuinely required.

Leave optional API keys empty to use available local fallbacks. Credentials are
never stored in the vault, prompts, MCP payloads, action summaries, or the
approval database.

## Retrieval evaluation

Use a small owner-scoped dataset to measure source recall, term support,
sufficiency, and citation identifiers:

~~~bash
cd services/ai
uv run pytest tests/os/knowledge tests/os/policy -q
~~~

`knowledge_evaluate_retrieval` returns metrics only. Final answers must still
pass through `knowledge_answer`, the evidence bundle, and citation validation.
