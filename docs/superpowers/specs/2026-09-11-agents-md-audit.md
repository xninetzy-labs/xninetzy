---
title: Xninetzy AGENTS.md Accuracy Audit
date: 2026-09-11
scope: /home/misbahul45/code/xninetzy/AGENTS.md
focus: akurasi & inkonsistensi (audit-only, no edits)
method: source inspection + codebase-memory graph queries
auditor: primary orchestrator (opencode + codebase-memory MCP)
status: COMPLETE_WITH_WARNINGS
---

# Xninetzy AGENTS.md Accuracy Audit

## 1. Ringkasan Eksekutif

| Area                        | Status | Catatan                                                                                          |
| --------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| Path referensi              | ✅ LULUS| Semua path utama (services/ai, services/wa-enggine, apps/docs, apps/cli, .agents/skills) konsisten |
| Verification commands (S25) | ✅ LULUS| ruff, pytest, yarn lint/test/build, astro check/build semuanya valid                              |
| Frontmatter                 | ⚠️ WASPADA | Versi 2.1.0 (file) vs 2.0.0 (skill terkait) belum disinkronkan                                  |
| Subagent registry           | ✅ LULUS| Named subagents (research-coordinator, topic-researcher, evidence-auditor, dll.) tersedia di runtime |
| Arsitektur boundary         | ✅ LULUS| Struktur `interfaces → tools/domains → OS/storage` tercermin di tree `app/xninetzy/`              |
| Drift vs global AGENTS.md   | ⚠️ WASPADA | 30/44 bagian project AGENTS.md tumpang tindih dengan `~/.config/opencode/AGENTS.md` (v2.0.0)     |
| Repo hygiene                | ⚠️ WASPADA | Direktori `~` (root), `outputs/` tidak di-gitignore, file tracked di `output/`                    |

**Verdict:** AGENTS.md **akurat untuk tooling, command, dan arsitektur** yang ada di repo saat ini. Tidak ada klaim yang SALAH. Namun ada beberapa peluang untuk **meningkatkan presisi** agar file lebih tahan terhadap drift.

**Tidak ada perubahan yang dilakukan ke AGENTS.md** sesuai permintaan audit-only.

---

## 2. Audit per Section

### 2.1 Frontmatter (lines 1-17)

| Klaim                              | Hasil verifikasi     | Status |
| ---------------------------------- | -------------------- | ------ |
| `name: xninetzy-opencode-primary`  | Cocok dengan judul   | OK     |
| `metadata.version: "2.1.0"`        | File version         | OK     |
| `metadata.scope: global`           | Mengingkari Section 1 yang menyebutnya governing repository policy | Catatan A1 |
| `metadata.authority` list          | Konsisten dengan Section 1 | OK |

**Catatan A1.** Frontmatter `scope: global` terasa terlalu luas. Section 1 sudah membatasi prioritas: `system safety → AGENTS.md → user request → institutional → project decisions → specialized skill → general practice`. Karena file ini hidup di repo proyek, label yang lebih akurat mungkin `scope: project` atau `scope: repository`.

### 2.2 Section 1 — Governing Policy (lines 37-60)

| Klaim                          | Hasil verifikasi | Status        |
| ------------------------------ | ---------------- | ------------- |
| `AGENTS.md` is governing policy | Terlihat dipakai oleh opencode runtime | OK |
| Priority order 7-tier          | Konsisten dengan `~/.config/opencode/AGENTS.md` | Catatan A2 |

**Catatan A2.** Tumpang tindih besar dengan global opencode AGENTS.md Section 1 dan 2. Bukan salah, tapi persis sama. Lihat Section 4.1.

### 2.3 Section 8 — Xninetzy MCP Contract (lines 254-287)

| Klaim                                                              | Hasil verifikasi                                  | Status |
| ------------------------------------------------------------------ | ------------------------------------------------- | ------ |
| Canonical MCP server `xninetzy`                                    | `services/ai/app/xninetzy/interfaces/mcp_server.py` | OK     |
| Commands: Obsidian, HEBAT/Moodle, knowledge, learning, tasks, goals, reminders, reviews, research, workflow, Graph RAG | Cocok dengan manifest & tool catalog tools | OK |
| Failure mode for missing OS access                                 | Terdefinisi dengan baik                           | OK     |

