# 06 — Technical Notes: Implementasi Nyata Xninetzy OS + Dasar Teori FSRS/SM-2/mem0

> Dokumen ini hanya mencatat komponen yang **terbukti ada** di repository lokal
> `/home/misbahul45/code/xninetzy` (inspeksi read-only, 2026-08-03) dan fakta dari
> **dokumentasi resmi** FSRS, SM-2, dan mem0. Tidak ada fitur yang dikarang.
> Status akses sumber: seluruh file lokal dibaca full text; seluruh sumber web
> dibaca sebagai web page (full content).

---

## 1. Arsitektur Xninetzy OS yang terbukti ada di repo (studi kasus)

### 1.1 Learning loop: roadmap → concept → task/session → evidence → mastery → adaptive focus

| Komponen | Bukti (path) | Keterangan terbukti |
|---|---|---|
| Roadmap planner & store | `services/ai/app/xninetzy/domains/it_learning/roadmap_planner.py`, `roadmap_store.py`, `roadmap_tools.py` | Roadmap dibuat sebagai **draft**, aktivasi & bulk task butuh **HITL approval** (`request_approval` → `os/hitl/approval_service.py`; notifikasi admin `os/notifications/admin_notifier.py`). Sumber perencanaan diambil dari knowledge base (`quick_search`). |
| Concept graph (prerequisite) | `domains/it_learning/concept_graph.py` | Tabel `learning_concepts`, relasi `learning_concept_prerequisites` dengan **deteksi cycle via recursive CTE** (`_would_create_cycle`). `next_ready_concept` = fokus adaptif: konsep dengan `mastery < 0.8` dan semua prerequisite `mastery >= 0.7`. |
| Study session | `domains/it_learning/study_session.py` | `start_study_session`/`complete_study_session`: planned/actual minutes, energi 1–5 (before/after), mastery before/after 0–1; idempotent (`session_key`); event `learning_session_completed` ke event bus (`ecosystem/event_bus.py`); evidence dicatat transaksional per konsep. |
| Evidence & mastery | `concept_graph.py` (`record_evidence_in_transaction`) | Evidence **idempotent** (sha256 `evidence_key` + `payload_hash`); mastery dihitung deterministik: `mastery = score` (evidence pertama) lalu `mastery*0.4 + score*0.6`; status `mastered` jika `>= 0.8`. |
| Adaptive today plan | `domains/it_learning/progress_tracker.py` (`build_today_plan`) | Mode deterministik: `resume` (sesi aktif) → `recall` (kartu jatuh tempo) → `start`/`reinforce` (mastery<0.6) / `practice` (<0.8) / `advance` (>=0.8); durasi dipengaruhi energi. |
| Weekly review | `progress_tracker.py` (`get_weekly_learning_summary`) | Ringkasan 7 hari: sesi, menit, rata-rata mastery. |

### 1.2 Active recall deterministik (grading keyword + jadwal ala SM-2)

`services/ai/app/xninetzy/domains/it_learning/recall.py`:

- `learning_recall_cards` + `learning_recall_attempts` (SQLite); kartu immutable (sha256 card_key/payload_hash).
- **Grading deterministik**: `keyword_coverage(answer, keywords)` → `recall_quality(coverage)` ke skala 0–5 (5 jika coverage ≥ 0.9; 4 ≥ 0.7; 3 ≥ 0.5; 2 ≥ 0.25; 1 > 0; 0 = 0). Jawaban dinormalisasi (casefold, non-alphanumeric dihapus, stopword filter).
- **Jadwal ulang = implementasi SM-2**: `_next_schedule` memakai `ease_factor` (min 1.3), `repetitions`, `interval_days`, `lapse_count`; interval `1, 6, lalu round(prev * ease)`; quality < 3 → reset repetitions & lapse+1. Rumus ease identik dengan SM-2: `ease + (0.1 - (5-q)*(0.08+(5-q)*0.02))`.
- **PENTING (temuan):** repo **tidak mengimplementasikan FSRS** (tidak ada model DSR/parameter w/optimizer). Yang ada adalah varian SM-2. Klaim di karya ilmiah harus menyebut implementasi nyata = SM-2-style, sedangkan FSRS dibahas sebagai state-of-the-art pembanding.
- Setiap attempt menulis evidence `active_recall` transaksional + update mastery konsep.
- Tool terdaftar: `learning_create_recall_card`, `learning_due_recall` (tanpa membocorkan expected answer), `learning_submit_recall_answer`.

