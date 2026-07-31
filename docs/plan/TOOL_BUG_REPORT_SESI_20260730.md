# Tool Bug Report — Sesi Deep Research & Implementasi 2026-07-30
## Analisis Bug dari Sesi: Feynman Technique, Learning Techniques, Vault Integration

**Tester:** Misbahul (via OpenCode MCP)  
**Tanggal:** 30 Juli 2026  
**Durasi Sesi:** ~2 jam (research + implementation)  
**Tools Dipakai:** ~20 tool calls (xninetzy MCP + web_search + paper_research + filesystem)

---

## Ringkasan

| Severitas | Jumlah | Deskripsi |
|---|---|---|
| 🔴 Critical | 3 | Tool gagal total atau data hilang |
| 🟡 Medium | 5 | Tool bekerja tapi hasil tidak akurat/terbatas |
| 🔵 Info | 3 | UX buruk, confusing, atau missing feature |

---

## 🔴 Critical Bugs

### B1. `knowledge_ingest_file` hanya support PDF — markdown gagal total

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

### B2. `obsidian_search` pakai substring linear scan — O(n) full vault read

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

### B3. `graph_search` pake SQL `LIKE %query%` — search kaku

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

## 🟡 Medium Bugs

### B4. `obsidian_read` tidak punya offset/limit — truncate hard di 3000 chars

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

### B5. Web search (`web_search_search` / DuckDuckGo) sering return 0 results

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

### B6. `obsidian_create` vs `obsidian_save_note` — duplikasi dengan perilaku berbeda

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

### B7. `obsidian_update_section` heading matching terlalu strict

**File:** `services/ai/app/xninetzy/os/notes/markdown_service.py` (via `vault_service.py:110-141`)

**Apa yang terjadi:**  
Whitespace ekstra di heading (`##  Title` vs `## Title`) bisa bikin gagal match atau duplicate section.

**Dampak:**  
Potensi duplicate sections atau silent failure.

**Saran:**
- Trim whitespace heading sebelum match
- Fallback: append kalau heading tidak ditemukan

---

### B8. Paper research tools return null abstracts

**Tool:** `paper_research_search_semantic`  
**Test:** 5 papers, semua `"abstract": null`

**Dampak:**  
Sulit menilai relevansi paper tanpa abstrak. Harus download dulu.

**Saran:**
- Fallback ke source lain (Crossref, OpenAlex) kalau abstract null

---

## 🔵 Informational / UX Issues

### B9. Dua tool search: `obsidian_search` (vault) vs `graph_search` (graph RAG)

Tidak ada unified search yang cover vault + graph + knowledge + memory.

**Saran:**  
Unified search tool.

### B10. Tool naming inconsistency

Beberapa pake prefix domain (`obsidian_*`, `knowledge_*`, `graph_*`), beberapa tidak (`calculate`, `datetime_now`).

**Saran:**  
Sudah cukup bagus — cukup info.

### B11. Legacy code duplikasi

- `services/ai/app/xninetzy/os/notes/vault_service.py` (primary) vs `services/ai/app/obsidian/vault_service.py` (legacy)
- `services/ai/app/xninetzy/os/graph/graph_tools.py` (primary) vs `services/ai/app/graph_rag/graph_tools.py` (legacy)

**Saran:**  
Hapus file legacy setelah diverifikasi tidak ada import yang merujuk.

---

## Prioritas Perbaikan

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
