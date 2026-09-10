# Analisis Lengkap Pengujian & Perbaikan Tools Xninetzy

*Tanggal: 2026-08-02*

Ringkasan eksekutif: Dokumen ini merupakan **satu dokumen analisis lengkap** yang menggabungkan seluruh isi bug report sesi 2026-07-30 (B1–B11, §2) dengan analisis pengujian dan perbaikan tools. Sesi ini bertujuan (1) menjalankan verifikasi final kualitas kode dan seluruh suite pengujian Xninetzy, serta (2) mendokumentasikan status perbaikan bug tools dari laporan sesi 2026-07-30 (B1–B11) beserta temuan perilaku kode. Hasil utama: full test suite **630 passed / 0 failed / 0 skipped** (durasi 336,87 detik / 5 menit 37 detik), `ruff check app tests` bersih (**All checks passed!**), **66 test baru** ditambahkan dalam 8 file test baru, dan **17 tool Xninetzy di-smoke-test live** via MCP (semua read-only, semuanya berhasil). Tidak ada commit/push yang dilakukan pada sesi ini.

## 1. Latar Belakang

- **Bug report sesi 2026-07-30** awalnya didokumentasikan sebagai file terpisah di `docs/plan/TOOL_BUG_REPORT_SESI_20260730.md`: berisi 11 temuan (B1–B11) — 3 critical (B1–B3), 5 medium (B4–B8), 3 informational (B9–B11) — beserta prioritas perbaikan (P0–P3). Catatan: pada saat sesi ini berjalan, file tersebut **sudah terhapus dari working tree oleh proses lain** (tercatat `D` di `git status`; hanya `MCP_OPENSOURCE_V1_ROADMAP.md` yang tersisa di `docs/plan/`). Isi laporan dibaca ulang dari git index (`git show HEAD:docs/plan/TOOL_BUG_REPORT_SESI_20260730.md`, 224 baris) untuk akurasi, dan **seluruh kontennya kini digabung ke dokumen ini** pada §2 — bukan lagi dibaca via `git show`, melainkan bagian permanen dari dokumen analisis ini.
- **Catatan soal `docs/plan/bug.md`**: file tersebut tidak ada di git history maupun working tree. Yang ditemukan adalah `bug.md` di **root repo** (`/home/misbahul45/code/xninetzy/bug.md`, 99 baris) — yaitu *MCP Ecosystem Bug Report* tanggal 2026-07-28 yang berisi isu permission: SQLite read-only (WAL lock contention), folder vault & data yang root-owned (`.backup`, `vector`, `wa-media`, `web-analysis`), dan root-cause permission mismatch (MCP server jalan sebagai `misbahul45` tapi direktori dimiliki `root`). Dokumen tersebut sudah diverifikasi teratasi pada 2026-07-28 (Docker AI memakai UID/GID host).
- **Analisis timeout Graph RAG** tidak ditemukan sebagai dokumen, sehingga diverifikasi langsung dari kode (`neo4j_lifecycle.py`, `neo4j_store.py`, `config.py`):
  - `ensure_running()` (neo4j_lifecycle.py:102–167) menjalankan `docker compose up -d neo4j` secara **sinkron** lewat `subprocess.run` (command timeout default 8 detik; `NEO4J_AUTOSTART_COMMAND_TIMEOUT_SECONDS = 8.0`, config.py:378), lalu **polling** ketersediaan bolt (`_bolt_ready`, socket timeout 1,0 dtk) tiap 0,25 dtk sampai deadline `min(BOOT_TIMEOUT 60s, READINESS_TIMEOUT 10s) = 10 dtk` default (config.py:376–377).
  - Setelah itu `neo4j_store.get_driver()` membuat driver dengan `connection_timeout = max(0.5, 3.0) = 3 dtk` (config.py:379) lalu memanggil `driver.verify_connectivity()` **tanpa timeout eksplisit** (neo4j_store.py:130).
  - Tidak ada latch persistent lintas proses; hanya ada `_boot_lock` (threading.Lock in-process, neo4j_lifecycle.py:120) dan *boot-failure cooldown* (`_mark_boot_failure`). Karena MCP stdio bersifat sekuensial per request, saat docker belum siap (mis. pull image lambat) satu panggilan graph tool dapat memblokir seluruh sesi stdio sehingga tool berbasis SQLite ikut terasa timeout. Sifatnya **intermittent**: setelah container up, panggilan berikutnya cepat.
  - Hingga sesi ini **belum ada penanganan khusus di kode** untuk masalah tersebut (hanya hardening cooldown yang sudah ada); isu ini tidak tercantum sebagai bug di laporan B1–B11.
  - Keterangan: klaim "polling 60s + verify_connectivity 30s" pada draf awal tidak persis cocok dengan kode — polling efektif default 10 dtk (min dari 60 dtk boot timeout dan 10 dtk readiness timeout), dan `verify_connectivity()` tidak diberi timeout eksplisit (angka 30 dtk di kode hanya untuk `subprocess timeout` pada `stop()`, neo4j_lifecycle.py:180). Angka yang dipakai di dokumen ini adalah hasil verifikasi kode.

