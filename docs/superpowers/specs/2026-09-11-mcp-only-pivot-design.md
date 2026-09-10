---
title: MCP-Only Pivot — Xninetzy
date: 2026-09-11
status: APPROVED (owner explicit)
scope: pivot project to MCP-only AI; delete WA + CLI layers
auditor: primary orchestrator (opencode)
spec_ref: 2026-09-11-agents-md-audit.md
plan_ref: 2026-09-11-mcp-only-pivot.md
---

# MCP-Only Pivot — Design Spec

## 1. Tujuan

Mengubah `xninetzy` menjadi **MCP-only AI server**. Hapus:

* `services/wa-enggine/` (seluruh Node.js WhatsApp engine)
* `apps/cli/` (seluruh Ink CLI)
* Kode WA + CLI di `services/ai`
* Konfigurasi terkait di `docker-compose.yml`, `.env.example`, `.env`, `scripts/install*`

Pertahankan:

* `services/ai` sebagai runtime utama MCP (FastAPI + langchain + langgraph + FAISS + Neo4j + MCP server)
* `apps/docs` (Astro documentation)
* Obsidian, knowledge, learning, life OS, research, lightning, HITL, dan workflow OS layer
* Semua `chat_id` defaults (MCP also needs chat_id for context)
* `.env` (owner manages), `.secrets/`, `data/`
* WA sessions di `services/wa-enggine/sessions/` — **dihapus langsung** sesuai owner (tidak dibackup)

## 2. Status & Authority

* **Approved by owner**: 2026-09-11 (multiple-choice confirmation):
  * Hapus semua, fokus MCP-only
  * Live WA sessions: hapus langsung (tanpa backup)
  * `.env`: edit `.env.example` + `.env`
* **Spec ref**: `docs/superpowers/specs/2026-09-11-agents-md-audit.md` (akurat, tidak ada klaim salah)
* **AGENTS.md governing policy**: tetap berlaku untuk sisa pekerjaan

## 3. Scope (categorized)

### 3.1 DIHAPUS seluruhnya (delete dir/file)

| Path | Reason |
|------|--------|
| `services/wa-enggine/` (seluruh isi non-ignored) | WA engine tidak dipakai lagi |
| `apps/cli/` (seluruh src + bin) | CLI tidak dipakai lagi |
| `services/ai/app/wa_tools/` | WA-specific code di layer app |
| `services/ai/app/tools/whatsapp/` | WA-specific code di tools |
| `services/ai/app/xninetzy/interfaces/whatsapp/` | WA-specific interface |
| `services/ai/app/xninetzy/interfaces/config_cli.py` | CLI tool |
| `services/ai/app/xninetzy/interfaces/onboarding_cli.py` | CLI tool |
| `services/ai/app/xninetzy/interfaces/host_agent_bridge.py` | CLI bridge ke luar |
| `scripts/install_host_agent_bridge.sh` | WA/CLI infra |
| `scripts/run_host_agent_bridge.sh` | WA/CLI infra |
| `services/ai/tests/interfaces/test_config_cli.py` | Test CLI |
| `services/ai/tests/interfaces/test_host_agent_bridge.py` | Test CLI bridge |
| `services/ai/tests/interfaces/test_onboarding_cli.py` | Test CLI |
| `services/ai/tests/interfaces/whatsapp/` | Tests WA |
| `services/wa-enggine/sessions/` (session files) | Live WA auth state (owner: hapus langsung) |

### 3.2 DIMODIFIKASI (strip + tulis ulang)

