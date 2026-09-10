# MCP-Only Pivot — Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax. Each phase is small and independently testable. The primary orchestrator executes this plan in-session; no external subagent dispatch needed.

**Goal:** Hapus `services/wa-enggine/`, `apps/cli/`, dan semua kode WA/CLI dari `services/ai`. Update docker, .env, scripts, docs, AGENTS.md. Setelah selesai, project adalah MCP-only AI server dengan apps/docs sebagai docs site.

**Architecture:** Single FastAPI service (`services/ai`) exposing tools only via MCP stdio (canonical) + optional HTTP MCP bridge for Codex/Claude Code/OpenCode HTTP clients. No WhatsApp. No CLI. `apps/docs` tetap sebagai Astro static docs site.

**Tech Stack:** Python 3.11+, FastAPI, langchain, langgraph, FAISS, SQLite, Neo4j (optional), MCP (FastMCP), Astro/Starlight, TypeScript.

## Global Constraints

* Versi AGENTS.md sebelum perubahan: `2.1.0`. Setelah: `2.2.0`.
* Tidak ada `git commit`/`git push`. Owner commit manual. Branch `pivot/mcp-only-20260911` dibuat tanpa commit.
* Tidak boleh hapus `.env` file kecuali line edit berizin. Tidak boleh hapus `.secrets/`. Tidak boleh hapus `data/`.
* Live WA sessions di `services/wa-enggine/sessions/` — `rm -rf` langsung (owner choose, no backup).
* `chat_id` parameter di life/research/goal tools: **dipertahankan** (MCP juga butuh); hanya docstring dari "WhatsApp chat ID" → "owner chat ID".
* MCP HTTP bridge (`POST /api/chat`) **dipertahankan** untuk Codex/Claude Code/OpenCode HTTP clients.
* Setiap fase harus lulus verifikasi minimal (Phase 9) sebelum lanjut.

---

## Phase 0 — Setup safety

- [ ] **Step 0.1**: `git status --short` — catat baseline working tree
- [ ] **Step 0.2**: `git checkout -b pivot/mcp-only-20260911` — branch tanpa commit
- [ ] **Step 0.3**: Cek file `services/wa-enggine/sessions/` ada (cek ada tidaknya)
- [ ] **Step 0.4**: Cari tahu ukuran `services/wa-enggine/sessions/` (`du -sh`)
- [ ] **Step 0.5**: Catat snapshot ukuran di laporan

## Phase 1 — Purge WA sessions (live auth state)

- [ ] **Step 1.1**: Owner SUDAH confirm `rm -rf services/wa-enggine/sessions/` langsung tanpa backup
- [ ] **Step 1.2**: `git rm -r --cached services/wa-enggine/sessions/` jika ter-track (cek `git ls-files | grep sessions` dulu)
- [ ] **Step 1.3**: `rm -rf services/wa-enggine/sessions/` hapus dari disk
- [ ] **Step 1.4**: Verifikasi: `ls services/wa-enggine/sessions/` 2>&1 | head (expected: not found)

> Catatan: bila `rm -rf` perlu preserve owner scope, gunakan `chown` terlebih dahulu jika folder dimiliki root.

## Phase 2 — Wholesale delete directories

- [ ] **Step 2.1**: `git rm -r --cached services/wa-enggine/` kecuali `services/wa-enggine/sessions/` (kalau masih ada)
- [ ] **Step 2.2**: `rm -rf services/wa-enggine/node_modules services/wa-enggine/dist services/wa-enggine/yarn.lock`
- [ ] **Step 2.3**: `rm -rf services/wa-enggine` (sisa dir)
- [ ] **Step 2.4**: `git rm -r --cached apps/cli/` kecuali `apps/cli/node_modules`, `apps/cli/dist`
- [ ] **Step 2.5**: `rm -rf apps/cli/node_modules apps/cli/dist apps/cli/yarn.lock`
- [ ] **Step 2.6**: `rm -rf apps/cli` (sisa dir)
- [ ] **Step 2.7**: Verifikasi `find . -maxdepth 3 -type d -name "wa-enggine" -o -name "cli" 2>/dev/null | grep -v node_modules`

## Phase 3 — Strip WA from services/ai

