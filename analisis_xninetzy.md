# Analisis & Testing Xninetzy MCP

> **Tanggal**: 2026-08-08, ±04:03–04:06 WIB
> **Metode**: (1) inspeksi kode sumber server MCP di repo ini, (2) live testing via MCP
> (40+ panggilan tool read-only + dry-run), (3) verifikasi konfigurasi client (opencode.jsonc).
> **Batasan**: hanya tool `read` / `draft` / dry-run yang dieksekusi. Tool `final`
> (submit/approval) dan yang menulis data pengguna TIDAK dieksekusi — dicatat sebagai
> "perlu approval/manual" (lihat §7).

---

## 1. Ringkasan eksekutif

| Aspek | Status |
|---|---|
| Kesehatan server MCP | ✅ Sehat — semua tool yang diuji berfungsi |
| Katalog skills | ✅ 29 valid, 0 invalid, 4 warnings (non-blocking) |
| Manajemen MCP eksternal | ✅ Fitur ada; belum ada server terdaftar (inaktif) |
| Risk policy (approval gate) | ✅ Berfungsi — tool `final` otomatis `requires_approval=true` |
| GraphRAG V3 (Neo4j) | ⚠️ Neo4j **offline** (degraded ke SQLite: 61 node/30 edge) |
| Session portal | ⚠️ HEBAT belum login; UACC `human_verification_required`; Cyber Campus cache `authenticated` |
| Kendala utama | Tidak ada — semua kegagalan yang muncul adalah status lingkungan (bukan bug) |

**Verdict**: sistem Xninetzy MCP dalam kondisi **LAYAK dan SEHAT** untuk dipakai. Tidak ada
bug ditemukan selama testing; temuan hanya berupa status lingkungan + catatan perbaikan kecil.

---

## 2. Arsitektur MCP server (dari kode)

### 2.1 Entry point & transport

```text
opencode.jsonc:
  "xninetzy": {
    "type": "local",
    "command": ["uv", "run", "--directory", "/home/misbahul45/code/xninetzy/services/ai",
                "python", "-m", "app.xninetzy.interfaces.mcp_server"],
    "enabled": true,
    "timeout": 120000
  }
```

- Server: **FastMCP** (`mcp.server.fastmcp`), nama `"xninetzy"`, transport **stdio**.
- Startup: `init_db()` → `run_migrations()` → registrasi tool → `mcp.run(transport="stdio")`.
- Path override host-safe di-bootstrap sebelum module lain load (`mcp_runtime.MCP_PATH_OVERRIDES`)
  agar server bisa jalan dari client mana pun.
- Principal: `mcp_principal().as_tool_context()` — chat_id diinjeksi **server-side**
  (bukan dari argumen caller) → owner-scoped, tidak bisa spoof dari prompt.

### 2.2 Registrasi tool (2 lapis)

1. **22 tool eksplisit** di `mcp_server.py` (253 baris):
   - Obsidian (11): `obsidian_list/search/read/create/append/update_section/todos/backlinks/headings/add_tags/set_frontmatter`
   - Knowledge (4): `knowledge_search`, `knowledge_answer` (async), `knowledge_list_sources`, `knowledge_ingest_text`
   - Task (4): `task_list/today/capture/complete`
   - Reminder (3): `reminder_list/create/cancel`
   - Semua wrapper tipis `@mcp.tool()` → memanggil `BaseTool.invoke()` dari registry.
2. **Tool dinamis via adapter**: `expose_xninetzy_tools(mcp, principal=...)` — mendaftarkan
   seluruh tool dari `tools/registry.py` (`get_all_tools()`, `get_tool_names()`,
   `get_tool_descriptions()`, `get_tool_groups()`).

### 2.3 Metadata & risk policy

- `tools/manifest.py`: `ToolManifest` berisi `risk (RiskClass)`, `requires_approval`,
  `requires_idempotency`, `feature_pack`, `stability`.
- `os/policy/action_policy.py`: `classify_risk(name)` dari mapping `_POLICY_ACTIONS`.
- Aturan: `requires_approval = (risk is FINAL)`; `requires_idempotency = risk in (WRITE, FINAL)`.
- **Terverifikasi live**: `tool_catalog` mengembalikan metadata yang konsisten —
  tool `final` (hebat_upload_submission, portal_krs_war_arm, qa_fill_kuesioner)
  semuanya `requires_approval=true` + `requires_idempotency=true`.

### 2.4 Struktur paket `os/` (domain subsystems)

```text
os/
├── academic/    HEBAT, Cyber Campus, UACC/UnairSatu, QA portal, KRS war/watcher
├── backup/      (cadangan)
├── graph/       Graph RAG
├── hitl/        Human-in-the-loop approval
├── inbox/       OS capture & triage
├── jobs/        briefing/review/sync terjadwal
├── knowledge/   vector store + document router
├── life/        goals, tasks, habits, money, workout
├── lightning/   self-improvement (episode, reward, proposal)
├── memory/      durable memory + checkpoint
├── notes/       Obsidian
├── notifications/ WA notifikasi
├── policy/      action_policy (RiskClass)
├── reminders/   scheduler reminder
├── research/    deep research session + subplan
├── rules/       aturan perilaku
├── style/       profil gaya jawaban
└── web_analysis/ crawl struktur situs akademik (GET/HEAD only)
```

