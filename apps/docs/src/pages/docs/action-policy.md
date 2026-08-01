---
layout: ../../layouts/DocsLayout.astro
title: Action policy dan provider CPU
description: Mode auto, approval, manual, final hard gate, serta pilihan provider lokal dan berbayar.
section: Operasional
---

Xninetzy memakai satu action policy untuk WhatsApp, LangGraph, MCP, Codex,
Claude Code, dan OpenCode. Policy ini tidak memberi izin baru; policy hanya
membuat keputusan safety konsisten di semua interface.

## Mode aksi

| Risiko | Default | Perilaku |
|---|---|---|
| read | auto | Baca data tanpa mengubah state |
| draft | auto | Buat rencana/preview tanpa side effect eksternal |
| write | approval | Owner/admin menyetujui sebelum perubahan |
| final | approval | Hard gate; tidak dapat diubah menjadi auto |

ACTION_POLICY_KILL_SWITCH=true mengubah write dan final menjadi manual.
Approval memiliki TTL dan hash isi aksi. Mengubah payload, plan, kelas, file, atau
snapshot portal membuat approval lama tidak valid. Mengulang approval yang sudah
disetujui tidak mengulang eksekusi.

~~~env
ACTION_POLICY_DEFAULT_MODE=approval
ACTION_POLICY_OVERRIDES=
ACTION_POLICY_TTL_SECONDS=300
ACTION_POLICY_MAX_WRITES_PER_RUN=30
ACTION_POLICY_KILL_SWITCH=false
~~~

Override hanya untuk aksi yang memang aman di deployment owner:

~~~env
ACTION_POLICY_OVERRIDES=obsidian_append=auto,portal_krs_war_arm=approval
~~~

KRS finalisasi, KRS War execution, HEBAT final submission, dan submit kuesioner
tetap membutuhkan approval owner walaupun ada override yang mencoba mengubahnya.

## HEBAT dan Cyber Campus

HEBAT upload tetap menggunakan confirmation token dan policy kill switch.
KRS War tetap membutuhkan admin identity, allowlist plan, arm/disarm, dan
revalidasi. Portal Cyber Campus read tools tidak menerima cookie/token dari
caller MCP; identity owner disuntikkan oleh server.

Final adapter Cyber Campus harus memvalidasi ulang session, kuota, jadwal,
action hash, dan snapshot portal sesaat sebelum submit. CAPTCHA/OTP tidak
dipecahkan oleh agent.

## CPU-only dan provider fleksibel

Xninetzy dirancang tanpa GPU:

~~~env
XNINETZY_DEVICE=cpu
EMBEDDING_DEVICE=cpu
CUDA_VISIBLE_DEVICES=
NVIDIA_VISIBLE_DEVICES=void
~~~

Default retrieval memakai SQLite + FAISS dan model Sentence Transformers yang
diunduh lalu dijalankan lokal di CPU. Model publik Hugging Face dapat dipilih
melalui EMBEDDING_MODEL; token hanya diperlukan untuk model private.

Provider berbayar bersifat optional dan deployment-scoped:

- Tavily atau Serper untuk web search;
- YouTube Data API untuk metadata YouTube;
- Flaz, OpenAI-compatible, OpenRouter, atau provider lain untuk chat;
- model embedding Hugging Face private bila benar-benar diperlukan.

Kosongkan API key optional untuk tetap memakai fallback lokal yang tersedia.
Credential tidak pernah disimpan dalam vault, prompt, payload MCP, action summary,
atau database approval.

## Evaluasi retrieval

Gunakan dataset kecil owner-scoped untuk mengukur source recall, term support,
sufficiency, dan citation identifiers:

~~~bash
cd services/ai
uv run pytest tests/os/knowledge tests/os/policy -q
~~~

knowledge_evaluate_retrieval hanya mengembalikan metrik. Jawaban final tetap
harus melewati knowledge_answer, evidence bundle, dan citation validation.