## 2. Bug Report Lengkap — Sesi 2026-07-30

*Berikut salinan lengkap bug report sesi 2026-07-30 (semua 11 temuan B1–B11, tabel prioritas, dan detail pendukung dipertahankan apa adanya; level heading disesuaikan agar menjadi sub-bagian dari dokumen ini).*

### Tool Bug Report — Sesi Deep Research & Implementasi 2026-07-30
#### Analisis Bug dari Sesi: Feynman Technique, Learning Techniques, Vault Integration

**Tester:** Misbahul (via OpenCode MCP)  
**Tanggal:** 30 Juli 2026  
**Durasi Sesi:** ~2 jam (research + implementation)  
**Tools Dipakai:** ~20 tool calls (xninetzy MCP + web_search + paper_research + filesystem)

---

#### Ringkasan

| Severitas | Jumlah | Deskripsi |
|---|---|---|
| 🔴 Critical | 3 | Tool gagal total atau data hilang |
| 🟡 Medium | 5 | Tool bekerja tapi hasil tidak akurat/terbatas |
| 🔵 Info | 3 | UX buruk, confusing, atau missing feature |

---

#### 🔴 Critical Bugs

##### B1. `knowledge_ingest_file` hanya support PDF — markdown gagal total

**File:** `services/ai/app/xninetzy/tools/ecosystem/knowledge_tools.py:46-81`  
**Lokasi kode:** `ingestion.py:108-147` — fungsi `ingest_pdf()`

**Apa yang terjadi:**  
Saat dipanggil `knowledge_ingest_file(file_path="...md")`, return error: `Could not extract text from PDF`.

**Root cause:**  
`knowledge_ingest_file()` hardcoded manggil `ingest_pdf()`, yang internally panggil `read_pdf_text()`. Tidak ada branch untuk `.md`, `.txt`, `.json`, `.csv`.

**Dampak:**  
Tidak bisa ingest file .md ke knowledge base. Harus copy-paste manual pake `knowledge_ingest_text`.

**Saran:**
- Auto-detect extension: `.md` / `.txt` → `ingest_text(baca_file)`, `.pdf` → `ingest_pdf()`
- Atau tambah parameter `file_type` biar eksplisit

---

##### B2. `obsidian_search` pakai substring linear scan — O(n) full vault read

**File:** `services/ai/app/xninetzy/os/notes/vault_service.py:43-59`

**Apa yang terjadi:**  
Pencarian multi-word sering return kosong meskipun isi note mengandung kata-kata itu.

**Root cause:**  
```python
for item in self.list_files():      # loop ALL files
    content = self.read_note(path)   # read EACH file fully
    if needle in haystack:           # simple Python substring match
```
1. Tidak ada FTS (Full-Text Search)
2. Scan linear semua file — O(n) per search
3. Multi-word query harus match eksak substring
4. Tidak ada caching/index

**Dampak:**  
Search lambat, sering miss untuk multi-word query, tidak scale.

**Saran:**
- Implementasi FTS5 SQLite
- Split query jadi individual keywords (AND logic)
- Cache isi file

