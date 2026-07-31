# Xninetzy MCP — V1 Production Open-Source Roadmap

**Tujuan:** Transformasi Xninetzy dari internal tool (READY FOR INTERNAL USE) menjadi production-grade open-source MCP server yang bisa diinstal siapa pun, dengan dokumentasi lengkap, error handling solid, dan pengalaman developer first-class.

**Basis data:** MCP usability review (154 tools, 54 executed), gap analysis, dokumentasi internal.
**Target V1 rilis:** Q1 2027 (3-4 bulan).

---

## V1 Definition of Done

Sebuah MCP server disebut **V1 Production Ready** jika:

1. ✅ Semua tool punya **stable contract** (nama, input, output tidak berubah antar rilis)
2. ✅ Semua tool return **structured error** yang actionable
3. ✅ Semua mutasi punya **idempotency key**
4. ✅ Semua output aman (tidak bocorkan JID, token, path internal)
5. ✅ **Knowledge synthesis** berfungsi dengan benar
6. ✅ **Web search** dan **YouTube search** jalan tanpa API key berbayar
7. ✅ Dokumentasi onboarding + contribution guide lengkap
8. ✅ Minimal 80% test coverage untuk domain kritis
9. ✅ CI/CD hijau (lint → typecheck → test → build)
10. ✅ Tidak ada `TODO`, `FIXME`, atau `# type: ignore` tanpa alasan

---

## Milestone V1

### Milestone 1: Foundation Fixes (Minggu 1-2)

**Goal:** Semua bug kritis dan blocking issue dari MCP review diperbaiki.

#### 1.1 Fix knowledge_answer synthesis

**Akar masalah (dari MCP review):** Tool `knowledge_answer` selalu return "Sintesis model sedang tidak tersedia" untuk semua query, meskipun evidence tersedia di knowledge base.

**Checklist:**
- [ ] Debug synthesis pipeline: retrieval → context building → LLM call → format
- [ ] Pastikan LLM call untuk synthesis menggunakan model yang benar (bukan flash)
- [ ] Fallback ke `knowledge_search` + template jika synthesis LLM gagal
- [ ] Tambah confidence scoring di output synthesis
- [ ] Test dengan berbagai jenis query: spesifik, broad, multi-bahasa

**Dependencies:** `os/knowledge/rag.py`, `os/knowledge/embeddings.py`
**Test coverage target:** 90%

#### 1.2 Redact sensitive identifiers dari output

**Akar masalah (dari MCP review):** `os_job_status` menampilkan `Target: 6285649204151@s.whatsapp.net` — JID WhatsApp penuh.

**Checklist:**
- [ ] Audit semua tool output untuk JID, cookie, token, path absolut
- [ ] Implementasikan masking layer di `core/security.py` (sudah disebut di WA_AI_SECOND_BRAIN_AUDIT.md sebagai usulan)
- [ ] Replace `sender_id`, `chat_id`, `Target` dengan label aman
- [ ] Test: tidak ada JID/credential muncul di output tool manapun

**Dependencies:** `interfaces/` — semua tool yang punya output WhatsApp metadata
**Test coverage target:** 100% (regex audit + integration test)

#### 1.3 Tambah idempotency key untuk semua mutasi

**Akar masalah (dari MCP review):** `graph_add_node`, `knowledge_ingest_text`, `os_capture`, `task_capture`, dan tool mutasi lain tidak punya idempotency key — retry bikin data duplikat.

**Checklist:**
- [ ] Audit semua tool mutasi (lihat tabel di review — ~100 tools)
- [ ] Tambah `idempotency_key: str = ""` sebagai optional field
- [ ] Implementasi idempotency store (hash → existing_result)
- [ ] Update dokumentasi untuk tiap tool yang sekarang idempotent
- [ ] Test: call yang sama 2x → result sama, data tidak duplikat

**Dependencies:** `db/sqlite.py` (table baru `idempotency_keys`)
**Test coverage target:** 100% untuk setiap tool mutasi

#### 1.4 Consistent error format

**Akar masalah (dari MCP review):** Mix of Indonesian and English errors. Ada error yang return "Something went wrong", ada yang return Python traceback.

