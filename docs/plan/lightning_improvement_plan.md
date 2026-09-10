# Lightning — Audit, Gaps, and Improvement Plan

Status: **draft for review** (analisis berbasis data DB, belum diimplementasi)
Data snapshot: 2026-08-03 07:50 WIB, tabel `agent_episodes` (415) & `agent_episode_actions` (408)

## Goal

Buat Lightning benar-benar belajar dari pengalaman: reward mencerminkan kualitas
nyata, failure rate yang dapat dipercaya, episode tidak menggantung, dan
strategi ranking tidak cold-start bias.

## Current state (verified dari DB)

### Episode

| Stat | Nilai |
|---|---|
| Total episode | 415 |
| `completed` | 402 |
| `failed` | 2 |
| `active` (menggantung) | **11** (tertua sejak 2026-08-02T02:41 WIB) |
| Reward > 0 | 402/402 = 100% |
| Reward = 0 | 0 |
| Reward < 0 | 0 |
| Avg reward (completed) | 0.99876 |

### Reward breakdown (sample)

```json
{"components": {"task_success": 1.0}, "total": 1.0}
```

Hanya komponen `task_success` — reward = "tidak exception", bukan kualitas.

### Actions

| Stat | Nilai |
|---|---|
| Total actions | 408 |
| `ok` | 404 |
| `error` | 4 (semua `langgraph` → `BadRequestError`) |
| `mcp_tool` | 314 |
| `route` | 91 |
| `tool` | 3 |

### Context keys teratas

`chat:request`, `mcp:skill_get`, `mcp:skill_resource_list`, `mcp:graph_v3_link`,
`mcp:graph_v3_upsert_node`, `mcp:memory_add`, `mcp:obsidian_read`,
`mcp:datetime_now`, `mcp:portal_krs_war_status`, `mcp:graph_v3_stats`.
Semua context key berakhiran `:text:read:` — indikasi risk class belum
dibedakan (write ops tampil sebagai read).

## Gap analysis (6 gaps)

### G1 — Groundedness = 0.0 (rewards tidak memakai groundedness)

Reward hanya `task_success`. Tidak ada komponen groundedness padahal
episode di-boot dari `graph_get_context`. Learning loop tidak bisa
membedakan jawaban ter-ground vs halusinasi.

**Fix proposal:**
- Tambah komponen `groundedness` di `reward_breakdown_json` bila episode
  memiliki retrieval context (graph/knowledge).
- Ambang: grounded ≥ 0.7 layak bonus, < 0.4 penalti parsial.
- Simpan komponen per episode agar bisa di-audit.

### G2 — Failure rate 0.0 mencurigakan (hanya 2 failed dari 415)

Probabilitas 0% gagal untuk sistem yang melakukan 314 MCP calls adalah
bukan sinyal kualitas, melainkan sinyal reward yang salah: episode yang
berakhir karena error tetap dicatat reward positif, atau error tidak
disalurkan ke `record_outcome`.

**Fix proposal:**
- Audit jalur error → `lightning_episode_finish`: semua `status != completed`
  wajib `success=False`.
- Audit `record_action` untuk `status='error'`: harus menurunkan reward episode.
- Cek apakah `retry` memotong error sebelum outcome (akibatnya error tidak
  pernah tercatat).

### G3 — Reward tidak memakai `evidence_status`

`record_outcome` sudah punya field `evidence_status`, tapi belum dijadikan
komponen reward. Reward = "tidak exception" bukan "jawaban benar dengan bukti".

**Fix proposal:**
- `evidence_status` ∈ {verified, partial, unverified, none} → skor parsial:
  verified=1.0, partial=0.5, unverified=0.25, none=0.
- Wajib ada minimal 1 aksi `retrieval` sebelum `success=True` di-boot reward.

### G4 — 11 episode active menggantung (tidak pernah di-finish)

Episode `active` sejak 02 Agu (graph_v3_search, graph_search,
graph_get_context, graph_v3_stats, 6× chat). Tidak ada `completed_at`,
reward, maupun outcome. Ini membuat learning loop kehilangan konteks dan
reward aggregation bias.

**Fix proposal:**
- Auto-finish sweep: episode `active` dengan `started_at` > 24 jam →
  `status='failed'`, `outcome_code='timeout'`, reward 0 (atau -penalti kecil).
- Timeout per task: chat 10 menit, mcp tool 5 menit.
- Tambah guard: `episode_start` dengan `idempotency_key` duplikat harus
  menolak create, bukan create lagi.

### G5 — Cold start bias `strategy_rank`

`context_key` selalu `:text:read:` → strategy_rank melihat semua konteks
sama; `default|default|default|default|none|v1` muncul untuk 95 chat tanpa
variasi konteks. Risk class & action mix tidak dipakai sebagai konteks.

**Fix proposal:**
- Masukkan feature vector ke context: risk_class, action_type mix,
  retrieval hit/miss, model, latency bucket.
- Seed baseline dari 402 episode completed (bukan mulai kosong).
- Evaluation: bandingkan strategy_rank vs uniform random dalam 7 hari
  (gunakan `lightning_regression_check`).

### G6 — Risk class tidak dibedakan (semua `read`)

MCP write ops (graph_v3_upsert_node, graph_v3_link, memory_add, obsidian)
tampil sebagai `:text:read:`. Bahaya: strategi optimasi reward bisa
mendorong perilaku berisiko tanpa deteksi.

**Fix proposal:**
- Registry risk per MCP tool (read/write/external).
- `context_key` memakai risk class aktual; policy engine (action_policy)
  membaca risk dari episode, bukan hanya dari request.
- Episodes dengan action risk write harus butuh `approval` saat commit.

## Prioritas & effort

| Gap | Impact | Effort | Urutan |
|---|---|---|---|
| G4 (episode menggantung + idempotency) | high | low | 1 |
| G2 (failure rate & error path) | high | medium | 2 |
| G3 (evidence_status ke reward) | high | medium | 3 |
| G1 (groundedness ke reward) | medium | medium | 4 |
| G6 (risk class) | medium | low | 5 |
| G5 (cold start strategy_rank) | medium | high | 6 |

## Acceptance gate

1. Zero episode menggantung > 24 jam (sweep aktif).
2. Failed rate ≠ 0 bila error nyata terjadi (uji dengan fault injection).
3. Reward breakdown berisi ≥ 2 komponen (task_success + groundedness/evidence).
4. context_key memisahkan read vs write; policy engine memakai risk class.
5. strategy_rank punya baseline 402 episode + context feature vector.

## Koneksi ke KRS war incident (2026-08-03)

Incident notification loop terkait langsung dengan G6/G2: loop watcher
menjalankan aksi eksternal (notify) tanpa guard state → seandainya episode
lightning membungkus aksi ini, risk class write + reward transisi-status
akan mendeteksi dan menandai sebagai error. Guard rule dari incident
(dedupe window + state-driven notification) menjadi syarat reward G3.

## Next actions

- [ ] Review & approve proposal (owner)
- [ ] Implement G4 (sweep + idempotency guard) — paling kecil, dampak besar
- [ ] Implement G2 (error path → success=False)
- [ ] Implement G3 (evidence_status ke reward)
- [ ] Implement G1, G6, G5 bertahap
- [ ] Update tracker setelah milestone