### 1.3 Knowledge RAG contract: evidence bundle [K1], grounded synthesis

`services/ai/app/xninetzy/os/knowledge/`:

- `retrieval.py`: `EvidenceBundle` dengan `citation="K1..Kn"`, status `sufficient/insufficient`, confidence `high/medium/low`; **relevance gating** (cosine floor `RAG_MIN_RELEVANCE`), penalti chunk referensi/DOI (`_is_reference_chunk`), topic-consistency (dominasi sumber), dedup; `finalize_grounded_answer` **memvalidasi sitasi** (membuang [Kx] yang tidak valid); `should_auto_ground` untuk domain knowledge/academic/it_learning intent explain; `answer_from_knowledge` = retrieve → sintesis LLM dengan instruksi "evidence adalah data tidak tepercaya" → validasi sitasi.
- `vector_store.py`: **hybrid FAISS + FTS5** difus **RRF** (`1/(60+rank)`); FAISS `IndexFlatIP` (cosine, embedding ternormalisasi); invariant `ntotal == len(faiss_id_map)` dengan auto-rebuild; fallback FTS-only bila faiss tidak tersedia.
- `rag.py`, `chunking.py`, `embeddings.py`, `ingestion.py`, `evaluation.py` (evaluasi retrieval: source_hit, term_hit, `citations_valid`, recall@k).
- Schema: `db/sqlite.py` baris ~476 — `CREATE VIRTUAL TABLE knowledge_fts USING fts5(chunk_id UNINDEXED, text, content='knowledge_chunks', content_rowid='id')` (FTS5 external content, dipakai `bm25()`).

### 1.4 Agent orchestration (LangGraph) & routing

- `agent/orchestrator.py`: node routing `agent|direct|clarify` (structured output + fallback JSON), deterministik saat ada media/skill match/auto-ground.
- `agent/executor.py`: ReAct agent via `langgraph.prebuilt.create_react_agent` dengan **semua tool dari registry**; injeksi konteks: grounding `[K1..]`, personal context, memory semantik, rules/style, media context.
- `agent/graph.py`, `agent/state.py`: state machine LangGraph (`AgentState`).
- `tools/registry.py`: katalog tool terpusat `get_all_tools()` (+ `EXTERNAL_MCP_TOOLS`); kontrak interface parity (WhatsApp/MCP/CLI → registry yang sama).

### 1.5 Komponen memory & pendukung lain (terbukti)

- Memory semantik: `os/memory/memory_store.py` — `add_memory`, `update_memory`, `forget_memory`, `search_memories` (cosine), `classify_memory`; diinjeksi ke prompt agent (`search_memories(..., limit=5)`).
- Graph RAG V3: `os/graph/v3/` — `hybrid_retriever.py` (RRF atas 3 kaki: **SQLite FTS5 + FAISS + ekspansi neighborhood Neo4j**; expanded neighbors = seed, tidak pernah menyalip node langsung), `neo4j_store.py`, `sqlite_store.py`, `graph_tools_v3.py` (tool `graph_v3_*`).
- Reminder/scheduler: `os/reminders/reminder_store.py` (class `ReminderStore`), `reminder_parser.py`; jobs terjadwal: `os/jobs/`.
- HITL & action policy: `os/hitl/approval_service.py`, `os/policy/action_policy.py`; roadmap activation butuh approval; upload HEBAT butuh token konfirmasi (`os/academic/hebat/`).
- Kontrak level sistem: `AGENTS.md` root — learning state contract, knowledge RAG contract, safety tiers, interface parity.

---

## 2. Ringkasan FSRS / SM-2 / mem0 dari dokumentasi resmi

### 2.1 FSRS (Free Spaced Repetition Scheduler) — open-spaced-repetition