| Path | Perubahan |
|------|-----------|
| `services/ai/app/main.py` | Hapus import & wiring WA + CLI bridge |
| `services/ai/app/xninetzy/interfaces/api/routes/chat.py` | Pertahankan sebagai MCP HTTP bridge, atau hapus (lihat sub-decision bawah) |
| `services/ai/app/xninetzy/interfaces/api/routes/debug.py` | Hapus jika hanya terkait WA/CLI auth |
| `services/ai/app/xninetzy/interfaces/api/owner_policy.py` | Hapus referensi WA-specific |
| `services/ai/app/xninetzy/interfaces/media/media_tools.py` | Buang delivery channel WA, pertahankan MCP |
| `services/ai/app/xninetzy/agent/response.py` | Buang WA-specific response shape |
| `services/ai/app/xninetzy/core/identity.py` | Buat identity model general (bukan WA-centric) |
| `services/ai/app/xninetzy/core/security.py` | Buang WA-specific security |
| `services/ai/app/xninetzy/db/migrations.py` | Hapus migration WA-specific columns/tables (jika ada) |
| `services/ai/app/xninetzy/os/academic/{hebat,mahasiswa_portal,qa_portal}/tools.py` | Pertahankan fungsi tapi ganti channel notifikasi |
| `services/ai/app/xninetzy/os/jobs/{service,tools}.py` | Buang WA scheduler references |
| `services/ai/app/xninetzy/os/memory/memory_store.py` | Chat_id semantics tetap (dipakai MCP) — hanya docstring |
| `services/ai/app/xninetzy/os/notifications/admin_notifier.py` | Buang WA delivery, pertahankan MCP-based |
| `services/ai/app/xninetzy/os/research/{permissions,subplanner}.py` | Buang WA channel |
| `services/ai/app/xninetzy/os/rules/store.py` | Chat_id tetap |
| `services/ai/app/xninetzy/skills/hebat/tools.py` | Buang WA references |
| `services/ai/app/xninetzy/tools/ecosystem/*.py` (life/research/goal) | Docstring: "WhatsApp chat ID" → "owner chat ID" |
| `services/ai/app/xninetzy/tools/registry.py` | Hapus tool WA + CLI |
| `services/ai/app/xninetzy/workflow/{executor,models,notifier,tools}.py` | Buang channel WA |
| `services/ai/tests/interfaces/api/test_security.py` | Update untuk non-WA model |
| `services/ai/tests/interfaces/media/test_media_pipeline.py` | Update untuk non-WA model |
| `services/ai/tests/interfaces/test_mcp_tool_adapter.py` | Pastikan adapter tidak reference WA tools |
| `services/ai/tests/README.md` | Update list channels |
| `services/ai/tests/tools/test_error_contract.py` | Update kontrak tanpa WA |
| `services/ai/tests/architecture/test_foldering_refactor.py` | Update expected folders (no whatsapp) |
| `services/ai/tests/core/test_*auth*.py`, `test_identity_redaction.py`, `test_output_sanitization.py` | Update tanpa WA-specific tests |
| `services/ai/tests/manual/hebat_e2e.py` | Hapus atau update |
| `services/ai/tests/os/{academic,jobs,notifications,research}/*.py` | Tests yang terkait WA channel-specific |
| `docker-compose.yml` | Hapus service `wa-enggine:` + `cli:` + env vars + healthchecks |
| `.env.example` | Hapus `WA_MCP_*`, `WA_MEDIA_*`, `CODING_AGENT_*_BRIDGE_*`, `ADMIN_JID`, `OWNER_ALLOWED_JIDS`, `CHAT_FAILOVER_WHATSAPP_ONLY` |
| `.env` | Hapus baris/komentar terkait WA/CLI/bridge (preview dulu) |
| `scripts/install.sh` | Hapus branch WA/CLI install |
| `scripts/install.ps1` | Hapus branch WA/CLI install (jika ada) |
| `scripts/krs-watch.sh` | Tetap (KRS war — tidak terkait WA) |
| `README.md` | Tulis ulang pesan: "WhatsApp-first" → "MCP-first Personal Learning OS & Life OS" |
| `xninetzy.md` | Tulis ulang interface listing (hapus WhatsApp & CLI) |
| `analisis_xninetzy.md` | Arsipkan sebagai `analisis_xninetzy.archived-2026-09-11.md`, atau tulis ulang section WA / tandai historical |
| `skills-docs-staging.md` | Tulis ulang tanpa CLI/WA references |
| `docs/AI_PROVIDERS_CODING_AGENTS_MCP.md` | Buang CLI/WA sections |
| `docs/superpowers/specs/2026-08-24-session-lifecycle-probe-design.md` | Review — mungkin terkait WA session lifecycle; arsipkan |
| `AGENTS.md` | Section 12 (Architecture), 25 (Verification), 35 (Secrets), 42 (Invariants) — ditulis ulang tanpa WA/CLI |
| `.gitignore` | Tambah `outputs/` (sejajar `output/` yang sudah ada), tambah pola `~` & backup dirs |

