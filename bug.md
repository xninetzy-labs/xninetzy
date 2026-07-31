# MCP Ecosystem Bug Report
> Date: 2026-07-28
> Scope: xninetzy MCP server (`services/ai/app/xninetzy/interfaces/mcp_server.py`)

## Status Resolusi

Diverifikasi pada 2026-07-28:

- ✅ SQLite dapat menjalankan transaksi tulis dari MCP host.
- ✅ Folder `Daily`, `Plans`, `.backup`, `vector`, `wa-media`,
  `web-analysis`, dan `hebat` sudah writable oleh user host.
- ✅ Docker AI memakai UID/GID host untuk mencegah file baru kembali root-owned.
- ✅ Reminder memahami relative time Indonesia dan Inggris, termasuk
  `in 1 minute`.
- ✅ Knowledge search menghapus hasil identik dari source/chunk yang sama.
- ✅ Seluruh 149 tool registry Xninetzy terekspos melalui MCP.
- ✅ HEBAT login, AJAX course sync, activity sync, resolver pluginfile, dan
  download PDF sudah diverifikasi end-to-end.
- ℹ️ Relevansi knowledge tetap bergantung pada dokumen yang sudah diingest.
- ℹ️ `obsidian_backlinks(limit)` bukan bug ketika vault memang tidak memiliki
  backlink.


---

## 🔴 CRITICAL

### 1. SQLite Read-Only Database
Write operations (`obsidian_create`, `obsidian_append`, `obsidian_update_section`) fail with:
```
attempt to write a readonly database
```
- **File:** `services/ai/data/xninetzy.sqlite3`
- **Evidence:** WAL files (`-wal`, `-shm`) present — possible lock contention
- **Impact:** All note-create/append/update tools broken

### 2. Vault Folder Ownership (root)
Two Obsidian vault folders still owned by root, blocking writes:
```
Daily/   → root:root
Plans/   → root:root
```
- **Impact:** MCP can't write Daily notes or edit Plans

### 3. Backup Directory Permission Cascade
MCP server tries to create `.backup/YYYY-MM-DD/` on every write but fails:
```
[Errno 13] Permission denied: '.../.backup/2026-07-28'
```
- **Root cause:** Backup dir or its parent had wrong ownership (partially fixed)
- **Impact:** Backup creation error cascades into transaction rollback

### 4. Additional Root-owned Data Directories
```
services/ai/data/vector/     → root:root
services/ai/data/wa-media/   → root:root
services/ai/data/web-analysis/ → root:root
```
- **Impact:** Likely breaks vector index rebuild, media ingestion, web analysis tools

---

## 🟡 MEDIUM

### 5. `knowledge_answer` Low Relevance
RAG returns relevance ~0.08 — knowledge base is empty (no ingested documents).
- **Impact:** Q&A falls back to model knowledge, no RAG value

### 6. `reminder_create` Natural Language Parsing
Input `"Test reminder in 1 minute"` fails with:
```
Waktu reminder masih ambigu. Sebutin tanggal/jamnya ya
```
- **Parser too strict:** relative time ("in 1 minute") not supported
- **Impact:** Reminder create unreliable for natural input

---

## 🟢 MINOR

### 7. `knowledge_search` Duplicate Results
Ingesting single text produces duplicate rows on search (2 identical results).
- **Suspected:** Indexing without dedup or chunk overlap

### 8. `obsidian_backlinks` Limit Parameter
Tag `limit` defined but no backlinks exist — purely informational.

---

## Root Cause Summary

**Permission mismatch:** MCP server runs as `misbahul45` but many data directories and vault folders are owned by `root`. SQLite write operations fail because the OS process can't create/modify journal files in directories it doesn't own.

**Fix required:** `pkexec chown -R misbahul45:misbahul45` on:
- `/home/misbahul45/Documents/xninetzy/Daily/`
- `/home/misbahul45/Documents/xninetzy/Plans/`
- `/home/misbahul45/code/xninetzy/services/ai/data/vector/`
- `/home/misbahul45/code/xninetzy/services/ai/data/wa-media/`
- `/home/misbahul45/code/xninetzy/services/ai/data/web-analysis/`