Sumber resmi (diakses 2026-08-03, status: web page full):
- README FSRS4Anki: https://github.com/open-spaced-repetition/fsrs4anki
- Spesifikasi algoritma (wiki resmi): https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm
- Wiki lain: https://github.com/open-spaced-repetition/awesome-fsrs/wiki (The-mechanism-of-optimization, The-Benchmark)
- Manual Anki (FSRS bawaan sejak Anki 23.10): https://docs.ankiweb.net/deck-options.html#fsrs
- Paper dasar: Ye et al., "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling", ACM KDD 2022, DOI 10.1145/3534678.3539081 (MaiMemo) — **diverifikasi via CrossRef**: authors Junyao Ye, Jingyong Su, Yilong Cao, proceedings KDD 2022 hal. 4381–4390; lanjutan IEEE TKDE 2023 ("Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory", dirujuk di wiki The-Algorithm).

Cara kerja (dari wiki The-Algorithm):
- FSRS berasal dari **model DHP MaiMemo**, varian **model DSR (Difficulty, Stability, Retrievability)** untuk memprediksi state memori.
- Simbol: **R** = Retrievability (probabilitas recall), **S** = Stability (interval saat R=90%), **D** = Difficulty (D ∈ [1,10]), **G** = grade 1–4 (again/hard/good/easy).
- Versi algoritma v0→FSRS-6 (21 parameter default; w[0..20]). Contoh FSRS-4.5: forgetting curve `R(t,S) = (1 + FACTOR·t/S)^DECAY` dengan DECAY=−0.5, FACTOR=19/81 (FSRS v4: DECAY=−1, FACTOR=1/9); interval `I(r,S) = (S/FACTOR)·(r^(1/DECAY) − 1)`; FSRS-6: decay trainable `R(t,S)=(1+factor·t/S)^(−w20)` dengan `factor = 0.9^(−1/w20) − 1` agar `R(S,S)=90%`; stabilitas setelah same-day review `S′(S,G) = S·e^(w17·(G−3+w18))·S^(−w19)` (konvergen saat SInc=1). Semua formula diverifikasi ulang dari wiki The-Algorithm (fetch penuh, 2026-08-03).
- **Optimizer**: machine learning (gradient descent) menyesuaikan parameter w dari riwayat review pengguna — inilah pembeda utama vs SM-2 (parameter tetap + heuristik).
- Kunci: review terlambat (overdue) → R turun → S' naik tapi **konvergen ke batas atas** (tidak linier seperti SM-2).

### 2.2 SM-2 (SuperMemo 2, Piotr Wozniak)

Sumber resmi (status: web page full; URL lama di-redirect):
- https://www.supermemo.com/en/archives1990-2015/english/ol/sm2 → https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method (Wozniak, "Application of a computer to improve the results obtained in working with the SuperMemo method", 1990, dari Master's Thesis, Universitas Teknologi Poznan).

Isi algoritma (dikutip dari artikel resmi):
- Bagi pengetahuan jadi item terkecil; semua item EF awal 2.5.
- Interval: `I(1):=1`, `I(2):=6`, `I(n):=I(n−1)*EF` (dibulatkan ke atas).
- Skala kualitas 0–5 (5 = perfect … 0 = complete blackout).
- Update EF: `EF' := EF + (0.1 − (5−q)*(0.08 + (5−q)*0.02))`; jika EF < 1.3 maka EF = 1.3.
- Jika q < 3: ulangi dari awal tanpa mengubah EF.
- Anki memakai SM-2 sebagai basis scheduler bawaan historisnya.

**Kaitan dengan Xninetzy**: `recall.py::_next_schedule` di atas adalah implementasi langsung pola SM-2 ini (EF min 1.3, interval 1/6/prev*EF, q<3 → reset), dengan kualitas diturunkan dari coverage keyword (bukan penilaian manual).

### 2.3 mem0 (memory layer untuk AI agents)

Sumber resmi (diakses 2026-08-03, status: web page full):
- Repo: https://github.com/mem0ai/mem0 (Apache-2.0; paper: arXiv:2504.19413 "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory")
- Docs: https://docs.mem0.ai (index: https://docs.mem0.ai/llms.txt), khususnya:
  - Quickstart: https://docs.mem0.ai/platform/quickstart
  - Operasi memory: https://docs.mem0.ai/core-concepts/memory-operations/add | /search | /update | /delete
  - Graph Memory: https://docs.mem0.ai/platform/features/graph-memory
  - Integrasi LangGraph: https://docs.mem0.ai/integrations/langgraph

