---
layout: ../../layouts/DocsLayout.astro
title: Lightning Reinforcement Learning
description: Episode, reward, contextual bandit, regression, dan approval untuk self-improvement Xninetzy.
section: Operasional
---

Lightning adalah loop evaluasi Xninetzy. Implementasinya menggunakan
contextual bandit CPU-only, bukan online fine-tuning bobot model.

~~~text
request → episode → action → outcome → reward → strategy ranking
                                      ↓
                              proposal + approval
                                      ↓
                              regression / rollback
~~~

## Kemampuan yang tersedia

Setiap request dari WhatsApp, LangGraph, MCP, Codex, Claude Code, atau OpenCode
dapat dicatat sebagai episode owner-scoped. Episode menyimpan route, strategy,
provider/model, tool action, status, latency, outcome, dan reward ter-redact.

Sinyal reward:

- keberhasilan task;
- feedback positif atau koreksi user;
- groundedness dan validitas citation;
- reliability tool;
- latency dan batas biaya.

Reward selalu dibatasi ke [-1, 1]. Event yang sama tidak boleh dihitung dua
kali karena setiap lifecycle menerima idempotency key.

## Contextual bandit

Strategy dibentuk dari route, provider, model, retrieval policy, skill set, dan
versi urutan tool. Context dibuat dari domain, intent, modality, risk class, dan
task type tanpa menyimpan prompt mentah sebagai key.

Ranking memakai UCB deterministik:

- strategy baru mendapat eksplorasi terbatas;
- strategy dengan reward lebih baik naik ranking;
- strategy error berulang turun melalui statistik dan circuit breaker;
- provider hanya dipilih dari allowlist deployment;
- aksi write dan final tetap tunduk pada action policy.

Lihat ringkasan:

~~~text
/agent-reward
/agent-ranking
/agent-improve
/agent-proposals
~~~

Melalui MCP, gunakan:

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

## Proposal dan approval

Lightning tidak mengubah kode atau policy secara otomatis. Proposal memiliki
confidence, risk score, evidence, baseline/candidate metrics, rollout state,
dan rollback metadata.

Lifecycle:

~~~text
pending → approved/rejected → active/canary → rolled_back
~~~

Rule low-risk tetap membutuhkan approval owner pada konfigurasi default.
Proposal code-fix hanya boleh menghasilkan diagnosis, diff, dan test report melalui
host coding bridge. Commit dan push tetap keputusan owner.

Regression default membutuhkan minimal 20 sample per strategy. Proposal ditandai
regression jika reward turun minimal 0.15, error rate naik 10%, atau latency
rata-rata naik 25%.

## Scheduler

Review harian dapat diaktifkan melalui OS scheduler. Job memiliki key harian dan
aman saat restart.

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

## Privasi

Prompt dan output dipotong serta disanitasi. API key, cookie, password, CAPTCHA,
browser state, token, dan isi attachment tidak disimpan dalam episode. Data
tersimpan lokal di SQLite sesuai retention.

## Verifikasi

~~~bash
cd services/ai
uv run pytest tests/os/lightning -q
~~~