**Checklist:**
- [ ] Definisikan error contract: `{"error": true, "code": "TOOL_NOT_FOUND", "message": "Task ID 99999 tidak ditemukan", "valid_values": null}`
- [ ] Implementasi error formatter di `tools/` base class
- [ ] Pastikan semua tool return error dalam format yang sama
- [ ] Bedakan: invalid_input vs not_found vs not_configured vs server_error
- [ ] Test: setiap tool error case return format yang benar

**Dependencies:** `tools/` — semua tools
**Test coverage target:** 80% (setiap tool punya error test)

---

### Milestone 2: Search & Research Hidup (Minggu 3-4)

**Goal:** Web search dan YouTube search berfungsi tanpa API key berbayar. Academic paper search menjadi capability baru.

#### 2.1 Integrasi DuckDuckGo web search (gratis)

**Akar masalah (dari MCP review):** `web_search` dan `research_web_collect` return "not active" karena butuh TAVILY_API_KEY/SERPER_API_KEY.

**Solusi:**
Ganti backend search dengan DuckDuckGo (gratis, tanpa API key). Bisa via library `duckduckgo_search` atau via MCP `web_search` server.

**Checklist:**
- [ ] Pilih implementation: library langsung (`duckduckgo_search` Python) vs MCP client
- [ ] Implementasi `WebSearchService` di `os/research/` dengan fallback engine
- [ ] Update `web_search` tool description: hapus mention TAVILY_API_KEY
- [ ] Tambah content fetching (fetchWebContent equivalent)
- [ ] Test: search berbagai query (EN, ID, teknis, umum)
- [ ] Test: edge case (empty query, special chars, rate limit)

**Dependencies:** `os/research/`, `tools/ecosystem/research_tools.py`
**Test coverage target:** 85%

#### 2.2 Integrasi yt-dlp YouTube search (gratis)

**Akar masalah (dari MCP review):** `youtube_search` dan `youtube_learning_search` return "not active" karena butuh YOUTUBE_API_KEY.

**Solusi:**
Ganti backend dengan yt-dlp (gratis, tanpa API key). yt-dlp sudah terbukti stabil di `youtube_search` MCP server yang saya gunakan selama review.

**Checklist:**
- [ ] Tambah dependency `yt-dlp` (Python package, sudah mature)
- [ ] Implementasi `YouTubeService` di `os/research/`
- [ ] Dukung: search video, get metadata, download transcript
- [ ] Update `youtube_search` dan `youtube_learning_search`
- [ ] Tambah tool baru: `youtube_get_transcript(url)` — ambil teks video
- [ ] Test: search, metadata, transcript untuk berbagai video
- [ ] Test: error handling (video private, not found, region block)

**Dependencies:** `os/research/`, `tools/ecosystem/research_tools.py`
**Test coverage target:** 80%

#### 2.3 Academic paper search (capability baru)

**Akar masalah (dari MCP review):** Xninetzy tidak punya akses ke sumber akademik manapun. Paper search adalah capability yang completely missing.

**Checklist:**
- [ ] Implementasi paper search via arXiv API (free, no key)
- [ ] Implementasi paper search via CrossRef API (free, no key)
- [ ] Tool: `research_search_papers(query, sources, max_results)`
- [ ] Tool: `research_get_paper(identifier, source)` — DOI, arXiv ID, PMID
- [ ] Tool: `research_download_paper(identifier, save_path)` — dengan fallback Sci-Hub
- [ ] Integrasikan hasil ke knowledge base: search paper → ingest langsung
- [ ] Update research brief generator untuk include paper sources

**Dependencies:** `os/research/`, `os/knowledge/ingestion.py`
**Test coverage target:** 75%

#### 2.4 Research pipeline end-to-end functional

**Checklist:**
- [ ] Reset: `research_light(query)` → web search + youtube + paper → ringkas
- [ ] Reset: `research_generate_brief(topic)` → subplan → search → brief dengan sumber nyata
- [ ] Reset: `deep_research_topic(topic)` — admin only, dengan session, sumber terverifikasi
- [ ] Output: setiap hasil research menyertakan sumber (title, URL, timestamp)
- [ ] Test: pipeline lengkap dari topic → search → brief → save

**Dependencies:** Semua tools di Milestone 2.1-2.3
**Test coverage target:** 70%

---

### Milestone 3: Open Source Readiness (Minggu 5-6)

**Goal:** Developer lain bisa clone, configure 1 file `.env`, run `npm install && npm start`, dan MCP server langsung jalan.

#### 3.1 Dokumentasi onboarding