### 3.3 DIPERTAHANKAN tanpa perubahan

| Path | Alasan |
|------|--------|
| `.env` (root) | Owner manages (kami edit atas izin eksplisit) |
| `.secrets/` | Neo4j auth — bukan WA/CLI |
| `data/` (documents, pixelrag, tmp) | Tidak terkait |
| `services/ai/data/*` | Internal data dirs, tidak terkait WA/CLI |
| `services/ai/app/xninetzy/tools/ecosystem/life_tools.py` dsj (chat_id default) | `chat_id` tetap dipakai MCP |
| `services/ai/app/xninetzy/os/life/*` | Life OS tanpa WA |
| `services/ai/app/xninetzy/os/lightning/*` | Lightning routing |
| `services/ai/app/xninetzy/os/knowledge/*` | Knowledge / RAG |
| `services/ai/app/xninetzy/os/research/*` core | Research OS |
| `services/ai/app/xninetzy/os/hitl/*` | HITL approval system |
| `services/ai/app/xninetzy/os/backup/*` | Backup system |
| `services/ai/app/xninetzy/domains/it_learning/*` | IT learning domain |
| `services/ai/app/xninetzy/interfaces/mcp_*` | MCP server, adapter, runtime — INTI |
| `services/ai/app/xninetzy/interfaces/api/health.py` | Healthcheck (tidak terkait WA/CLI) |
| `services/ai/app/xninetzy/interfaces/api/reminders.py` | Reminder API endpoint |
| `services/ai/app/xninetzy/skills/*` (xninetzy-* built-in) | MCP-accessible skills |
| `apps/docs/*` | Astro docs |
| `services/ai/.agents/skills/` | Skill catalog MCP |
| `tests/os/academic/hebat/`, `tests/os/research/` yang tidak spesifik WA | Tests inti |
| `krs-watch.sh` | KRS war (tidak terkait WA) |

### 3.4 KEPUTUSAN SUB-PINDAI (sub-decisions)

* **HTTP API endpoint `POST /api/chat` di `services/ai/app/xninetzy/interfaces/api/routes/chat.py`**:
  * CLI menggunakan endpoint ini
  * MCP stdio tidak menggunakan HTTP
  * MCP HTTP bridge (untuk Codex/Claude Code/OpenCode via HTTP) menggunakan ini
  * **Keputusan**: pertahankan endpoint untuk HTTP MCP bridge; port number, env vars dipertahankan
* **Notifikasi Channel** (untuk admin_notifier, hitl, etc.):
  * Saat ini mungkin WA + MCP
  * **Keputusan**: channel = MCP-based (saved to knowledge / inbox), tidak ada WA fallback
* **Owner identity injection** (`MCP_PRINCIPAL_ID`, `MCP_PRINCIPAL_NAME`):
  * Tetap dipakai (server-side injected)
  * Owner ALLOWED_JIDs tidak relevan setelah WA hilang

## 4. Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| Branch `main` tercemar | Bekerja pada branch `pivot/mcp-only-20260911`; commit hanya di branch (opsional, tidak wajib) |
| Tests gagal karena WA-specific references | Identifikasi & hapus satu per satu; hanya tersisa tests MCP-pure |
| Subtle WA references pada docstring/logging | Grep `whatsapp\|baileys\|wa_enggine\|wa_tools` final pass; report remaining |
| AGENTS.md drift dengan global setelah perubahan | Tulis ulang section terkait; bump versi ke `2.2.0` |
| `.env` kehilangan rahasia penting | Preview diff sebelum edit |
| Owner lupa credentials live WA sudah dihapus | Laporkan di final report dengan instruksi "jika butuh WA lagi, harus install ulang wa-enggine dari history" |

## 5. Definition of Done