- [ ] **Step 3.1**: `rm -rf services/ai/app/wa_tools`
- [ ] **Step 3.2**: `rm -rf services/ai/app/tools/whatsapp`
- [ ] **Step 3.3**: `rm -rf services/ai/app/xninetzy/interfaces/whatsapp`
- [ ] **Step 3.4**: Strip WA imports dari `services/ai/app/main.py` (baca dulu, hapus import WA, pertahankan MCP startup)
- [ ] **Step 3.5**: Hapus tests WA-specific:
  - `services/ai/tests/interfaces/whatsapp/test_admin_verification.py`
  - `services/ai/tests/interfaces/whatsapp/test_wa_media_client.py`
  - `services/ai/tests/interfaces/whatsapp/test_wa_send_media.py`
  - `rm -rf services/ai/tests/interfaces/whatsapp`
- [ ] **Step 3.6**: Hapus `services/ai/tests/interfaces/api/test_security.py` (jika spesifik WA auth) atau rewrite
- [ ] **Step 3.7**: `rm services/ai/tests/manual/hebat_e2e.py` jika WA-only atau rewrite
- [ ] **Step 3.8**: Update tests yang reference `wa_tools`, `whatsapp`, `chat_id="system"`:
  - `services/ai/tests/os/academic/test_captcha_delivery.py` —rewrite tanpa WA delivery
  - `services/ai/tests/os/academic/test_grade_token_coordinator.py` — pertahankan jika MCP, rewrite jika WA
  - `services/ai/tests/os/notifications/test_admin_notifier.py` — rewrite tanpa WA channel
  - `services/ai/tests/os/research/test_deep_research_permissions.py` — rewrite WA ACL
  - `services/ai/tests/tools/test_error_contract.py` — update kontrak tanpa WA
  - `services/ai/tests/architecture/test_foldering_refactor.py` — update expected folder map
  - `services/ai/tests/core/test_configure_internal_auth.py` — rewrite tanpa WA-specific
  - `services/ai/tests/core/test_identity_redaction.py` — rewrite tanpa WA jid
  - `services/ai/tests/core/test_output_sanitization.py` — rewrite tanpa WA-specific
  - `services/ai/tests/interfaces/media/test_media_pipeline.py` — rewrite delivery test
  - `services/ai/tests/interfaces/test_mcp_tool_adapter.py` — verify adapters ok
  - `services/ai/tests/README.md` — update channel list

## Phase 4 — Strip CLI dari services/ai

- [ ] **Step 4.1**: `rm services/ai/app/xninetzy/interfaces/config_cli.py`
- [ ] **Step 4.2**: `rm services/ai/app/xninetzy/interfaces/onboarding_cli.py`
- [ ] **Step 4.3**: `rm services/ai/app/xninetzy/interfaces/host_agent_bridge.py`
- [ ] **Step 4.4**: Hapus `services/ai/tests/interfaces/test_config_cli.py`
- [ ] **Step 4.5**: Hapus `services/ai/tests/interfaces/test_host_agent_bridge.py`
- [ ] **Step 4.6**: Hapus `services/ai/tests/interfaces/test_onboarding_cli.py`
- [ ] **Step 4.7**: Strip CLI imports dari `main.py` jika ada

## Phase 5 — Rewire services/ai core