**Checklist:**
- [ ] `README.md` — one-paragraph what is this, quick start (3 langkah), screenshot
- [ ] `docs/GETTING_STARTED.md` — instalasi lengkap (prerequisites, clone, install, configure, run, verify)
- [ ] `docs/CONFIGURATION.md` — semua env vars, dengan contoh nilai default
- [ ] `docs/ARCHITECTURE.md` — high-level architecture (satu diagram Mermaid cukup)
- [ ] `docs/MCP_TOOLS.md` — tabel semua tools, deskripsi, contoh input/output
- [ ] `docs/DEVELOPMENT.md` — cara run test, coding conventions, PR流程
- [ ] `CONTRIBUTING.md` — contribution guidelines, code of conduct
- [ ] `LICENSE` — pilih open source license (MIT recommended untuk MCP tools)

**Target:** Developer bisa `uv run xninetzy` dalam < 5 menit.

#### 3.2 Environment & configuration hardening

**Checklist:**
- [ ] `.env.example` — semua variable dengan komentar, tanpa secrets
- [ ] Validasi env vars di startup: required vs optional, format checking
- [ ] Default values yang aman untuk development
- [ ] Dokumentasi API key: mana yang required, mana yang optional, mana yang gratis
- [ ] `docker-compose.yml` — one-command startup (AI service + WA engine + MCP server)
- [ ] Dockerfile optimal (multi-stage, small image)

#### 3.3 Test infrastructure

**Checklist:**
- [ ] CI/CD pipeline: GitHub Actions (lint → typecheck → test → build)
- [ ] Unit test: minimal 80% coverage untuk `os/` dan `domains/it_learning/`
- [ ] Integration test: end-to-end workflow test (research → save → recall)
- [ ] MCP contract test: setiap tool dipanggil dengan valid/invalid input → assert error format
- [ ] Snapshot test: output tool tidak berubah tanpa sengaja
- [ ] Test dengan SQLite in-memory (bukan produksi)

**Commands yang harus hijau di CI:**
```bash
uv run ruff check app tests
uv run pytest --cov=app --cov-fail-under=80
uv run mypy app --strict
```

#### 3.4 Code quality baseline

**Checklist:**
- [ ] `ruff` linting dengan konfigurasi ketat
- [ ] `mypy --strict` untuk semua kode baru
- [ ] Hapus semua `# type: ignore` tanpa komentar
- [ ] Hapus semua `TODO` dan `FIXME` (buat GitHub Issues sebagai gantinya)
- [ ] Type hints untuk semua fungsi publik
- [ ] Docstrings untuk semua tools (LLM-readable — ini critical untuk MCP)

#### 3.5 Semantic versioning & changelog

**Checklist:**
- [ ] `pyproject.toml` dengan version field
- [ ] `CHANGELOG.md` mengikuti Keep a Changelog
- [ ] GitHub Release workflow otomatis (tag → build → publish)
- [ ] Package di PyPI? Optional, tapi ideal untuk `pip install xninetzy-mcp`

---

### Milestone 4: Production Hardening (Minggu 7-8)

**Goal:** MCP server stabil di production dengan monitoring, security, dan performance yang acceptable.

#### 4.1 Tool output standardization

**Akar masalah (dari MCP review):** Output format campur aduk — ada yang JSON array (`obsidian_list`), ada yang WhatsApp Markdown (`os_today`), ada yang campuran (`knowledge_search` return evidence blocks).

**Checklist:**
- [ ] Definisikan dual output: JSON untuk MCP consumption, Markdown untuk WhatsApp display
- [ ] Implementasi `format_for_mcp()` → structured dict
- [ ] Implementasi `format_for_whatsapp()` → WhatsApp-compatible markdown
- [ ] Semua tool panggil keduanya; MCP client dapet JSON, WhatsApp dapet Markdown
- [ ] Tool description menjelaskan output format dengan jelas
- [ ] Test: setiap tool return valid JSON ketika dipanggil via MCP

**Output contract:**
```python
# Standar output untuk MCP
{
    "status": "success" | "error",
    "data": { ... } | None,
    "error": { "code": str, "message": str, "details": ... } | None,
    "metadata": { "tool": str, "duration_ms": int, "source": str }
}
```

#### 4.2 Tool naming & description audit

**Akar masalah (dari MCP review):** Tool overlap tidak jelas (os_today vs task_today vs life_dashboard), deskripsi tidak menjelaskan kapan *tidak* boleh dipakai.