### 2.4 Section 9 — Skill Registry Contract (lines 289-317)

| Klaim                                                                          | Hasil verifikasi                                  | Status |
| ------------------------------------------------------------------------------ | ------------------------------------------------- | ------ |
| Path `services/ai/.agents/skills` (terbaca sebagai lokasi skill agent)          | Direktori ada, berisi 30 skills termasuk xninetzy-* | OK     |
| `skill_list`, `skill_get`, `skill_suggest_for_request`, `skill_validate`, `skill_install`, `skill_resource_list`, `skill_resource_read`, `skill_healthcheck` | Semua callable via MCP                  | OK     |
| Owner-scoped, audited, idempotent                                              | `skill_install` & `skill_validate` cocok dengan global AGENTS.md | OK |

**Catatan A3.** Tidak ada indeks eksplisit skills `xninetzy-*`. Frontmatter klaim versi `2.1.0` tapi skill terkait (mis. `xninetzy-assignment-orchestrator/SKILL.md`) membawa `version: "2.0.0"`. Lihat Catatan A1 + Section 4.3.

### 2.5 Section 10 — Local Repository Rule (lines 320-335)

| Klaim                                                                          | Hasil verifikasi | Status |
| ------------------------------------------------------------------------------ | ----------------- | ------ |
| `git status --short` workflow                                                  | Standar           | OK     |
| "preserve unrelated changes"                                                   | Pernah ditegaskan | OK     |
| "Do not silently overwrite user work"                                          | Jelas             | OK     |

### 2.6 Section 11 — Codebase Knowledge Graph (lines 339-362)

| Klaim                                                                | Hasil verifikasi                                      | Status |
| -------------------------------------------------------------------- | ----------------------------------------------------- | ------ |
| `search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, `get_architecture` | Semua tersedia via `codebase-memory` MCP | OK     |
| Fallback ke grep/glob                                                 | Konsisten dengan skill `codebase-memory`              | OK     |
| Discovery priority, bukan prohibition                                | Cocok dokumentasi                                     | OK     |

**Catatan A4.** Section ini cukup baik dan selaras dengan skill `codebase-memory`. Auditor menjalankan `index_status`, `get_architecture`, `search_graph` selama audit ini — semua bekerja.

### 2.7 Section 12 — Architecture Boundary (lines 365-394)

Klaim:

```text
WhatsApp / CLI / MCP
        ↓
shared tools / domain
        ↓