- [ ] **Step 5.1**: `services/ai/app/xninetzy/agent/response.py` — hapus WA-specific response shape, pertahankan MCP response
- [ ] **Step 5.2**: `services/ai/app/xninetzy/core/identity.py` — pertahankan identity injection (MCP pakai juga), hapus WA-specific
- [ ] **Step 5.3**: `services/ai/app/xninetzy/core/security.py` — hapus WA-specific security, pertahankan MCP auth
- [ ] **Step 5.4**: `services/ai/app/xninetzy/db/migrations.py` — review dan hapus migration WA-specific columns/tables
- [ ] **Step 5.5**: `services/ai/app/xninetzy/interfaces/api/owner_policy.py` — hapus WA-specific policies
- [ ] **Step 5.6**: `services/ai/app/xninetzy/interfaces/api/routes/chat.py` — pertahankan sebagai HTTP MCP bridge, hapus WA-specific
- [ ] **Step 5.7**: `services/ai/app/xninetzy/interfaces/api/routes/debug.py` — audit dan rewrite
- [ ] **Step 5.8**: `services/ai/app/xninetzy/interfaces/media/media_tools.py` — hapus WA delivery, pertahankan MCP
- [ ] **Step 5.9**: `services/ai/app/xninetzy/os/jobs/service.py` dan `tools.py` — hapus WA scheduler references
- [ ] **Step 5.10**: `services/ai/app/xninetzy/os/memory/memory_store.py` — docstring: ganti "WhatsApp" → "owner"
- [ ] **Step 5.11**: `services/ai/app/xninetzy/os/notifications/admin_notifier.py` — hapus WA delivery channel
- [ ] **Step 5.12**: `services/ai/app/xninetzy/os/research/permissions.py` — hapus WA-specific ACL
- [ ] **Step 5.13**: `services/ai/app/xninetzy/os/research/subplanner.py` — hapus WA references
- [ ] **Step 5.14**: `services/ai/app/xninetzy/os/rules/store.py` — docstring update (keep `chat_id`)
- [ ] **Step 5.15**: `services/ai/app/xninetzy/os/academic/hebat/tools.py` — hapus WA references di submission
- [ ] **Step 5.16**: `services/ai/app/xninetzy/os/academic/mahasiswa_portal/captcha_delivery.py` — hapus WA CAPTCHA delivery
- [ ] **Step 5.17**: `services/ai/app/xninetzy/os/academic/mahasiswa_portal/grade_token.py` — hapus WA delivery
- [ ] **Step 5.18**: `services/ai/app/xninetzy/os/academic/mahasiswa_portal/krs_watcher.py` — hapus WA notification
- [ ] **Step 5.19**: `services/ai/app/xninetzy/os/academic/mahasiswa_portal/tools.py` — hapus WA channel
- [ ] **Step 5.20**: `services/ai/app/xninetzy/skills/hebat/tools.py` — hapus WA references
- [ ] **Step 5.21**: `services/ai/app/xninetzy/tools/ecosystem/life_tools.py` — docstring update (keep chat_id)
- [ ] **Step 5.22**: `services/ai/app/xninetzy/tools/ecosystem/goal_tools.py` — docstring update
- [ ] **Step 5.23**: `services/ai/app/xninetzy/tools/ecosystem/research_tools.py` — hapus WA references
- [ ] **Step 5.24**: `services/ai/app/xninetzy/tools/registry.py` — hapus WA + CLI tool registration
- [ ] **Step 5.25**: `services/ai/app/xninetzy/workflow/executor.py` — hapus WA notifier
- [ ] **Step 5.26**: `services/ai/app/xninetzy/workflow/models.py` — hapus WA models
- [ ] **Step 5.27**: `services/ai/app/xninetzy/workflow/notifier.py` — hapus WA channel
- [ ] **Step 5.28**: `services/ai/app/xninetzy/workflow/tools.py` — hapus WA references

## Phase 6 — Update infra config

- [ ] **Step 6.1**: `docker-compose.yml` — hapus block `wa-enggine:`, hapus `cli:`, hapus `WA_MCP_BASE_URL`, hapus `WA_*` env, hapus `CODING_AGENT_*_BRIDGE_*` (kalau CLI-only)
- [ ] **Step 6.2**: `.env.example` — hapus baris `WA_*`, `*_BRIDGE_*`, `CHAT_FAILOVER_WHATSAPP_ONLY`, `ADMIN_JID`, `OWNER_ALLOWED_JIDS`
- [ ] **Step 6.3**: `.env` — preview diff, konfirmasi terakhir ke user (operator boleh proceed jika user sudah confirm), apply edit
- [ ] **Step 6.4**: `scripts/install.sh` — hapus branch `wa-enggine install`, `cli install`, `bridge install`
- [ ] **Step 6.5**: `scripts/install.ps1` — sama (jika ada)
- [ ] **Step 6.6**: `scripts/install_host_agent_bridge.sh` — hapus file
- [ ] **Step 6.7**: `scripts/run_host_agent_bridge.sh` — hapus file

## Phase 7 — Update docs

- [ ] **Step 7.1**: `README.md` — baris 3, 12, 31, 50, 56, 57, 79, 83, 90, 92 — ganti WhatsApp-first narrative jadi MCP-first
- [ ] **Step 7.2**: `xninetzy.md` — section interface (CLI, WhatsApp) — hapus + ganti MCP-first narrative
- [ ] **Step 7.3**: `skills-docs-staging.md` — hapus CLI/WA references
- [ ] **Step 7.4**: `analisis_xninetzy.md` — tandai sebagai historical dengan header `> ARCHIVED 2026-09-11: pivot MCP-only`
- [ ] **Step 7.5**: `docs/AI_PROVIDERS_CODING_AGENTS_MCP.md` — hapus CLI/WA section
- [ ] **Step 7.6**: `docs/superpowers/specs/2026-08-24-session-lifecycle-probe-design.md` — review, kalau terkait WA session lifecycle → tandai historical
- [ ] **Step 7.7**: `apps/docs/src/content/` (jika ada) — audit file terkait WA/CLI

