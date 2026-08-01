# Analisis Codebase Graph RAG Xninetzy

Tanggal: 2026-08-01
Scope: `services/ai/app/xninetzy/os/graph/` + integrasi MCP, registry, schema, tes, dan dokumen desain terkait.

## 1. Letak dan Arsitektur

Sistem Graph RAG hidup di `services/ai/app/xninetzy/os/graph/` (hasil refactoring dari `app/graph_rag/` yang kini tinggal adapter backward-compat) dan terhubung ke MCP melalui registry terpusat.

```
os/graph/
├── models.py        → Pydantic GraphNode / GraphEdge (definisi tipe)
├── graph_store.py   → Lapisan persistence SQLite (add_node, add_edge, search_nodes, edges_for_node)
├── graph_context.py → Traversal 1-hop (node + edge tetangga) → format markdown
├── graph_tools.py   → 7 definisi tool LangChain (@tool) yang diekspos ke MCP
├── graph_search.py  → Re-export search_nodes (kompatibilitas)
├── graph_builder.py → Placeholder kosong (hanya docstring)
└── prompts.py       → 1 kalimat prompt: graph menghubungkan topic, concept, source, note, task, goal, roadmap, research brief
```

Alur keterhubungan:

```
MCP client (Codex/Claude/OpenCode)
        │  stdio
        ▼
interfaces/mcp_server.py (FastMCP "xninetzy")
        │  expose_xninetzy_tools()  ← expose OTOMATIS semua tool registry
        ▼
interfaces/mcp_tool_adapter.py (inject identity local-owner, buang field trusted)
        ▼
tools/registry.py  →  os/graph/graph_tools.py
        ▼
os/graph/graph_store.py  →  SQLite (db/migrations.py: graph_nodes, graph_edges)
```

## 2. Bagaimana sistem dibangun — per lapisan

### a) Storage: SQLite dua tabel (bukan Neo4j)
Schema dibuat di `db/migrations.py:298-317`:
- `graph_nodes` — id, node_type, title, content, metadata_json, created_at, updated_at
- `graph_edges` — id, source_node_id, target_node_id, edge_type, metadata_json, created_at

Tidak ada `REFERENCES` (foreign key), tidak ada index khusus selain primary key.

### b) Domain tools (graph_tools.py)
7 tool terdaftar di registry (3 read + 4 write):

| Tool | Fungsi | Catatan |
|---|---|---|
| `graph_add_node` | Insert node | Bebas string `node_type`, tanpa idempotency key |
| `graph_add_edge` | Insert edge | Tanpa validasi node exist |
| `graph_search` | Cari node | `LIKE %query%` — case-sensitive |
| `graph_get_context` | Topic map 5 node + 3 edge/node | Traversal 1-hop |
| `graph_explain_topic_map` | Identik dengan `graph_get_context` | Duplikasi fungsi |
| `graph_link_research_to_roadmap` | Edge hardcode `created_from` | roadmap → research |
| `graph_link_note_to_topic` | Edge hardcode `stored_in` | note → topic |

### c) Retrieval (graph_store.search_nodes)
Murni keyword substring — SQL `WHERE title LIKE ? OR content LIKE ? OR node_type LIKE ?` tanpa `COLLATE NOCASE`, tanpa FTS5, tanpa embedding. Ini masalah terdokumentasi (bug B3 di TOOL_BUG_REPORT_SESI_20260730.md): search "learning techniques" tidak menemukan node berjudul "Evidence-Based Learning Techniques…".

### d) Konteks (graph_context.get_graph_context)
Ambil 5 node relevan → untuk tiap node ambil maks. 3 edge (JOIN dua arah) → format WhatsApp markdown. Jadi "topic map"-nya adalah ekspansi 1-hop dari hasil keyword search, bukan traversal graph sejati.

### e) Integrasi MCP — bagian paling rapi
`mcp_server.py` hanya mendefinisikan ~20 tool inti secara manual, lalu sisanya via `expose_xninetzy_tools()` yang otomatis me-expose seluruh isi registry. Kunci desainnya di `mcp_tool_adapter.py`:
- `MCPPrincipal` → identity local-owner di-inject server-side; caller tidak bisa memalsukan chat_id/sender_id (field trusted dibuang dari signature)
- Nama tool MCP = nama tool LangChain, jadi graph_* tampil apa adanya di client