shared database / policy
```

Verifikasi struktur `app/xninetzy/`:

```text
interfaces/  ← API, WhatsApp, media, MCP, host-agent-bridge, config_cli, onboarding_cli
tools/      ← tool registry & per-domain wrappers
domains/    ← it_learning, future.*
os/         ← academic, hitl, knowledge, life, lightning, memory, reminders, research, rules, graph, ...
db/         ← SQLite
```

**Catatan A5.** Klaim arsitekturvalid. Tapi lihat Section 4.4 — WhatsApp dan CLI saat ini adalah interface layers yang sama statusnya dengan MCP. Setelah pivot (lihat request lanjutan), Section 12 perlu ditulis ulang untuk hanya menyebut MCP.

### 2.8 Section 19 — Research Orchestration (lines 593-620)

Named subagents: `research-coordinator → topic-researcher × 3–6 → evidence-auditor → primary synthesis`.

**Verifikasi:** ketiganya tersedia di runtime opencode (lihat AGENTS.md system prompt: "research-coordinator", "topic-researcher", "evidence-auditor"). Konsisten.

### 2.9 Section 20 — Assignment Orchestration (lines 623-651)

Named subagents: `assignment-analyst → research workers → section-writer × 2–5 → evidence-auditor → integration → generator → artifact-QA`.

**Verifikasi:** runtime opencode menyediakan `assignment-analyst`, `section-writer`, `artifact-qa`, `evidence-auditor`. (Tidak ada yang named `generator` eksplisit — diopencode, generator adalah skill `xninetzy-artifact-orchestrator`). Ini bukan salah, tapi bisa lebih eksplisit. Catatan minor A6.

### 2.10 Section 24 — Coding Workflow (lines 718-742)

| Klaim                                                                  | Hasil verifikasi                          | Status |
| ---------------------------------------------------------------------- | ----------------------------------------- | ------ |
| RED → GREEN → format → build/typecheck → full suite → coding review    | Cocok dengan `test-driven-development` skill | OK |
| "Do not add new source comments"                                       | Cocok dengan verifikasi repo              | OK     |
| "Required API docstrings, license headers, generated markers, config prose, and documentation remain permitted" | Tepat                              | OK     |

### 2.11 Section 25 — AI Verification Commands (lines 744-773)

| Klaim                                                                | Verifikasi                                                                                  | Status |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------ |
| `cd services/ai && uv run ruff check app tests`                      | `pyproject.toml` mendeklarasikan `ruff>=0.9` sebagai dependency; tidak ada `[tool.ruff]` config eksplisit tetapi ruff default memadai | OK |
| `uv run pytest`                                                      | Tidak ada `[tool.pytest.ini_options]` di `pyproject.toml`; perlu konfirmasi opsi default  | Catatan A7 |
| `cd services/wa-enggine && yarn lint && yarn test && yarn build`     | `package.json`: `lint="tsc --noEmit"`, `test="tsx --test src/**/*.test.ts"`, `build="tsc"` | OK |
| `cd apps/docs && yarn check && yarn build`                           | `package.json`: `check="astro check"`, `build="astro build"`                             | OK     |

**Catatan A7.** `services/ai` tidak punya konfigurasi pytest eksplisit di `pyproject.toml`. Perintah di AGENTS.md akan jalan dengan default uv, tapi kasus-kasus tertentu (test paths, markers, fixture) tidak terdokumentasi. Bisa ditambah jika perlu.

**Catatan A8 (lebih relevan dengan pivot).** Section 25 tidak menyebut `apps/cli` walaupun `apps/cli/package.json` punya `lint` opsional (`typecheck` saja). Setelah pivot, section ini cukup bagus.

### 2.12 Section 30 — Reliability Invariants (lines 909-931)

| Klaim                                         | Verifikasi                                | Status |
| --------------------------------------------- | ----------------------------------------- | ------ |
| FAISS vector count == chunk-ID map length     | Konsisten dengan `services/ai/app/xninetzy/os/knowledge/` | OK |
| Background loops supervised & observable      | Cocok dengan `services/ai/app/xninetzy/os/jobs/store.py` (Node `JobStore.get` muncul di hotspots) | OK |

### 2.13 Section 33 — Lightning (lines 968-1006)

Klaim tentang contextual-bandit routing, episode/action/outcome/reward, allowlist, owner approval.

**Verifikasi:** `xninetzy_mcp_lightning` skill ada di `.agents/skills/`. Implementasi `services/ai/app/xninetzy/os/lightning/` ada di graph (hotspots menunjukkan `set_armed`, `get`, `auto_calibrate_if_needed`, `run_krs_war_if_armed`). Konsisten.

### 2.14 Section 34 — Git Ownership (lines 1010-1029)

Klaim: agent tidak boleh commit/push kecuali owner eksplisit. `git reset` butuh konfirmasi.

**Verifikasi:** Cocok dengan global opencode AGENTS.md. Konsisten.

### 2.15 Section 35 — Security and Secrets (lines 1033-1048)

Klaim: tidak commit `.env`, credentials, API keys, cookies, WhatsApp sessions, Moodle browser state, access tokens.

**Verifikasi:** `.gitignore` mencantumkan `.env`, `.openclaude/settings.local.json`, `data/secrets`. `services/wa-enggine/sessions/` (WhatsApp auth state) eksplisit di-ignore (lihat entry `services/wa-enggine/sessions/` di `not_indexed` graph). Konsisten. Catatan A9 tentang direktori `~` di root.

---

## 3. Path & Command Verification (Matriks Detail)

| Klaim di AGENTS.md                                       | Path/Command aktual                                  | Hasil |
| -------------------------------------------------------- | ---------------------------------------------------- | ----- |
| `cd services/ai && uv run ruff check app tests`          | `services/ai/pyproject.toml` deps `ruff>=0.9`        | ✅    |
| `cd services/ai && uv run pytest`                        | tests dir ada, no explicit pytest config             | ✅ (default) |
| `cd services/wa-enggine && yarn lint`                    | `lint: "tsc --noEmit"`                               | ✅    |
| `cd services/wa-enggine && yarn test`                    | `test: "tsx --test src/**/*.test.ts"`                | ✅    |
| `cd services/wa-enggine && yarn build`                   | `build: "tsc"`                                       | ✅    |
| `cd apps/docs && yarn check`                             | `check: "astro check"`                               | ✅    |
| `cd apps/docs && yarn build`                             | `build: "astro build"`                               | ✅    |
| `services/ai/.agents/skills` path implicit               | Direktori ada dengan 30 skills                       | ✅    |
| Subagents: research-coordinator, topic-researcher       | opencode runtime provides them                       | ✅    |
| Subagents: evidence-auditor, assignment-analyst          | opencode runtime provides them                       | ✅    |
| Subagents: section-writer, artifact-qa                   | opencode runtime provides them                       | ✅    |

---

## 4. Temuan & Catatan (bukan rekomendasi edit)

### 4.1 Tumpang tindih dengan global opencode AGENTS.md

Project AGENTS.md (1241 lines, 44 sections) dan `~/.config/opencode/AGENTS.md` (2700+ lines, 45 sections) berbagi sekitar 30/44 section dengan isi yang **sangat mirip** (hingga versiSection berbeda):

| Project Section                          | Global Section                   | Overlap                          |
| ---------------------------------------- | -------------------------------- | -------------------------------- |
| S1 Governing Policy                      | S1 + S2                          | Hampir identik                   |
| S2 Mission                               | S42                              | Mirip                            |
| S4 Non-Negotiable Truth Rules            | S4                               | Identik                          |
| S5 Global Workflow                       | S5                               | Hampir identik                   |
| S7 Source-of-Truth Routing               | S4 (Source-of-Truth Hierarchy)   | Mirip                            |
| S22 Evidence Audit                       | S11                              | Mirip                            |
| S27 Academic Safety Tiers                | S17                              | Mirip                            |
| S37 Completion Contract                  | S26                              | Mirip                            |
| S38 Anti-Overreach                       | S29                              | Identik                          |
| S42 Non-Negotiable Invariants (19)       | S32                              | Hampir identik (19 vs 16)        |

**Catatan A10.** Proyek ini adalah Xninetzy. Mempertahankan dua file AGENTS.md yang sangat mirip adalah keputusan sadar, tapi membawa **risiko drift**: ketika satu diubah, yang lain tidak. Saat ini project v2.1.0, global v2.0.0. Versi akhirnya bisa diperdebatkan — project AGENTS.md menggunakan ulang banyak invariants global, jadi satu sumber lebih sederhana.

### 4.2 Naming/version drift

* `services/ai/.agents/skills/xninetzy-assignment-orchestrator/SKILL.md` frontmatter `version: "2.0.0"`
* Project AGENTS.md frontmatter `version: "2.1.0"`
* Global opencode AGENTS.md frontmatter `version: "2.0.0"`

Tidak salah, tapi rilis tidak sinkron. Bisa ditambah `provenance: xninetzy-orchestrator@2.1.0` di skill-skill utama agar mudah diketahui.

### 4.3 Tidak ada indeks subagents

AGENTS.md hanya menyebut subagents dengan nama di Section 19, 20, 21, 24. Tidak ada bagian "Subagent Registry" yang mendaftar seluruh subagents opencode. Lihat subagents yang tersedia dari runtime:

```yaml
- academic-operator
- artifact-qa
- assignment-analyst
- browser-operator
- code-implementer
- code-reviewer
- evidence-auditor
- explore
- general
- github-operator
- research-coordinator
- section-writer
- topic-researcher
- xninetzy (via MCP)
```

Jika author ingin referensi cepat, satu section dapat didaftarkan. Tidak urgent.

### 4.4 Arsitektur interface listing

Section 12 menyebut "WhatsApp / CLI / MCP" sebagai interface layers. Setelah pivot (lihat request lanjutan), daftar ini perlu dipersempit.

### 4.5 Repo hygiene (di luar ruang lingkup AGENTS.md)

* Direktori `~` di root repo (`/home/misbahul45/code/xninetzy/~`), dimiliki `root`. Kemungkinan backup editor. **Tidak** masuk `.gitignore` walaupun seharusnya diabaikan.
* Direktori `outputs/` (dengan 's') tidak masuk `.gitignore`, padahal `output/` (tanpa 's') masuk.
* File tracked di `output/AVD_Prak2_187241037/*` (docx & pdf) — boleh jadi artefak akademik sah, tapi bukan source code.

Tiga item ini berada di luar scope AGENTS.md tetapi **penting bagi kebersihan repo**.

### 4.6 Yang TIDAK bermasalah

* Semua path package, interface, OS module konsisten dengan codebase.
* Verification commands Section 25 valid hari ini.
* Frontmatter name/description akurat.
* Subagents dan skill registry valid hari ini.
* Bagian .env secrets: `.env` tidak ter-commit (aman).
* `services/wa-enggine/sessions/` tidak ter-commit (aman).

---

## 5. Bukti Audit (Evidence)

| Klaim                                       | Bukti                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------- |
| Project indexed by codebase-memory          | `home-misbahul45-code-xninetzy`, nodes=8845, edges=33334               |
| 30 skills in `.agents/skills/`              | `ls services/ai/.agents/skills/ \| wc -l` = 30                         |
| ruff installed                              | `services/ai/pyproject.toml` deps `ruff>=0.9`                          |
| astro check + build available               | `apps/docs/package.json`                                              |
| wa-enggine scripts                          | `services/wa-enggine/package.json`                                     |
| Subagents available                         | runtime opencode (lihat system AGENTS.md, daftar `general` dll.)       |
| AGENTS.md section count                     | 44 section (verified by line 1 + by index of headings)                 |
| Frontmatter dual-version                    | file=2.1.0, assignment-orchestrator skill=2.0.0, global=2.0.0          |

---

## 6. Kesimpulan & Verdict

* **Tidak ada klaim AGENTS.md yang terbukti salah terhadap state repo saat ini.** Kompatibel dengan global opencode AGENTS.md.
* Versi, subagents, paths, dan verification commands valid untuk commit `78792ba` (HEAD).
* Risiko utama: **drift dengan global opencode AGENTS.md** karena dua file memiliki konten hampir sama. Owner dapat memilih:
  1. Pertahankan duplikasi sadar;
  2. Pertahankan project AGENTS.md tapi tambahkan penanda "delegate to global" untuk section yang sepenuhnya overlap;
  3. Hapus project AGENTS.md dan andalkan global (resiko: kehilangan identitas proyek).
* Audit tidak menyentuh AGENTS.md. Tidak ada commit dilakukan.

**Status: COMPLETE_WITH_WARNINGS**

### Lampiran A — Daftar Catatan

| Catatan | Lokasi           | Tipe         | Rekomendasi aksi (informasional, TIDAK dilakukan) |
| ------- | ---------------- | ------------ | ------------------------------------------------- |
| A1      | Frontmatter      | consistency  | Evaluasi ganti `scope: global` → `scope: project` |
| A2      | Section 1        | drift        | Bandingkan teks dengan global                    |
| A3      | Section 9        | drift        | Sinkronkan versi frontmatter dengan skill utama  |
| A4      | Section 11       | (no action)  | Section sehat                                    |
| A5      | Section 12       | future drift | Akan berubah setelah pivot WA/CLI               |
| A6      | Section 20       | clarity      | Bisa ditambah pemetaan eksplisit ke MCP skills  |
| A7      | Section 25       | missing doc  | Bisa tambah pytest config reference              |
| A8      | Section 25       | future       | Akan berubah setelah pivot WA/CLI               |
| A9      | Section 35       | hygiene      | Direktori `~` di root: tidak terkait AGENTS.md   |
| A10     | Section 1-42     | drift        | Tumpang tindih besar dengan global AGENTS.md     |