## Phase 8 — Rewrite AGENTS.md

- [ ] **Step 8.1**: Section 8 (Xninetzy MCP Contract) — keep tapi bersihkan dari CLI/WA narrative
- [ ] **Step 8.2**: Section 12 (Architecture Boundary) — ubah diagram: `MCP / HTTP MCP bridge → tools / domains → OS / storage`. Hapus WhatsApp / CLI listing
- [ ] **Step 8.3**: Section 13 (Interface Parity) — hapus WhatsApp, natural-language LangGraph, Codex, Claude Code, OpenCode. Hanya MCP + HTTP MCP bridge untuk HTTP clients
- [ ] **Step 8.4**: Section 25 (AI Verification Commands) — hapus `cd services/wa-enggine && yarn ...`. Pertahankan `services/ai` dan `apps/docs`. Tambah `apps/cli` removed notice
- [ ] **Step 8.5**: Section 27 (Academic Safety Tiers) — tetap
- [ ] **Step 8.6**: Section 28 (External Action Protocol) — pertahankan
- [ ] **Step 8.7**: Section 35 (Security and Secrets) — hapus WhatsApp sessions + Moodle browser state references (no longer present)
- [ ] **Step 8.8**: Section 41 (Canonical End-to-End Loop) — update
- [ ] **Step 8.9**: Frontmatter — bump `version: "2.2.0"`
- [ ] **Step 8.10**: Operating Philosophy + Non-Negotiable Invariants — update S42 untuk tidak menyebut WhatsApp / CLI

## Phase 9 — Update .gitignore

- [ ] **Step 9.1**: Tambah `outputs/` entry (sejajar `output/`)
- [ ] **Step 9.2**: Tambah entry untuk `~/` (root backup folder)
- [ ] **Step 9.3**: Tambah `**/sessions/` pattern jika generic
- [ ] **Step 9.4**: Verifikasi `cat .gitignore`

## Phase 10 — Verifikasi

- [ ] **Step 10.1**: `cd services/ai && uv run ruff check app tests 2>&1 | tee /tmp/ruff.out` — fix errors
- [ ] **Step 10.2**: `cd services/ai && uv run pytest 2>&1 | tee /tmp/pytest.out` — fix errors (WA-specific tests dihapus/ditulis ulang)
- [ ] **Step 10.3**: `cd apps/docs && yarn check 2>&1 | tee /tmp/docs-check.out`
- [ ] **Step 10.4**: `cd apps/docs && yarn build 2>&1 | tee /tmp/docs-build.out`
- [ ] **Step 10.5**: Final grep sweep:
  - `grep -r "whatsapp\|baileys\|wa_enggine\|wa_tools\|whatsapp-first\|onboarding_cli\|host_agent_bridge\|config_cli" --include="*.py" --include="*.md" --include="*.yml" --include="*.sh" --include="*.ts" --include="*.tsx" . 2>/dev/null | grep -v node_modules | grep -v dist | grep -v __pycache__ | grep -v ".git/" | grep -v "_archive/" | grep -v "docs/superpowers/specs/2026-09-11-"`
  - Expected: baris di `apps/docs/src/content/legacy*` (jika ada) + `analisis_xninetzy.md (archived)` + `docs/superpowers/specs/2026-09-11-*audit*` (allowed context)
- [ ] **Step 10.6**: `find . -name "wa-enggine" -o -name "apps/cli" 2>/dev/null` — expected: nothing
- [ ] **Step 10.7**: `git status --short` — expected: many Modified + many Deleted, no new untracked of WA/CLI

## Phase 11 — Final report

- [ ] **Step 11.1**: Tulis ringkasan ke checkpoint memory (via `xninetzy_memory_add` atau local note)
- [ ] **Step 11.2**: Print final diff ringkas
- [ ] **Step 11.3**: Print test results
- [ ] **Step 11.4**: Print instruksi commit manual untuk owner

---

## Self-Review Checklist (after writing)

- [x] Spec coverage: setiap file di Section 3.2 masuk Phase 5+
- [x] No "TBD"/"TODO" dalam plan ini
- [x] Phase granularitas: fase besar, step kecil; setiap fase punya verification gate
- [x] Tidak conflict dengan AGENTS.md invariants
- [x] Branch safety tercakup di Phase 0
- [x] `.env` handled dengan preview (Phase 6.3)
- [x] WA sessions dihapus sesuai owner (Phase 1)