---

##### B3. `graph_search` pake SQL `LIKE %query%` — search kaku

**File:** `services/ai/app/xninetzy/os/graph/graph_store.py`

**Apa yang terjadi:**  
Search "learning techniques" tidak menemukan node dengan judul "Evidence-Based Learning Techniques untuk Xninetzy".

**Root cause:**  
`SELECT * FROM graph_nodes WHERE title LIKE ?` — case sensitive by default. Juga tidak ada semantic search atau FTS.

**Dampak:**  
Graph RAG tidak bisa menemukan node relevan kalau wording berbeda.

**Saran:**
- Tambah FTS5 di `graph_nodes`
- Fix collation: `LIKE ? COLLATE NOCASE`
- Inject embeddings untuk semantic search

---

#### 🟡 Medium Bugs

##### B4. `obsidian_read` tidak punya offset/limit — truncate hard di 3000 chars

**File:** `services/ai/app/xninetzy/tools/internal/obsidian.py:122-133`

**Apa yang terjadi:**  
Tool `obsidian_read(path)` cuma menerima `path`, bukan `offset`/`limit`. Isi file dipotong paksa di 3000 karakter.

```python
def obsidian_read(path: str) -> str:
    content = _vault().read_note(path)
    return f"*{path}*\n\n{content[:3000]}"   # hard truncate
```

**Dampak:**  
File >3000 chars tidak terbaca penuh lewat tool ini.

**Saran:**
- Tambah parameter `offset` dan `limit` ke tool adapter

---

##### B5. Web search (`web_search_search` / DuckDuckGo) sering return 0 results

**Tool:** `web_search_search` (MCP server `web_search`)  

**Apa yang terjadi:**  
3 queries pertama semuanya return `{ totalResults: 0, results: [] }`. Harus switch ke `websearch` tool alternatif.

**Root cause:**  
Tidak jelas — kemungkinan rate limiting DuckDuckGo, atau bug di package, atau query terlalu panjang.

**Dampak:**  
Tool web search tidak reliable.

**Saran:**
- Tambah retry mechanism
- Fallback engine (DuckDuckGo → Bing → Startpage)
- Logging: bedakan "0 results karena query" vs "karena error"

---

##### B6. `obsidian_create` vs `obsidian_save_note` — duplikasi dengan perilaku berbeda

**File:** `services/ai/app/xninetzy/tools/internal/obsidian.py:137-198`

| Aspek | `obsidian_create` | `obsidian_save_note` |
|---|---|---|
| Path | path relatif langsung | folder + title (digabung) |
| Overwrite | `overwrite=False` (hardcoded) | `overwrite=False`, fallback timestamp |
| Gagal | Return error | Auto-timestamp (ubah path!) |

**Dampak:**  
Inconsistent behavior. User bisa kira file berhasil di path diminta, tapi ternyata di path berbeda.

**Saran:**
- Tambah parameter `overwrite` ke `obsidian_create`
- Perjelas return path real yang dipakai

---

##### B7. `obsidian_update_section` heading matching terlalu strict

**File:** `services/ai/app/xninetzy/os/notes/markdown_service.py` (via `vault_service.py:110-141`)

**Apa yang terjadi:**  
Whitespace ekstra di heading (`##  Title` vs `## Title`) bisa bikin gagal match atau duplicate section.

**Dampak:**  
Potensi duplicate sections atau silent failure.

**Saran:**
- Trim whitespace heading sebelum match
- Fallback: append kalau heading tidak ditemukan

---

##### B8. Paper research tools return null abstracts

**Tool:** `paper_research_search_semantic`  
**Test:** 5 papers, semua `"abstract": null`

**Dampak:**  
Sulit menilai relevansi paper tanpa abstrak. Harus download dulu.

**Saran:**
- Fallback ke source lain (Crossref, OpenAlex) kalau abstract null

---

#### 🔵 Informational / UX Issues

##### B9. Dua tool search: `obsidian_search` (vault) vs `graph_search` (graph RAG)

Tidak ada unified search yang cover vault + graph + knowledge + memory.

**Saran:**  
Unified search tool.