### f) Integrasi agent LangGraph
- Prompt agent mencantumkan kategori "Graph RAG: graph_search, graph_get_context, graph_explain_topic_map, graph_link_note_to_topic"
- Registry kategori "graph" hanya berisi 3 tool read
- chat_failover.py mengecualikan graph_explain_topic_map dari fallback model umum
- Skill system punya alias graph_rag → graph-rag di skills/registry.py

## 3. Temuan penting (dari inspeksi kode + dokumen repo)

1. Ini Graph RAG MVP paling minimal, bukan GraphRAG sejati: graph_builder.py masih placeholder kosong, dan GRAPH_RAG_MVP.md mengakui "belum Neo4j dan belum hybrid semantic graph retrieval penuh".
2. Graph praktis KOSONG — mcp-usability-review.md (MED-09) mencatat semua query return "Belum ada node graph yang cocok" (hanya 2 node terisi), dan GAP_ANALYSIS_ENGINEERING_VISION.md menegaskan: "walau tools ada, data tidak ada… populate graph otomatis saat knowledge ingest + research complete" — tapi tidak ada kode populate otomatis; semua insert hanya via tool manual.
3. graph_explain_topic_map = alias graph_get_context — duplikasi yang membingungkan.
4. Write tanpa idempotency key — melanggar reliability rule di AGENTS.md (side-effect harus idempotent); tercatat juga di gap analysis.
5. Tidak ada validasi referensial — add_edge bisa menunjuk node yang tidak ada.
6. Search kaku — LIKE case-sensitive, no FTS, no semantic (bug B3).
7. Output markdown WhatsApp, bukan JSON — agent engineering loop harus parse teks (gap analysis poin 1).
8. models.py (GraphNode/GraphEdge) tidak benar-benar dipakai store — store bekerja langsung dengan dict/row SQLite.
9. Test sangat tipis: 1 test yang hanya mengecek insert + search dasar (tests/os/graph/test_graph_rag.py).
10. Ada jalur legacy app/graph_rag/ → re-export, plus app/skills/graph_rag/ → re-export — kompatibilitas dijaga baik, tapi menambah permukaan import.

## 4. Skor kematangan

| Aspek | Status |
|---|---|
| Storage & schema | ✅ Berfungsi (SQLite) |
| Eksposur MCP | ✅ Otomatis & aman (identity injection) |
| Traversal/retrieval | 🟡 1-hop keyword-only, case-sensitive |
| Graph builder/ingest otomatis | ❌ Placeholder |
| Semantic search | ❌ Belum ada |
| Idempotency & validasi | ❌ Belum ada |
| Data terisi | ❌ Kosong dalam praktik |

## 5. Rekomendasi prioritas

1. P0 — Populate graph otomatis: hook ke knowledge_ingest_* dan research complete (buat node topic/source + edge related_to/created_from), agar closed-loop Capture→Understand→Plan berfungsi (sesuai solusi di gap analysis).
2. P0 — Perbaiki search: COLLATE NOCASE + FTS5 di graph_nodes (bug B3); opsi lanjutan: inject embedding node dengan model yang sudah dipakai FAISS knowledge.
3. P1 — Idempotency key di graph_add_node/graph_add_edge + validasi node exist sebelum edge (AGENTS.md reliability rules).
4. P1 — Bedakan atau hapus graph_explain_topic_map (saat ini duplikat).
5. P2 — Index source_node_id/target_node_id untuk traversal, dan pertimbangkan output JSON+markdown dual.

## Referensi file yang dianalisis

- services/ai/app/xninetzy/os/graph/*.py (7 modul)
- services/ai/app/xninetzy/interfaces/mcp_server.py
- services/ai/app/xninetzy/interfaces/mcp_tool_adapter.py
- services/ai/app/xninetzy/tools/registry.py
- services/ai/app/xninetzy/db/migrations.py (baris 298-317)
- services/ai/app/xninetzy/agent/prompts.py
- services/ai/app/xninetzy/skills/registry.py
- services/ai/tests/os/graph/test_graph_rag.py
- docs/plan/GRAPH_RAG_MVP.md
- docs/plan/TOOL_BUG_REPORT_SESI_20260730.md (bug B3)
- docs/plan/mcp-usability-review.md (MED-09)
- docs/plan/GAP_ANALYSIS_ENGINEERING_VISION.md

Catatan: Semua klaim berdasarkan inspeksi full text file lokal; temuan tentang bug/gap bersumber dari dokumen repo yang dibaca langsung.