* [ ] `services/wa-enggine/` tidak ada
* [ ] `apps/cli/` tidak ada
* [ ] `services/ai` tidak punya direktori/file dengan nama `wa`, `whatsapp`, `cli` (kecuali nama skill yang sah tanpa prefix `wa`)
* [ ] `services/ai/tests` tidak punya tests WA/CLI-specific
* [ ] `docker-compose.yml` tidak punya service `wa-enggine` atau `cli`
* [ ] `.env.example` dan `.env` tidak punya `WA_*`, `*_BRIDGE_*`, `*_WHATSAPP_*`, `*CLI*` env
* [ ] `scripts/install.sh`, `scripts/install.ps1` tidak punya branch WA/CLI install
* [ ] `README.md`, `xninetzy.md`, `skills-docs-staging.md`, `apps/docs` docs tidak menyebut WA/CLI sebagai interface utama (boleh menyebut di historical/migration note)
* [ ] `AGENTS.md` Section 12, 25, 35, 42 reflect MCP-only architecture; version `2.2.0`
* [ ] `cd services/ai && uv run ruff check app tests` lulus
* [ ] `cd services/ai && uv run pytest` lulus atau tests WA/CLI dihapus dengan documented reason
* [ ] `cd apps/docs && yarn check && yarn build` lulus
* [ ] `git status --short` menampilkan perubahan sebagai uncommitted (owner commit manual)

## 6. Anti-Overreach (saya TIDAK akan)

* ❌ `git commit` / `git push` (S34 AGENTS.md)
* ❌ Hapus `.env` file (selain edit izin line)
* ❌ Hapus `.secrets/`
* ❌ Mengubah Neo4j config atau vector DB files runtime
* ❌ Touch `data/` runtime data
* ❌ Asumsi apa yang owner inginkan tanpa konfirmasi eksplisit

## 7. Urutan Eksekusi (high-level)

```
Phase 0 — git branch
   create pivot/mcp-only-20260911 (no commit)

Phase 1 — Snapshot WA sessions then purge
   services/wa-enggine/sessions/ — hapus (owner: tanpa backup)

Phase 2 — Hapus services
   services/wa-enggine/ (rm -rf, kecuali sessions & node_modules)
   apps/cli/ (rm -rf, kecuali node_modules)

Phase 3 — Strip WA dari services/ai
   services/ai/app/wa_tools/ — hapus
   services/ai/app/tools/whatsapp/ — hapus
   services/ai/app/xninetzy/interfaces/whatsapp/ — hapus
   main.py — hapus WA imports
   interfaces/{config_cli,onboarding_cli,host_agent_bridge}.py — hapus
   tests WA-specific — hapus
   tests yang import WA modules — fix atau hapus

Phase 4 — Strip CLI dari services/ai
   (already covered in Phase 3)

Phase 5 — Update docker-compose, .env files, install scripts
   docker-compose.yml — hapus wa-enggine & cli services
   .env.example — strip WA/CLI
   .env — strip WA/CLI (preview + apply)
   scripts/install.sh, install.ps1 — strip WA/CLI

Phase 6 — Rewrite docs
   README.md, xninetzy.md, skills-docs-staging.md, analisis_xninetzy.md
   apps/docs content jika terkait
   docs/AI_PROVIDERS_CODING_AGENTS_MCP.md

Phase 7 — Rewrite AGENTS.md
   Section 12, 25, 35, 42
   Bump versi ke 2.2.0

Phase 8 — Update .gitignore
   outputs/ entry
   ~ entry (root backup)

Phase 9 — Verifikasi
   cd services/ai && uv run ruff check app tests
   cd services/ai && uv run pytest
   cd apps/docs && yarn check && yarn build
   grep final sweep

Phase 10 — Laporan
   Diff summary, test results, owner commit instructions
```

## 8. References

* Spec audit: `docs/superpowers/specs/2026-09-11-agents-md-audit.md`
* Plan: `docs/superpowers/plans/2026-09-11-mcp-only-pivot.md`
* AGENTS.md governing policy: `/home/misbahul45/code/xninetzy/AGENTS.md` (akan diupdate ke v2.2.0)