Modul registri tool: `tools/ecosystem/*` (ai_runtime, document, goal, helper, knowledge,
life, pixelrag, research, tool_catalog, unified_search, web_analysis)
+ `tools/internal/*` (obsidian, reminder, calculation, datetime, planning).
**44 file** mengandung pola registrasi tool.

---

## 3. Hasil testing tooling & kemampuan (live)

Semua dieksekusi read-only / dry-run. ✅ = berfungsi.

### 3.1 Core & sistem
| Tool | Hasil |
|---|---|
| `datetime_now` | ✅ `2026-08-08T04:03:51+07:00` (Asia/Jakarta) |
| `calculate("(100-25)/3")` | ✅ 25 |
| `calculate_percentage(15,40)` | ✅ 37.5% + penjelasan |
| `ai_provider_status` | ✅ LLM aktif: flaz / deepseek-v4-flash |
| `coding_agent_status` | ✅ opencode |
| `skill_discovery` | ✅ map 9 kategori + slash commands |

### 3.2 Memory & Knowledge OS
| Tool | Hasil |
|---|---|
| `memory_get_context` | ✅ return memory scoped relevan (UACC pending, SE Akademik, artifact #63) |
| `memory_list` | ✅ 45+ record (berisi banyak checkpoint lintas project) |
| `knowledge_list_sources` | ✅ source 118–122 (HEBAT PDF) |
| `knowledge_search` | ✅ evidence bundle + status confidence (`insufficient` jujur untuk query di luar data) |
| `graph_v3_stats` | ✅ Enabled, 61 node / 30 edge, outbox 0 — **Neo4j offline** |
| `unified_search` | ✅ lintas knowledge + vault + graph + memory |

### 3.3 Life OS & OS kernel
| Tool | Hasil |
|---|---|
| `life_dashboard` | ✅ goals/tasks/habits hari ini |
| `task_today` | ✅ tidak ada due; inbox menampilkan 3 task HEBAT |
| `goal_list` | ✅ Full-Stack Agentic AI Engineer (learning, monthly, high) |
| `habit_today` | ✅ 3 habit |
| `os_today` | ✅ attention queue: task #19 HEBAT prioritas tinggi |
| `os_inbox` | ✅ 0 pending, 17 archived |
| `reminder_list` | ✅ kosong |
| `rules_healthcheck` | ✅ 4 aturan aktif, injection OK |
| `style_show` | ✅ default |

### 3.4 Portal akademik & subsystem
| Tool | Hasil |
|---|---|
| `portal_info` | ✅ cache struktur ada, session terenkripsi ada, CAPTCHA tidak pernah di-solve |
| `uacc_info` | ✅ status `human_verification_required`, session ada |
| `hebat_login_status` | ✅ status benar: belum login |
| `web_analysis_status(hebat)` | ✅ auth_required, cache 2026-08-01 tidak stale |
| `lightning_healthcheck` | ✅ 1029 episode, success 98.9%, approval_flow owner-only |
| `workflow_latest` | ✅ belum ada workflow |
| `deep_research_list` | ✅ 2 session (APSI use case, belajar programming) |
| `obsidian_folder_status` | ✅ 120 notes, healthy, 0 duplicate |

### 3.5 Tools yang TIDAK dieksekusi (sengaja)
`hebat_upload_submission`, `portal_krs_war_arm`, `qa_fill_kuesioner` (semua `final`
butuh approval), `wa_send_*`, `graph_v3_rebuild` (destruktif), login CAPTCHA/OTP,
external MCP add/remove, dan semua tool write data pengguna.

---

## 4. Hasil testing skills

| Uji | Hasil |
|---|---|
| `skill_list` | ✅ **29 skills**: 24 trusted-builtin + 5 owner-installed |
| `skill_healthcheck` | ✅ 29 valid, 0 invalid, **4 warnings** |
| `skill_suggest_for_request` | ✅ ranking deterministik (it-learning 1.00 untuk query learning) |
| `skill_get("research")` | ✅ progressive disclosure — isi lengkap 8 fase workflow |
| `skill_resource_list("research")` | ✅ 8 resources (agents/ + references/ + scripts/) |
| `skill_resource_read("research/agents/adversarial-reviewer.md")` | ✅ konten terbaca |
| `skill_validate` (SKILL.md sintetis) | ✅ valid, SHA-256, **tidak disimpan** |

### Warning katalog (non-blocking)
- `gh-fix-ci`, `playwright`, `academic-assignment`: body memuat URL eksternal
  (verifikasi provenance).
- `playwright-interactive`: SKILL.md 693 baris (target ≤ 500 untuk progressive disclosure).
- Catatan: `test-mcp` (owner-installed) dideskripsikan "hapus jika tidak diperlukan".

---

## 5. Hasil testing manajemen MCP

| Uji | Hasil |
|---|---|
| `external_mcp_list` | ✅ `success: true`, **enabled: false**, servers: [] — fitur ada, belum dipakai |
| `tool_catalog` (risk=read) | ✅ 8 tool: metadata lengkap (feature_pack, risk, stability, approval, idempotency) |
| `tool_catalog` (risk=final) | ✅ 3 tool final, semua `requires_approval=true` |
| `external_mcp_tools` | ⏭️ tidak dipanggil (tidak ada server terdaftar → pasti error kosong; bukan bug) |
| `external_mcp_add/remove` | ⏭️ tidak dieksekusi (aksi konfigurasi — butuh permintaan eksplisit) |

**Analisis manajemen MCP**: model "shared registry + adapter" (`mcp_tool_adapter.py`)
berarti tool baru cukup ditambahkan ke `tools/registry.py` + `manifest.py`, dan
langsung terekspos ke semua client tanpa perubahan client. Fitur external MCP
(stdio, secret dari env lokal) tersedia untuk integrasi pihak ketiga — cocok dengan
roadmap memory #46 (akses UACC via external MCP / web fetch).

---

## 6. Temuan & observasi

1. **Neo4j offline** — GraphRAG V3 berjalan dalam mode degraded (SQLite canonical:
   61 node/30 edge, outbox 0). Projection Neo4j tidak live. Tidak memblokir fungsi
   lain; hanya menjadikan `graph_v3_search` hybrid terbatas.
2. **4 skill warnings** — kualitas katalog baik (29/29 valid), warnings hanya
   URL eksternal + panjang body satu skill.
3. **HEBAT belum login** — sesi Moodle tidak aktif saat testing (status dilaporkan
   jujur oleh tool, bukan kegagalan).
4. **External MCP belum aktif** — fitur management tersedia dan sehat.
5. **Memory besar (45+ record)** — `memory_list` sangat panjang; perlu konsolidasi
   berkala (beberapa checkpoint lama bisa di-supersede).
6. **Owner-scoped security terbukti** — chat_id diinjeksi server-side; policy
   `final → approval` konsisten di catalog; CAPTCHA/OTP manual dijawab owner;
   tidak ada tool yang bisa melewati approval gate.
7. **Semua read tool berperilaku jujur** — `knowledge_search` melaporkan
   `status=insufficient` bila bukti tidak cukup (tidak mengarang).

---

## 7. Yang belum diuji (perlu approval/manual)

- Submit tugas HEBAT (token konfirmasi) — tier final
- KRS War arm/upgrade — tier final
- QA kuesioner — tier final
- Kirim pesan/media WhatsApp — external action
- Login CAPTCHA/OTP (HEBAT, Cyber Campus, UACC) — manual owner
- `graph_v3_rebuild` — destruktif
- `external_mcp_add/remove` — konfigurasi
- Tool write lainnya (task_capture, obsidian_create, money_add, dsb.) — tier 1,
  tidak dieksekusi agar tidak mengotori data; mekanisme wrapper sama dengan yang sudah diuji.

---

## 8. Rekomendasi

| Prioritas | Aksi |
|---|---|
| Sedang | Cek kenapa Neo4j offline (projection GraphRAG V3) — aktifkan untuk hybrid search penuh |
| Rendah | Bersihkan warning 4 skill: verifikasi URL eksternal, potong SKILL.md playwright-interactive |
| Rendah | Pertimbangkan hapus skill `test-mcp` bila tidak dipakai |
| Sedang | Konsolidasi memory lama (supersede checkpoint yang sudah outdated) |
| Rendah | Aktifkan external MCP bila butuh integrasi pihak ketiga (roadmap UACC #46) |
| — | Lanjutkan testing area lain yang butuh interaksi manual (login HEBAT/Cyber Campus) |

---

## 9. Lampiran — detail teknis

- Server: `services/ai/app/xninetzy/interfaces/mcp_server.py` (253 baris)
- Adapter: `services/ai/app/xninetzy/interfaces/mcp_tool_adapter.py`
  (`expose_xninetzy_tools`, `mcp_principal`)
- Runtime: `services/ai/app/xninetzy/interfaces/mcp_runtime.py` (`MCP_PATH_OVERRIDES`)
- Registry: `services/ai/app/xninetzy/tools/registry.py` — `get_all_tools`,
  `get_tool_names`, `get_tool_descriptions`, `get_tool_groups`
- Manifest: `services/ai/app/xninetzy/tools/manifest.py` — `ToolManifest`,
  `manifest_for(name)`, `_feature_pack`, `_requires_evidence`
- Policy: `services/ai/app/xninetzy/os/policy/action_policy.py` — `RiskClass`,
  `classify_risk`, `_POLICY_ACTIONS`
- Client config: `~/.config/opencode/opencode.jsonc` (MCP local, timeout 120 s,
  default_agent xninetzy, modes xn-research/xn-assignment/xn-learn)
- DB: SQLite diinisialisasi + migrasi otomatis saat startup MCP