##### B10. Tool naming inconsistency

Beberapa pake prefix domain (`obsidian_*`, `knowledge_*`, `graph_*`), beberapa tidak (`calculate`, `datetime_now`).

**Saran:**  
Sudah cukup bagus — cukup info.

##### B11. Legacy code duplikasi

- `services/ai/app/xninetzy/os/notes/vault_service.py` (primary) vs `services/ai/app/obsidian/vault_service.py` (legacy)
- `services/ai/app/xninetzy/os/graph/graph_tools.py` (primary) vs `services/ai/app/graph_rag/graph_tools.py` (legacy)

**Saran:**  
Hapus file legacy setelah diverifikasi tidak ada import yang merujuk.

---

#### Prioritas Perbaikan

| Priority | Bug | Effort | Impact |
|---|---|---|---|
| P0 | B1 — knowledge_ingest_file hanya PDF | 1-2 jam | 🔴 Blocker |
| P0 | B2 — obsidian_search linear scan + no FTS | 4-8 jam | 🟡 Tidak scale |
| P1 | B3 — graph_search LIKE-only | 2-4 jam | 🟡 Graph RAG kurang berguna |
| P1 | B4 — obsidian_read no offset/limit | 1 jam | 🟡 File besar tidak terbaca |
| P1 | B5 — web_search DuckDuckGo 0 results | 2-4 jam | 🟡 Search tidak reliable |
| P2 | B6 — obsidian_create vs save_note duplikasi | 1 jam | 🔵 UX confusing |
| P2 | B7 — update_section strict heading | 1 jam | 🔵 Edge case |
| P2 | B8 — null abstracts | 2 jam | 🔵 Utility kurang |
| P3 | B9-B11 — naming, unified search, legacy | 4-8 jam | 🔵 Technical debt |

---

*Ditulis berdasarkan pengalaman langsung menggunakan tools Xninetzy MCP selama sesi deep research dan implementasi 30 Juli 2026.*

## 3. Status Implementasi Perbaikan Bug (B1–B11)

| Kode | Deskripsi | Status | Bukti/File |
|---|---|---|---|
| B1 | `knowledge_ingest_file` hanya support PDF | ✅ Diperbaiki | `tools/ecosystem/knowledge_tools.py:72–75` — routing `suffix`: `.pdf` → PDF, `{.md,.markdown,.txt,.json,.csv}` → text; diuji `test_knowledge_ingest_file_supports_markdown` |
| B2 | `obsidian_search` linear scan, multi-word miss | ✅ Diperbaiki | `os/notes/vault_service.py:45–46,56–65` — query di-split jadi keyword, match pakai `casefold()` per keyword (AND) |
| B3 | `graph_search` SQL `LIKE %q%` case-sensitive | ✅ Diperbaiki | `os/graph/graph_store.py:49` — `LIKE ? COLLATE NOCASE` pada title/content/node_type; `:56` klausa AND per keyword |
| B4 | `obsidian_read` tanpa offset/limit (truncate 3000) | ✅ Diperbaiki | `tools/internal/obsidian.py:123` — `obsidian_read(path, offset=0, limit=3000)` |
| B5 | `web_search_search` (DuckDuckGo) sering 0 results | ⛔ Di luar repo | Bug MCP eksternal (`web_search` server); tidak bisa diperbaiki dari repo ini |
| B6 | `obsidian_create` vs `obsidian_save_note` duplikasi perilaku | ✅ Diperbaiki | `tools/internal/obsidian.py:145` — `obsidian_create(path, content, overwrite=False)`; parameter `overwrite` tersedia |
| B7 | `obsidian_update_section` heading matching terlalu strict | ✅ Diperbaiki (sesi sebelumnya) | Tidak diubah pada sesi ini; status perbaikan dari sesi sebelumnya |
| B8 | Paper research tools return null abstracts | ⛔ Di luar repo | Bug MCP eksternal (`paper_research` server); tidak bisa diperbaiki dari repo ini |
| B9 | Tidak ada unified search (vault+graph+knowledge+memory) | ✅ Diperbaiki | File baru `tools/ecosystem/unified_search_tools.py`; terdaftar di `tools/registry.py:154` (import), `:450` (registrasi), `:632` (grup `unified_search`); **diverifikasi live** sesi ini (lihat §4) |
| B10 | Tool naming inconsistency | ✅ Tidak ada aksi | Info-only (di laporan dinyatakan "sudah cukup bagus") |
| B11 | Legacy code duplikasi `app/obsidian` + `app/graph_rag` | ⏸️ Menunggu keputusan owner | Direktori legacy masih ada (`app/obsidian/`, `app/graph_rag/` — 14+ file adapter). Penghapusan bersifat destruktif; `test_foldering_refactor` perlu update bila dihapus |

