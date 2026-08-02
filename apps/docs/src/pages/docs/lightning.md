---
layout: ../../layouts/DocsLayout.astro
title: Lightning reinforcement learning
description: Episodes, rewards, contextual bandits, regressions, and approval-based self-improvement.
section: AI & developer tools
---

Lightning is Xninetzy's evaluation loop. It uses a CPU-only contextual bandit,
not online fine-tuning of model weights.

~~~text
request → episode → action → outcome → reward → strategy ranking
                                      ↓
                              proposal + approval
                                      ↓
                              regression / rollback
~~~

## Available capabilities

A request from WhatsApp, LangGraph, MCP, Codex, Claude Code, or OpenCode can be
recorded as an owner-scoped episode. Episodes store redacted route, strategy,
provider and model, tool actions, status, latency, outcome, and reward.

Reward signals include:

- task success;
- positive feedback or owner corrections;
- groundedness and citation validity;
- tool reliability;
- latency and cost boundaries.

Rewards are clamped to `[-1, 1]`. The same lifecycle event cannot be counted
twice because each record carries an idempotency key.

## Contextual bandit

A strategy includes route, provider, model, retrieval policy, skill set, and tool
ordering version. Context contains domain, intent, modality, risk class, and task
type without using the raw prompt as a key.

Deterministic UCB ranking provides limited exploration for new strategies,
raises strategies with better observed rewards, and lowers repeated failures
through statistics and circuit breakers. Providers remain deployment-
allowlisted, and write or final actions remain subject to action policy.

Inspect results with:

~~~text
/agent-reward
/agent-ranking
/agent-improve
/agent-proposals
~~~

MCP tools:

~~~text
lightning_episode_start
lightning_record_action
lightning_record_outcome
lightning_episode_finish
lightning_reward_summary
lightning_strategy_rank
lightning_regression_check
lightning_propose_improvement
~~~

## Proposals and approval

Lightning never changes code or policy automatically. A proposal includes
confidence, risk score, evidence, baseline and candidate metrics, rollout state,
and rollback metadata.

~~~text
pending → approved/rejected → active/canary → rolled_back
~~~

Low-risk rules still require owner approval under the default configuration. A
code-fix proposal may produce only diagnosis, a diff, and a test report through
the host coding bridge. Commit and push remain owner decisions.

Regression analysis requires at least 20 samples per strategy by default. A
proposal is marked as a regression when reward drops by at least `0.15`, error
rate rises by 10%, or average latency rises by 25%.

## Scheduler

Enable daily review through the OS scheduler. Its daily key is replay-safe
across restarts.

~~~env
LIGHTNING_ENABLED=true
LIGHTNING_REVIEW_ENABLED=false
LIGHTNING_REVIEW_HOUR=2
LIGHTNING_REVIEW_INTERVAL_HOURS=24
LIGHTNING_AUTO_APPLY=false
LIGHTNING_CODE_FIX_ENABLED=false
LIGHTNING_PROVIDER_OPTIMIZATION_ENABLED=true
LIGHTNING_EXPLORATION_RATE=0.10
LIGHTNING_MIN_SAMPLES_PER_STRATEGY=20
LIGHTNING_EVALUATION_WINDOW_DAYS=7
LIGHTNING_RETENTION_DAYS=90
LIGHTNING_MAX_EVENT_CHARS=4000
~~~

## Privacy

Prompts and outputs are truncated and sanitized. API keys, cookies, passwords,
CAPTCHA values, browser state, tokens, and attachment contents are not stored in
episodes. Retained data stays in local SQLite.

## Verification

~~~bash
cd services/ai
uv run pytest tests/os/lightning -q
~~~