**Checklist:**
- [ ] Audit semua 154 tools untuk naming consistency
- [ ] Setiap tool description harus jawab:
  - What does this tool do? (1 kalimat)
  - When should you use this? (1-2 kalimat)
  - When should you NOT use this? (1 kalimat — **ini yang sering kurang**)
  - What side effects or confirmation needed? (jika ada)
- [ ] Domain prefix konsisten: `hebat_`, `learning_`, `portal_`, `graph_`, dll
- [ ] Bedakan read vs write secara eksplisit: `list_` vs `create_` vs `delete_`
- [ ] Hapus/gabung tool yang overlap (os_today vs task_today vs life_dashboard)
- [ ] Test: LLM prompt dengan tool list → hitung correct selection rate

#### 4.3 Security audit & hardening

**Checklist:**
- [ ] Audit semua tool untuk injection risk (SQL injection di identifier fields)
- [ ] Path traversal check di semua tool yang terima path/file fields
- [ ] Rate limiting per tool (terutama yang panggil API eksternal)
- [ ] Input size limits (query max length, limit max value)
- [ ] Output size limits (truncate large responses)
- [ ] SSRF protection untuk tool yang fetch URL
- [ ] Audit bahwa JID, token, cookie, password tidak pernah muncul di output

#### 4.4 Performance optimization

**Checklist:**
- [ ] Cache untuk frequent queries (knowledge_search, hebat_list_courses)
- [ ] Pagination untuk semua list tools (cursor-based, bukan offset-based)
- [ ] Lazy loading untuk FAISS index (jangan load di startup)
- [ ] Connection pooling untuk SQLite (WAL mode sudah aktif — good)
- [ ] Timeout untuk external API calls (web search, YouTube, paper search)
- [ ] Profile: temukan tool paling lambat → optimasi

**SLA target V1:**
- Discovery (tools/list): < 500ms
- Read-only tool (cached): < 1s
- Read-only tool (uncached): < 3s
- Search tool (knowledge/paper): < 5s
- Research pipeline: < 30s

#### 4.5 MCP specific hardening

**Checklist:**
- [ ] Expose server version via MCP metadata (`serverInfo.version`)
- [ ] Implement `resources/list` dan `resources/read` untuk data yang cocok (dashboard, status)
- [ ] Support `notifications/initialized` untuk client connection tracking
- [ ] Graceful shutdown handler (tutup DB, save state, terminate subprocess)
- [ ] Health check endpoint: `/health` → return status semua komponen

---

### Milestone 5: V1 Release (Minggu 9-10)

**Goal:** Tag `v1.0.0`, publish, dan dokumentasi publik.

#### 5.1 Release preparation

**Checklist:**
- [ ] Regression test: semua tool dari MCP review masih berfungsi
- [ ] Performance benchmark vs baseline (dari review)
- [ ] Dokumentasi final review
- [ ] `CHANGELOG.md` untuk v1.0.0
- [ ] `README.md` update dengan badge: CI, coverage, version, license
- [ ] Contoh penggunaan: `pip install xninetzy-mcp` atau `npx xninetzy-mcp`
- [ ] Video demo: 2 menit setup + run

#### 5.2 Post-release monitoring

**Checklist:**
- [ ] GitHub Issues template: bug report, feature request, question
- [ ] Discussion forum atau Discord link
- [ ] First 30 days: weekly triage for issues
- [ ] Roadmap publik untuk V2

---

## Ringkasan V1 Tool Changes

### Tools yang dihapus atau digabung

| Tool | Masalah | Solusi |
|---|---|---|
| `os_today` | Overlap dengan `task_today` + `life_dashboard` | Gabung → `os_dashboard` |
| `task_today` | Overlap dengan `os_today` | Hapus, ganti ke `os_dashboard` |
| `life_dashboard` | Overlap dengan `os_today` | Hapus, ganti ke `os_dashboard` |
| `research_light` | Name tidak jelas bedanya dengan `research_generate_brief` | Rename → `research_quick` |
| `helper_get` | Overlap dengan `skill_discovery` | Gabung → `helper_get` menjadi canonical |
| `calculate_percentage` | Bisa di-calculate | Hapus, `calculate` sudah cover |

### Tools baru di V1