## 4. Pengujian & Verifikasi

**Metodologi:** (a) full pytest suite dari `services/ai`, (b) lint `ruff check app tests`, (c) smoke test live 17 tool read-only via MCP xninetzy. Semua hasil di bawah dicatat langsung dari eksekusi sesi ini.

**Hasil full suite:**

```
630 passed, 3 warnings in 336.87s (0:05:36)
```

- **630 passed / 0 failed / 0 skipped**, durasi **336,87 detik** (5 menit 37 detik).
- Sebelum eksekusi dipastikan tidak ada proses pytest lain berjalan (cek `pgrep -f pytest`: hanya false positive transient, tidak ada proses pytest aktif).
- Tidak ada kegagalan yang terkait `life_tools.py`/`test_life_tools.py` — seluruh 15 test life tools lulus, tidak perlu perbaikan test.
- 3 warnings non-fatal: deprecation Starlette/httpx pada `fastapi/testclient`, dan `FutureWarning` `get_sentence_embedding_dimension` → `get_embedding_dimension` pada `os/knowledge/embeddings.py:106`.

**Test baru sesi ini (dihitung dari file, `grep "def test_"`):**

| File | Jumlah test |
|---|---|
| tests/os/life/test_goal_tools.py | 7 |
| tests/os/life/test_life_tools.py | 15 |
| tests/tools/test_calculation.py | 16 |
| tests/tools/test_datetime_info.py | 6 |
| tests/tools/test_planning.py | 11 |
| tests/tools/test_helper_tools.py | 6 |
| tests/ecosystem/test_unified_search_tools.py | 3 |
| tests/os/knowledge/test_knowledge_tools.py | 2 |
| **Total** | **66** |

Keterangan: rencana awal menyebut 63 test untuk 7 file (dengan `test_calculation.py` = 15); jumlah aktual untuk 7 file tersebut adalah **64** (`test_calculation.py` = 16), ditambah `test_knowledge_tools.py` (2 test baru) sehingga total test baru = **66**. Semua file di atas berstatus baru (untracked/staged `A` di git). Selain itu ada penambahan test pada file lama: `tests/os/graph/test_graph_v3.py` (+13 baris) dan `tests/os/graph/test_neo4j_lifecycle.py` (+60 baris).

**Smoke test live via MCP (17 tool, semua read-only):**