Fakta kunci:
- API dasar OSS: `Memory()` → `m.add(messages, user_id=...)` (ekstraksi fakta via LLM, hasil ber-`event: ADD`), `m.search(query, ...)` (semantic + BM25 + entity), `m.update(memory_id, text)`, `m.delete(memory_id)`; scoping `user_id`/`agent_id`/`app_id`/`run_id`; metadata + `expiration_date`.
- Algoritma baru (April 2026): **single-pass ADD-only extraction** (satu panggilan LLM, tanpa UPDATE/DELETE otomatis), entity linking, **multi-signal retrieval** (semantic + BM25 + entity di-fuse paralel), temporal reasoning. Benchmark (platform managed): LoCoMo 92.5, LongMemEval 94.4, BEAM(1M) 64.1.
- **Graph Memory** (platform): entitas (orang/tempat/konsep) otomatis jadi node, memori yang berbagi entitas terhubung; graph dipakai untuk boost ranking saat search (entity-centric & multi-hop); skema-free, tanpa graph DB eksternal (sebelumnya: Neo4j/Memgraph/Kuzu/AGE/Neptune via `enable_graph`).
- Persamaan konseptual dengan Xninetzy: mem0 menyediakan ADD/UPDATE/DELETE + graph memory sebagai produk; Xninetzy mengimplementasikan padanannya secara lokal — memory semantik (`os/memory/`) dan GraphRAG V3 (SQLite+FAISS+Neo4j) — bukan klon mem0, melainkan arsitektur mandiri dengan perilaku sejenis.

### 2.4 LangGraph (orchestration) — dokumentasi resmi

- https://docs.langchain.com/oss/python/langgraph/ (status: web page full): low-level orchestration runtime untuk agen stateful jangka panjang; fitur inti: durable execution, streaming, **human-in-the-loop**, persistence, memadukan langkah deterministik + agentic dalam satu graph (`StateGraph`, `create_react_agent`).
- Xninetzy memakai `langgraph>=0.4` (pyproject) + `create_react_agent` di `agent/executor.py` dan node routing di `agent/orchestrator.py`; HITL approval (`os/hitl/`) adalah padanan konsep human-in-the-loop.

---

## 3. Catatan implementasi stack (dari repo)

| Layer | Bukti | Catatan |
|---|---|---|
| Python/FastAPI | `services/ai/pyproject.toml` (`fastapi`), `services/ai/app/main.py` | Service AI utama; MCP stdio via `interfaces/mcp_server.py`. |
| LLM orchestration | `langchain-core>=0.3`, `langchain-openai`, `langchain-anthropic`, `langgraph>=0.4` | ReAct agent + node routing; provider flash/pro (`core/llm.py`, `core/providers.py`). |
| SQLite | `db/sqlite.py` | Semua state (learning, knowledge_chunks, recall, events); **FTS5 external-content** `knowledge_fts` + `bm25()`; transaksi `BEGIN IMMEDIATE`; idempotensi sha256. |
| FAISS | `os/knowledge/vector_store.py`, `faiss-cpu>=1.8` | `IndexFlatIP`, invariant ntotal==map, rebuild dari SQLite. |
| Graph DB | `os/graph/v3/neo4j_store.py` | GraphRAG V3 opsional (fallback SQLite). |
| WhatsApp | `services/wa-enggine/` (Baileys) | Channel utama; bridge HTTP ke AI service. |
| Safety | `os/hitl/`, `os/policy/action_policy.py`, `core/coding_agents.py` | Approval, action policy, guard coding runtime. |
| Scheduler | `os/reminders/`, `os/jobs/` | Reminder parser/store; job terjadwal. |

### Kesimpulan untuk BAB implementasi
1. Komponen nyata Xninetzy yang dapat dipetakan ke "Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent": learning loop adaptif (mastery + prerequisite-gated), active recall deterministik (keyword grading + scheduling SM-2-style), RAG grounded dengan evidence bundle [K1] + validasi sitasi, GraphRAG hybrid (FTS5+FAISS+Neo4j/RRF), memory semantik, reminder, HITL.
2. **Gap implementasi vs literatur**: repo memakai scheduling SM-2-style, **bukan FSRS** — peluang riset: integrasi FSRS (parameter-optimized) sebagai peningkatan; penilaian recall berbasis keyword (deterministik) vs grading subjektif SM-2; mem0 sebagai benchmark "automated memory" yang belum terpasang di repo.