| Tool | Domain | Deskripsi |
|---|---|---|
| `os_dashboard` | Core | Gabungan os_today + task_today + life_dashboard |
| `youtube_get_transcript` | Research | Ambil transcript video YouTube (yt-dlp) |
| `research_search_papers` | Research | Search academic papers (arXiv + CrossRef) |
| `research_get_paper` | Research | Get paper details by DOI/ID |
| `research_download_paper` | Research | Download paper PDF |
| `web_fetch_content` | Core | Fetch dan extract konten dari URL |
| `system_health` | Core | Comprehensive health check |
| `system_metrics` | Core | Usage metrics (calls, tokens, errors) |

### Tools yang diperbaiki di V1

| Tool | Perbaikan |
|---|---|
| `knowledge_answer` | Fix synthesis pipeline |
| `web_search` | Ganti backend DuckDuckGo |
| `youtube_search` | Ganti backend yt-dlp |
| `research_web_collect` | Ganti backend DuckDuckGo |
| `research_youtube_collect` | Ganti backend yt-dlp |
| `os_job_status` | Redact JID |
| Semua list tools | Tambah pagination + total_count |
| Semua mutasi tools | Tambah idempotency_key |

### Tools yang ditunda ke V2

| Tool | Alasan |
|---|---|
| `deep_research_topic` dengan RL | Butuh event system dulu |
| Closed-loop orchestrator | Butuh dependency graph dulu |
| Assignment intelligence pipeline | Butuh event system dulu |
| RL episode recorder | Butuh observability dulu |
| Automated improvement loop | Butuh RL dulu |
| Episodic memory | Butuh memory compression dulu |

---

## V1 Dependency Graph

```
Milestone 1 (Foundation)
├── Fix knowledge_answer
│     └── knowledge_search (existing, works)
├── Redact JID
│     └── core/security.py (new)
├── Idempotency keys
│     └── db/idempotency.py (new)
└── Error format
      └── tools/base.py (refactor)

Milestone 2 (Search)
├── DuckDuckGo search
│     ├── os/research/web_search.py (refactor)
│     └── web_search (existing MCP or library)
├── yt-dlp search
│     ├── os/research/youtube_search.py (refactor)
│     └── yt-dlp library (new dep)
└── Paper search
      ├── os/research/paper_search.py (new)
      └── arXiv + CrossRef API (new)

Milestone 3 (OSS)
├── Dokumentasi
│     ├── README.md (new)
│     ├── docs/ *.md (new)
│     └── CONTRIBUTING.md (new)
├── CI/CD
│     ├── .github/workflows/ (new)
│     └── pyproject.toml config
└── Tests
      ├── tests/unit/ (new)
      ├── tests/integration/ (new)
      └── tests/mcp_contract/ (new)

Milestone 4 (Production)
├── Output standard
│     └── tools/formatter.py (refactor)
├── Naming audit
│     └── tools/registry.py (refactor)
├── Security
│     ├── core/security.py (audit)
│     └── tools/validation.py (new)
└── Performance
      ├── core/cache.py (new)
      └── tools/pagination.py (new)
```

---

## Resources Required

### Engineering hours (estimasi)

| Milestone | Engineer-weeks | Parallelizable |
|---|---|---|
| M1: Foundation | 2-3 | Ya (task independen) |
| M2: Search | 2-3 | Ya (3 search services) |
| M3: OSS | 1-2 | Ya (docs ≠ code) |
| M4: Production | 2-3 | Partial |
| M5: Release | 1 | No |
| **Total** | **8-12** | **3-4 bulan calendar** |

### External dependencies (baru)

| Dependency | Untuk | License | Risk |
|---|---|---|---|
| `duckduckgo_search` | Web search | MIT | Low — mature |
| `yt-dlp` | YouTube search | Unlicense | Low — mature |
| `arxiv` | Paper search | MIT | Low |
| `httpx` | HTTP client (sudah ada?) | BSD | Low |

Tidak ada dependency berbayar. V1 = **zero paid API key required**.

---

## V1 Exit Criteria

V1 dinyatakan rilis jika DAN HANYA JIKA:

```
[ ] Semua tool di Milestone 1-2 berfungsi dan ter-test
[ ] CI/CD hijau untuk semua commit ke main
[ ] Test coverage ≥ 80%
[ ] Tidak ada secret/JID/token bocor di output
[ ] Developer baru bisa setup dalam < 5 menit (dengan timer)
[ ] `knowledge_answer(query)` return synthesized answer untuk query valid
[ ] `web_search(query)` return real results tanpa API key
[ ] Semua tool return structured JSON melalui MCP
[ ] Semua error return format yang konsisten
[ ] Dokumentasi V1 complete
[ ] Tag v1.0.0 dibuat
```

---

## File yang akan dibuat/dimodifikasi

### File baru
```
docs/GETTING_STARTED.md
docs/CONFIGURATION.md
docs/ARCHITECTURE.md
docs/MCP_TOOLS.md
docs/DEVELOPMENT.md
CONTRIBUTING.md
LICENSE
.github/workflows/ci.yml
.github/workflows/release.yml
tests/unit/test_knowledge_synthesis.py
tests/unit/test_web_search.py
tests/unit/test_youtube_search.py
tests/unit/test_paper_search.py
tests/unit/test_idempotency.py
tests/unit/test_security_redaction.py
tests/integration/test_research_pipeline.py
tests/mcp_contract/test_tool_contracts.py
app/xninetzy/core/security.py
app/xninetzy/core/cache.py
app/xninetzy/core/pagination.py
app/xninetzy/tools/formatter.py
app/xninetzy/tools/validation.py
app/xninetzy/db/idempotency.py
app/xninetzy/os/research/paper_search.py
```

### File dihapus
```
tools/legacy/* (isi adapter backward-compat lama)
app/planning/* (sudah migrasi ke os/life)
app/tools/hebat/* (sudah migrasi ke os/academic/hebat)
```

### File dimodifikasi
```
app/xninetzy/tools/registry.py — hapus/gabung tool, tambah tool baru
app/xninetzy/os/knowledge/rag.py — fix synthesis
app/xninetzy/os/research/web_search.py — ganti DuckDuckGo
app/xninetzy/os/research/youtube_search.py — ganti yt-dlp
app/xninetzy/os/life/dashboard.py — gabung os_today + task_today
app/xninetzy/interfaces/mcp_server.py — tambah serverInfo.version
app/xninetzy/core/config.py — tambah env vars baru
README.md — rewrite total
pyproject.toml — tambah dependencies, version
```

---

## Catatan dari MCP Review

**Yang sudah benar dan harus dipertahankan:**
1. Domain-prefixed tool names (`hebat_`, `learning_`, `portal_`, `graph_`) — ini membantu LLM selection
2. Zero `additionalProperties: true` — input validation strict
3. Tidak ada stack trace di output error — aman
4. Idempotent daily note creation — `obsidian_daily` return error untuk overwrite
5. HITL approval untuk aksi berisiko — pattern yang benar
6. try/except di semua internal tools — tidak crash server

**Yang paling critical untuk V1:**
1. `knowledge_answer` broken → ini tool #1 untuk "Learning OS" value proposition
2. Search tidak aktif → whole research pipeline mati
3. Output format campur aduk → agent harus parse manual, workflow terhambat
4. JID kebocoran → security issue
5. Tidak ada idempotency key → retry tidak aman
6. Dokumentasi developer nihil → open source impossible

---

## Lampiran: Perbandingan Sebelum-Sesudah V1

| Aspek | Sebelum V1 | Sesudah V1 |
|---|---|---|
| Web search | ❌ Tidak aktif (butuh API key) | ✅ DuckDuckGo gratis |
| YouTube search | ❌ Tidak aktif (butuh API key) | ✅ yt-dlp gratis |
| Paper search | ❌ Tidak ada | ✅ arXiv + CrossRef |
| Knowledge synthesis | ❌ Broken | ✅ Bekerja |
| Output format | Campur aduk | ✅ JSON standard |
| Error format | Tidak konsisten | ✅ Standard contract |
| Idempotency | ❌ Tidak ada | ✅ Semua mutasi |
| JID leak | ❌ Bocor | ✅ Redacted |
| Dokumentasi | ❌ Internal only | ✅ Public OSS |
| Test coverage | Partial | ✅ ≥ 80% |
| CI/CD | ❌ Tidak ada | ✅ GitHub Actions |
| Setup time | 30+ menit | ✅ < 5 menit |
| API key required | Tavily + Serper + YouTube | ✅ Zero |

---

*Dokumen ini berdasarkan MCP usability review (30 Juli 2026, 154 tools tested) dan gap analysis. Target V1: Q1 2027.*