| Tool | Hasil singkat |
|---|---|
| `skill_list` | 22 skill katalog; termasuk `test-mcp` [owner-installed] (uji coba) |
| `knowledge_list_sources` | 12 sumber knowledge ter-ingest |
| `goal_list` | 2 goal aktif (TEST GOAL - akan dihapus; Full-Stack Agentic AI Engineer) |
| `task_list` | 30 task aktif (tampilan 20 entri, mayoritas [HEBAT]) |
| `reminder_list` | 5 reminder pending (jadwal sholat 2026-08-02) |
| `hebat_login_status` | ❌ Belum login HEBAT |
| `graph_v3_stats` | Enabled, 43 node / 17 edge, outbox 0, **Neo4j online: False** (graceful), cooldown 0,0s |
| `ai_provider_status` | LLM aktif: **flaz / deepseek-v4-flash** |
| `style_show` | Default (belum ada gaya khusus) |
| `os_today` | Attention queue; fokus utama: Tugas 2 Implementasi ERP Odoo (#19) |
| `life_dashboard` | Minggu, 2 Agustus 2026; 2 goals aktif; tidak ada task due hari ini; habit Test MCP |
| `habit_today` | Habit `Test MCP` (0/1) |
| `learning_list_roadmaps` | 2 roadmap (#2 draft, #1 active) |
| `obsidian_folder_status` | `healthy: false`, 13 notes, 38 folder struktur canonical missing |
| `portal_info` | Cache struktur ada; status `human_verification_required`; session terenkripsi ada; submit KRS tidak diotomasi (read/notify only) |
| `skill_healthcheck` | Valid 22 / Invalid 0 / Warnings 4 |
| `unified_search` ("Evidence-Based Learning Techniques") | Knowledge 4 (K1–K4), Vault 5, Graph 1, Memory 1 |

## 5. Temuan Kode & Perilaku

- ✅ **FIXED — dead code `daily_review_generate`** (`tools/ecosystem/life_tools.py:356–377`): `summary_parts` sebelumnya dihitung tetapi tidak pernah dirender. Sekarang output menyertakan section `*Ringkasan:*` dengan fallback `"Belum ada ringkasan."` (`summary_text = "\n".join(...) or "Belum ada ringkasan."`, line 364; render line 377). Test assertion baru di `tests/os/life/test_life_tools.py`: `test_daily_review_generate_uses_checkin_and_tasks` memastikan `"Ringkasan"` dan `"Mood 4/5, Fokus 5/5"` muncul; `test_daily_review_generate_empty` memastikan fallback `"Belum ada task selesai dicatat"` + `"Belum ada goal aktif"`.
- **Quirk `calculate`**: `tools/internal/calculation.py:47` melakukan `expression.replace("%", "/100")` — jadi `%` diartikan **persen** (÷100), operator modulo `%` tidak didukung. Ekspresi tidak valid mengembalikan string error `"Error menghitung '...': ..."` (line 50–51), **tidak crash**. Perilaku ini terdokumentasi via test error-path: 6 test error di `tests/tools/test_calculation.py` (invalid expression, empty, incomplete, division-by-zero, unsafe, unsupported operator).
- **Duplikat evidence pada `unified_search`**: pada query "Evidence-Based Learning Techniques", hasil knowledge menampilkan K3 dan K4 dari sumber yang sama ("Prompt Pondasi — Cara Belajar Efektif (Evidence-Based Learning Techniques)"). Ini normal untuk RAG multi-chunk (dua chunk dari satu sumber), bukan bug. (K2 pada hasil tersebut adalah "TEST MCP Knowledge - hapus" — data uji, lihat §7.)
- **Skill healthcheck**: 22 valid / 0 invalid / 4 warnings — warning pada `gh-fix-ci`, `playwright`, `academic-assignment` (body memuat URL eksternal; verifikasi provenance & network intent) dan `playwright-interactive` (2 warning: URL eksternal + SKILL.md 693 baris > target progressive disclosure 500 baris).
- **Obsidian folder status**: `healthy=false`; 13 notes ditemukan; **38 folder struktur canonical belum dibuat** (Home, Inbox/*, Learning/*, Academic/*, Research/*, Life/*, Knowledge/*, Attachments, System/*, Archive, dll); `duplicate_ids` kosong.

## 6. Infrastruktur & Integrasi Eksternal

- **Neo4j / GraphRAG V3**: enabled (43 node aktif, 17 edge aktif, outbox pending 0) tetapi **Neo4j online: False** → sistem berjalan graceful dengan failure cooldown (0,0s saat dicek). Root-cause mekanisme autostart sinkron dijelaskan di §1.
- **HEBAT (Moodle)**: **belum login** — perlu perintah `login hebat` sebelum sinkronisasi course/assignment.
- **Portal Cyber Campus**: session terenkripsi **ada**, cache struktur **ada**, status struktur `human_verification_required` (CAPTCHA tidak pernah disolve otomatis); submit KRS **tidak diotomasi** — monitoring hanya read/notify.
- **Provider LLM aktif**: `flaz` / `deepseek-v4-flash` (allowlist deployment).

## 7. Data Hygiene

Data uji sisa berikut ditandai "akan dihapus" dan **butuh konfirmasi owner** sebelum dihapus (aksi destruktif):

| Jenis | ID/Nama | Keterangan |
|---|---|---|
| Knowledge source | #12 "TEST MCP Knowledge - hapus" | manual_note, 2026-08-01 |
| Knowledge source | #2 "Test knowledge text - akan dihapus" | tipe test, 2026-07-30 |
| Goal | #1 "TEST GOAL - akan dihapus" | personal / daily / low |
| Habit | "Test MCP" | 0/1 hari ini |
| Skill owner | `test-mcp` | deskripsi: "Skill uji coba MCP session testing - hapus jika tidak diperlukan" |

## 8. Risiko & Gap

- **B5 / B8 di luar repo** — tidak dapat dikerjakan dari repo ini (MCP eksternal).
- **B11 menunggu keputusan** — hapus vs pertahankan adapter legacy (`app/obsidian`, `app/graph_rag`); penghapusan membutuhkan update test arsitektur (`test_foldering_refactor`).
- **Vault canonical structure belum di-init** — `obsidian_folder_status` menunjukkan 38 folder missing; opsi: `obsidian_vault_init` atau organize preview + approval owner.
- **Timeout Neo4j autostart belum dipatch** — autostart sinkron tanpa latch lintas-proses berpotensi menimbulkan intermittent timeout tool saat docker belum siap (analisis lengkap §1).
- **`TOOL_BUG_REPORT_SESI_20260730.md` digabung ke dokumen ini** — file asli (224 baris) terhapus dari working tree oleh proses lain; kontennya kini permanen di §2 dokumen ini dan file terpisah tidak dipulihkan.
- **Agent/proses paralel lain aktif mengedit repo** — `git status` menunjukkan banyak file graph yang dimodifikasi (`neo4j_lifecycle.py`, `neo4j_store.py`, `graph_service.py`, `graph_tools_v3.py`, dll.) dan sejumlah file `docs/plan/*` dihapus dari working tree oleh proses lain; potensi konflik merge dan kehilangan perubahan yang tidak disengaja.

## 9. Rekomendasi & Next Steps (urut prioritas)

1. **Putuskan B11** — Opsi A: hapus `app/obsidian` + `app/graph_rag` dan update `test_foldering_refactor`; Opsi B: pertahankan dengan dokumentasi debt.
2. **Patch Neo4j autostart** (latch/async/timeout terpisah dari proses panggilan tool) — issue terpisah dari bug report B1–B11.
3. **Cleanup data uji sisa** (§7) setelah konfirmasi owner.
4. **Init struktur vault canonical** (`obsidian_vault_init` atau organize preview + approval).
5. **Login HEBAT** lalu sync assignments/reminder.

## 10. Referensi File

- `docs/plan/TOOL_BUG_REPORT_SESI_20260730.md` — dokumen asli (224 baris) terhapus dari working tree; seluruh kontennya **digabung ke dokumen ini** (lihat §2)
- `bug.md` (root repo) — MCP Ecosystem Bug Report 2026-07-28 (permission/ownership), 99 baris
- `docs/plan/analysis_terbaru.md` (dokumen ini)
- `services/ai/app/xninetzy/tools/ecosystem/unified_search_tools.py` (baru)
- `services/ai/app/xninetzy/tools/ecosystem/life_tools.py` (fix `daily_review_generate`)
- `services/ai/app/xninetzy/tools/internal/calculation.py` (quirk `%`)
- `services/ai/app/xninetzy/os/graph/v3/neo4j_lifecycle.py` + `neo4j_store.py` (autostart sinkron)
- File test baru: `services/ai/tests/os/life/test_goal_tools.py`, `services/ai/tests/os/life/test_life_tools.py`, `services/ai/tests/tools/test_calculation.py`, `services/ai/tests/tools/test_datetime_info.py`, `services/ai/tests/tools/test_planning.py`, `services/ai/tests/tools/test_helper_tools.py`, `services/ai/tests/ecosystem/test_unified_search_tools.py`, `services/ai/tests/os/knowledge/test_knowledge_tools.py`
