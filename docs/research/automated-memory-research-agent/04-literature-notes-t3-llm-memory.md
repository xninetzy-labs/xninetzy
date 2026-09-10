# Literature Notes T3 — LLM Memory & Autonomous Agents (Automated Memory Arsitektur)

- Riset: "Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent"
- Tanggal verifikasi: 2026-08-03 (semua metadata dicek langsung ke arXiv/Semantic Scholar/OpenAlex)
- Metode: verifikasi ID arXiv via halaman abs arXiv; venue/DOI via OpenAlex/Semantic Scholar; full text dibaca untuk Generative Agents, MemGPT, Survey 2404.13501, mem0, Zhou et al. 2026; abstract untuk LoCoMo, A-MEM, Santoro, FSFM, SimpleMem, MemoryBank.
- Status: 11 sumber (T3-01 s.d. T3-11); deep round full text mem0 + Zhou selesai 2026-08-03; "MemorySandbox (Zhong et al.)" teridentifikasi kemungkinan = MemoryBank (lihat T3-11).

## Ringkasan koreksi metadata (penting!)

| Item di brief | ID yang disangka | Fakta terverifikasi |
|---|---|---|
| LoCoMo (2401.04959?) | 2401.04959 = "Elephant polynomials" (math, salah) | Paper LoCoMo yang benar: **2402.17753** "Evaluating Very Long-Term Conversational Memory of LLM Agents" (ACL 2024, DOI 10.18653/v1/2024.acl-long.747) |
| mem0 (2411.04965?) | 2411.04965 = "BitNet a4.8" (salah) | Paper mem0 yang benar: **2504.19413** (Chhikara et al., 2025-04-28) |
| "Lifelong Memory for LLMs" (2411.14486?) | 2411.14486 = "The Impossible Test" (salah) | Tidak ada paper berjudul itu di ID tsb; kandidat terdekat: SimpleMem (2601.02553) |
| MemorySandbox / "Memory is All You Need" (2402.04279?) | 2402.04279 = paper fisika "Electrokinetic origin of swirling flow" (salah) | "Memory Is All You Need" yang asli = **2406.08413** (survey CIM hardware, Wolters et al.) — bukan topik agent memory. "MemorySandbox" tidak ditemukan di arXiv/Semantic Scholar/OpenAlex/Google Scholar/web. **Misteri "Zhong et al." terpecahkan: paper Zhong et al. 2024 yang nyata = MemoryBank** (AAAI 2024, arXiv 2305.10250) — sistem memory stream + forgetting berbasis Ebbinghaus, sangat mungkin inilah yang dimaksud brief. A-MEM (2502.12110, NeurIPS 2025) tetap dicatat sebagai pengganti yang disepakati user |

---

## [T3-01] Generative Agents: Interactive Simulacra of Human Behavior
- Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein; 2023; UIST '23 (The 36th Annual ACM Symposium on User Interface Software and Technology, San Francisco, 22 halaman); DOI 10.1145/3586183.3606763; arXiv:2304.03442 (v2, 2023-08-06); https://arxiv.org/abs/2304.03442
- Access: full text (PDF dibaca; ~4965 sitasi per Semantic Scholar, snapshot 2026-08-03)
- Temuan kunci:
  - Arsitektur 3 komponen: **memory stream** (database catatan pengalaman natural language: observasi ber-timestamp creation + last access), **reflection** (sintesis memori ke insight level-tinggi), **planning** (rencana disimpan kembali ke memory stream).
  - **Retrieval scoring**: `score = α_recency·recency + α_importance·importance + α_relevance·relevance` (semua α = 1, dinormalisasi min-max ke [0,1]). Recency = exponential decay faktor **0.995** per jam game sejak akses terakhir; importance = integer 1–10 dihasilkan LLM saat memori dibuat; relevance = cosine similarity embedding memori vs embedding query.
  - Reflection dipicu saat akumulasi importance event terbaru > threshold **150** (~2–3×/hari); insight wajib menyertakan pointer ke memori yang menjadi evidence (citation), membentuk pohon refleksi.
  - Ablasi membuktikan observasi/planning/reflection masing-masing kontributif; error paling umum: gagal me-retrieve memori relevan, embellishment/fabrikasi memori, gaya bicara terlalu formal.
  - Implementasi: 25 agent di dunia sandbox "Smallville", model ChatGPT (gpt-3.5-turbo).
- Keterbatasan: simulasi 2 hari game-time; evaluasi believability via interview, bukan task metrics; biaya LLM tinggi; sandbox The Sims (bukan aplikasi nyata); bias instruksi-tuning pada gaya bahasa.
- Relevansi: fondasi automated memory agent (memory stream + scoring retrieval + konsolidasi via refleksi) — pola yang diadopsi luas oleh sistem memory modern.

## [T3-02] MemGPT: Towards LLMs as Operating Systems
- Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, Joseph E. Gonzalez; 2023 (v1 2023-10-12, v2 2024-02-12); arXiv preprint (UC Berkeley); DOI 10.48550/arXiv.2310.08560; arXiv:2310.08560; https://arxiv.org/abs/2310.08560
- Access: full text (PDF dibaca; ~1019 sitasi per Semantic Scholar, snapshot 2026-08-03)
- Temuan kunci:
  - **Virtual context management**: analogi paging OS — data dipindah antara main context (RAM) dan external context (disk) untuk memberi ilusi konteks tak terbatas.
  - **Memory tiers**: main context = system instructions (read-only) + working context (blok read/write ukuran tetap untuk fakta/preferensi persona) + FIFO queue (riwayat bergulir dengan recursive summary di indeks 0); external context = **recall storage** (database pesan) + **archival storage** (objek teks bebas, vector search via pgvector/HNSW).
  - Queue manager: peringatan "memory pressure" saat prompt > 70% context; flush saat 100% (evict ~50%, generate recursive summary baru). Memory edits & retrieval **self-directed** oleh LLM via function calls; interrupts + function chaining (heartbeat) untuk multi-step retrieval.
  - Hasil Deep Memory Retrieval (task konsistensi lintas sesi, dataset MSC): accuracy GPT-3.5 38.7%→66.9%, GPT-4 32.1%→92.5%, GPT-4 Turbo 35.3%→93.4% dengan MemGPT. Nested KV retrieval (multi-hop): MemGPT+GPT-4 tak terpengaruh kedalaman nesting; baseline 0% di 3 level.
- Keterbatasan: dependensi kemampuan function calling model dasar (degradasi signifikan dengan GPT-3.5); paging berulang bisa mahal; evaluasi pada 2 domain (chat + document QA) dengan dataset sintetis/terbatas; biaya token function call overhead tidak dianalisis mendalam.
- Relevansi: sumber utama konsep **memory tiers + virtual context management + self-editing memory** — dasar desain sistem memory OS-like untuk agent (termasuk pendahulu Letta).

## [T3-03] Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo)
- Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, Yuwei Fang; 2024; ACL 2024 — Proceedings of the 62nd Annual Meeting of the ACL (Volume 1: Long Papers); DOI 10.18653/v1/2024.acl-long.747; arXiv:2402.17753; https://arxiv.org/abs/2402.17753
- Access: abstract + metadata (arXiv & OpenAlex); PDF tidak dibaca penuh
- Temuan kunci:
  - **LoCoMo dataset**: percakapan sangat panjang rata-rata **300 turn / 9K token per percakapan, hingga 35 sesi**; dibuat via pipeline machine-human (agent LLM + persona + temporal event graph, diverifikasi editor manusia).
  - Benchmark: question answering (single-hop, temporal, multi-hop, open-domain), event summarization, multimodal dialogue generation.
  - Temuan evaluasi: LLM (termasuk long-context & RAG) kesulitan memahami percakapan panjang serta dinamika temporal/kausal jarak jauh; long-context LLM & RAG membantu tapi **masih jauh di bawah performa manusia**.
- Keterbatasan: hanya percakapan open-domain sintetis; konteks 300 turn/9K token masih kecil vs percakapan tahunan; baseline model yang dievaluasi (2024) sudah berubah.
- Relevansi: benchmark standar untuk memory jangka sangat panjang; dipakai sebagai tolok ukur oleh mem0, SimpleMem, A-MEM dll — berguna untuk evaluasi "automated memory" pada riset ini. (Catatan: ID 2401.04959 di brief adalah paper matematika; ID benar 2402.17753.)

## [T3-04] Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory
- Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, Deshraj Yadav; 2025 (2025-04-28); arXiv preprint; DOI 10.48550/arXiv.2504.19413; arXiv:2504.19413; https://arxiv.org/abs/2504.19413; kode: https://mem0.ai/research
- Access: **full text** (PDF dibaca 2026-08-03)
- Temuan kunci — arsitektur:
  - **Pipeline 2 fase (incremental)**: (1) **extraction** — input = pasangan pesan (m_{t-1}, m_t) + konteks ganda: summary percakapan S dari database (modul async summary generation memperbarui S periodik tanpa menunda pipeline) + jendela m pesan terbaru; prompt P = (S, {m_{t-m}..m_{t-2}}, m_{t-1}, m_t) → fungsi ekstraksi φ (LLM) menghasilkan set fakta salient Ω. (2) **update** — untuk tiap fakta ω: retrieve top-s=10 memori paling mirip (embeddings dense), lalu LLM via **function calling** memilih 1 dari 4 operasi: **ADD** (buat baru), **UPDATE** (augmentasi memori yang ada), **DELETE** (kontradiksi), **NOOP**. Konfigurasi: m=10 pesan, s=10 memori, inference GPT-4o-mini, vector DB dense embeddings.
  - **Mem0g (varian graph)**: graph berlabel berarah G=(V,E,L); node = entitas (type classification + embedding + timestamp), edge = relasi triplet (v_s, r, v_d); ekstraksi 2 tahap (entity extractor + relationship generator); saat integrasi: pencocokan node via threshold kemiripan t; **conflict detection + LLM update resolver** — relasi yang usang ditandai *invalid* (tidak dihapus fisik) demi temporal reasoning; **dual retrieval**: entity-centric (traversal subgraph dari anchor node) + semantic triplet (query embedding dicocokkan ke embedding triplet); backend Neo4j, GPT-4o-mini.
- Temuan kunci — evaluasi (LOCOMO):
  - Dataset (deskripsi mem0): 10 percakapan, ±600 dialog, ±26.000 token rata-rata, ±200 pertanyaan/percakapan; kategori adversarial dikeluarkan (tanpa ground truth). Catatan: angka ini berbeda dari deskripsi paper LoCoMo asli (±300 turn/9K token, ≤35 sesi) — perlu klarifikasi definisi (turn vs dialog).
  - Baseline 6 kategori: LoCoMo/ReadAgent/MemoryBank/MemGPT/A-Mem (established), LangMem (open-source), RAG (chunk 128–8192, k∈{1,2}), full-context, OpenAI ChatGPT memory, Zep.
  - Hasil: Mem0 terbaik di **single-hop** (F1 38.72, J 67.13) dan **multi-hop** (F1 28.64, J 51.15); Mem0g terbaik di **temporal** (F1 51.55, J 58.13); **open-domain** dimenangkan Zep (J 76.60 vs Mem0g 75.71). Overall J: Mem0g 68.44 tertinggi antar semua metode; full-context 72.90 tapi total p95 latency 17.1s vs Mem0 1.44s (≈92% lebih rendah) dan Mem0g 2.60s.
  - **Efisiensi token**: Mem0 ~7k token/percakapan, Mem0g ~14k, Zep >600k (redundansi summary di tiap node), full conversation ~26k. Search latency: Mem0 p50 0.148s (terendah semua), Mem0g 0.476s, A-Mem 0.668s, LangMem 17.99s (tidak praktis). Konstruksi graph Mem0 < 1 menit; Zep gagal retrieval sesaat setelah write (perlu jam — proses background async).
  - Klaim penutup: 5%/11%/7% improvement relatif (single-hop/temporal/multi-hop) vs metode terbaik per kategori; p95 latency turun >91% vs full-context.
- Keterbatasan: preprint; evaluasi mandiri (risiko bias); semua eksperimen GPT-4o-mini (satu backbone); kategori adversarial LoCoMo dihilangkan; klaim "26% relatif vs OpenAI" di abstract tidak tampak konsisten dengan angka J tabel (perlu perhitungan ulang); graph memory justru menurun di single-/multi-hop (overhead); dataset LOCOMO tidak dirilis penuh untuk kategori adversarial.
- Relevansi: contoh operasional lengkap pola extract→consolidate (ADD/UPDATE/DELETE/NOOP)→retrieve + varian graph; angka latency/token menjadi pembanding desain "automated memory" riset ini. (Catatan: ID 2411.04965 di brief = BitNet; ID benar 2504.19413.)

## [T3-05] A-MEM: Agentic Memory for LLM Agents (pengganti "MemorySandbox" yang tidak ditemukan)
- Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang; 2025 (v1 2025-02-17, v11 2025-10-08); **NeurIPS 2025** (Advances in Neural Information Processing Systems; venue terverifikasi dari halaman abs arXiv); arXiv:2502.12110; DOI 10.48550/arXiv.2502.12110; https://arxiv.org/abs/2502.12110
- Access: abstract (dari halaman abs arXiv, diverifikasi ulang 2026-08-03); PDF belum dibaca
- Temuan kunci:
  - Memory agentic berbasis metode **Zettelkasten**: setiap memori baru dibuat sebagai note dengan atribut terstruktur (contextual descriptions, keywords, tags); sistem menganalisis memori historis untuk **dynamic indexing & linking** (jaringan pengetahuan saling terhubung); integrasi memori baru dapat **memperbarui representasi kontekstual & atribut memori lama** (memory evolution → jaringan memori menyempurna terus).
  - Keunggulan klaim: organisasi memori adaptif vs sistem dengan operasi/struktur tetap (termasuk graph database); superior vs SOTA baseline pada enam foundation model.
  - Kode: https://github.com/WujiangXu/A-mem (evaluasi) dan https://github.com/WujiangXu/A-mem-sys (sistem).
- Keterbatasan: abstract tidak mencantumkan angka kuantitatif; "agentic" di sini = keputusan organisasi memori oleh LLM, bukan memori yang belajar dari RL; evaluasi pada 6 foundation model (2025), bukan di benchmark panjang seperti LoCoMo.
- Relevansi: pola organisasi memori adaptif (linking + evolution) — alternatif desain untuk modul konsolidasi memory. (Catatan verifikasi: "MemorySandbox" (Zhong et al.) TIDAK ditemukan di arXiv/Semantic Scholar/OpenAlex/Google Scholar/web search; kandidat terdekat adalah paper ini. "Memory Is All You Need" yang asli — 2406.08413, Wolters et al. 2024 — adalah survey **hardware compute-in-memory**, bukan arsitektur memory agent, jadi tidak relevan untuk T3.)

## [T3-06] Are We Ready For An Agent-Native Memory System?
- Wei Zhou, Xuanhe Zhou, Shaokun Han, Hongming Xu, Guoliang Li, Zhiyu Li, Feiyu Xiong, Fan Wu; 2026 (2026-06-23); arXiv preprint; arXiv:2606.24775 (cs.CL, cs.DB, cs.IR); https://arxiv.org/abs/2606.24775; kode: https://github.com/OpenDataBox/MemoryData (taxonomy: https://github.com/OpenDataBox/awesome-agent-memory)
- Access: **full text** (PDF dibaca 2026-08-03)
- Temuan kunci — kerangka & taksonomi:
  - Sistem memory formal sebagai tuple 4 modul: **M_sys = ⟨R, S, Q, U⟩** — (R) Memory Representation & Storage: logical representation (token-level sequence — explicit text / implicit vector; graph & tree topology — temporal KG, hierarchical tree; heterogeneous composite) + physical storage (transient in-context register, single-engine: vector/graph/relational/file, multi-engine); (S) Extraction: raw sequence concatenation / schema-free semantic / schema-constrained structured; (Q) Retrieval & Routing: native attention / semantic dense KNN / topological subgraph traversal / autonomous agentic routing (function call, generative query expansion) / multi-stage hybrid (sequential, parallel ensemble); (U) Maintenance: timestamp-based multi-versioning (invalidasi logis, append-only), capacity-driven physical eviction (constraint-based FIFO/token, score-based decay/heat), LLM-driven semantic consolidation (inline compaction, tool-driven CRUD), continuous parametric optimization (offline training).
  - Taksonomi 14 sistem: MemoChat, Mem0, MEM1, MemAgent, MemTree, Zep, Mem0g, Cognee, LightMem, SimpleMem, MemOS, MemoryOS, A-MEM, Letta; distingsi dari RAG (stateless read-only) dan context engineering.
- Temuan kunci — evaluasi end-to-end (12 sistem + 2 baseline: Long Context, Embedding RAG; 5 workloads/11 dataset: LoCoMo, LongMemEval via MemoryAgentBench, DB-Bench dari LifelongAgentBench, LongBench, dll):
  - **Finding 1 (Workload-Aligned Memory)**: tidak ada arsitektur dominan; Zep 48.0 LLM Judge Accuracy di LongMemEval, Cognee 35.3 ROUGE-L F1; MemOS 11.5 EM di LoCoMo; Long Context 48.20 EM di DB-Bench; MemoChat 55.4 Task Success Rate; MemoryOS & MemOS paling dekat frontier. **Baseline Long Context (tanpa memory) sering kompetitif bahkan menang** (DB-Bench).
  - **Finding 2 (Evidence-Centric Memory Organization)**: retrieval = masalah *evidence completion*, bukan top-1 ranking; SimpleMem Recall@1 tertinggi 39.0 tapi A-MEM 69.5/85.9 dan MemTree 59.7/80.5 di Recall@5/@10; Embedding RAG drop tajam saat evidence distance gap membesar (37.1→7.4 Ans F1).
  - **Finding 3 (Temporal Update Fidelity)**: revisability harus dibangun di representasi (binding entitas/event, bukan append teks); graph/organized memory paling andal menangani update (Zep 44.4 Substr EM di Knowledge Update; Cognee 18.7 di Temporal Reasoning); append-only store & fact-extraction plugin lemah pada targeted overwrites → stale facts → **"hallucinations of the past"**; backbone scaling hanya membantu setelah grounding berhasil (MemOS konsisten terkuat di 4 backbone: 32.2–41.2).
  - **Finding 4 (Horizon-Structured Memory)**: horizon panjang → masalahnya pemilihan abstraksi, bukan volume; LongBench: SimpleMem stabil Short→Medium (35.2→34.9) vs Long Context drop (42.6→19.0); raw long-context unggul untuk query time-dependent karena konsolidasi semantik merusak chronological cues.
  - **Finding 5 (Operational Scaling Rule)**: efisiensi ditentukan **scope maintenance**, bukan struktur: localized maintenance (LightMem 48.3 utility @ 3.67s, MemTree 63.5 @ 15.9s) vs whole-memory coordination (Cognee >84 @ 116.5s, Zep >84 @ 155.1s; LongBench: Mem0 374s, A-MEM 552s); Mem0 21.4 utility @ 35.9s.
- Temuan kunci — ablasi per modul (M1–M4):
  - **M1 (Finding 6, Representasi)**: retensi konten > abstraksi; LightMem User-Only Raw terbaik di semua metrik (LoCoMo EM 24.2/Ans F1 38.9; LongMemEval Substr EM 26.0); summary abstraktif anjlok (8.5/15.6); kompresi ringan menjaga reasoning tapi melemahkan exact match; hierarki menambah akses tapi tidak memulihkan konten hilang.
  - **M2 (Finding 7, Late Filtering)**: ekstraksi konservatif/coverage-preserving lebih baik; MemOS Fast Memorize 25.5 vs Fine Memorize 2.5 EM (LoCoMo); heuristic topic > LLM topic; menyimpan turn user+assistant membantu.
  - **M3 (Finding 8)**: hybrid balanced fusion > sparse-leaning (A-MEM 24.6 vs 23.0); lightweight planning membantu (SimpleMem Planning Only 20.7/90.6 vs No Planning 18.7/86.4); refleksi tambahan di atas planning **tidak membantu** (20.0) — overhead.
  - **M4 (Finding 9, Konservatif > agresif)**: Conservative-Merge 23.5 vs default 23.2 vs Delayed-Flush 20.6 (Ans F1, MemoryOS); single-topic forced summary melemah; raw context tetap terbaik untuk exact phrasing (23.7 Substr EM).
- Keterbatasan: preprint; evaluasi terpusat di benchmark NLP (LoCoMo/LongMemEval/LongBench — DB-Bench terbatas); angka memakai EM/ROUGE yang bisa meremehkan sistem jawaban berbentuk bebas; 12 sistem versi 2025–2026 (dapat berubah cepat); metrik "Normalized Utility" definisi internal.
- Relevansi: **kerangka 4 modul + 9 findings + 11 observation ini adalah peta desain terbaik untuk arsitektur automated memory riset ini** — memberi panduan konkret (retensi konten, konservatif consolidation, localized maintenance, struktur untuk evidence jauh) dan amunisi kritik terhadap evaluasi black-box.

## [T3-07] One-shot Learning with Memory-Augmented Neural Networks
- Adam Santoro, Sergey Bartunov, Matthew Botvinick, Daan Wierstra, Timothy Lillicrap; 2016; arXiv preprint 2016-05-19; versi konferensi: "Meta-Learning with Memory-Augmented Neural Networks", ICML 2016 (PMLR v48, proceedings.mlr.press/v48/santoro16.pdf; ~1252 sitasi per OpenAlex); arXiv:1605.06065; https://arxiv.org/abs/1605.06065
- Access: abstract + metadata (arXiv & OpenAlex); PDF tidak dibaca penuh
- Temuan kunci:
  - MANN (berbasis Neural Turing Machine): external memory memungkinkan **fast encoding & retrieval informasi baru** tanpa retrain parameter (mengatasi catastrophic interference pada one-shot learning).
  - Kontribusi utama: metode akses external memory yang **content-based** (fokus pada isi memori), berbeda dari pendekatan sebelumnya yang menambah location-based focusing.
- Keterbatasan: era pra-LLM (2016); skala kecil; representasi vektor, bukan natural language; tidak membahas retrieval scoring berbasis waktu/pentingnya.
- Relevansi: fondasi historis "memory-augmented" yang menginspirasi tier memory & external memory pada sistem LLM modern; pembanding evolusi dari memory vektor ke memory teks.

## [T3-08] A Survey on the Memory Mechanism of Large Language Model based Agents
- Zeyu Zhang, Xiaohe Bo, Chen Ma, Rui Li, Xu Chen, Quanyu Dai, Jieming Zhu, Zhenhua Dong, Ji-Rong Wen; 2024 (2024-04-21); arXiv preprint ("Preprint, under review"); 39 halaman; arXiv:2404.13501; https://arxiv.org/abs/2404.13501
- Access: full text (sebagian besar dibaca; repository: github.com/nuster1128/LLM_Agent_Memory_Survey)
- Temuan kunci:
  - Survey pertama (klaim penulis) tentang memory mechanism agent LLM; definisi memory sempit (dalam satu trial) vs luas (lintas trial + external knowledge).
  - Taksonomi implementasi 3 dimensi: **memory sources** (inside-trial, cross-trial, external knowledge), **memory forms** (textual vs parametric), **memory operations** — writing W, management P (reflection/abstraksi, merging, **forgetting**), reading R; formulasi unifikasi: `a_{t+1} = LLM{ R( P( M_{t-1}, W({a_t,o_t}) ), c_{t+1} ) }`.
  - Evaluasi: direct (subjective/objective) & indirect (conversation, multi-source QA, long-context apps); aplikasi: role-play, social simulation, personal assistant, game, code generation, recommendation, expert system; future directions: parametric memory, memory multi-agent, **memory-based lifelong learning**.
- Keterbatasan: preprint 2024 (usang untuk sistem 2025–2026: belum mencakup mem0, A-MEM, AgeMem, dsb); taksonomi berbasis sistem pra-2024; depth per-sistem terbatas.
- Relevansi: kerangka kerja untuk memposisikan desain modul memory riset ini (sumber/bentuk/operasi) dan memetakan sistem yang sudah diverifikasi di notes ini.

## [T3-09] FSFM: A Biologically-Inspired Framework for Selective Forgetting of Agent Memory
- Yingjie Gu, Wenjian Xiong, Liqiang Wang, Pengcheng Ren, Chao Li, Xiaojing Zhang, Yijuan Guo, Qi Sun, Jingyao Ma, Shidang Shi; 2026 (2026-04-22); arXiv preprint; arXiv:2604.20300; https://arxiv.org/abs/2604.20300
- Access: abstract
- Temuan kunci:
  - Argumen: **selective forgetting** (terinspirasi hippocampal indexing/consolidation theory + Ebbinghaus forgetting curve) sama pentingnya dengan remembering; taksonomi mekanisme lupa: **passive decay-based, active deletion-based, safety-triggered, adaptive reinforcement-based**.
  - Manfaat 3 dimensi: efisiensi (intelligent memory pruning), kualitas (update preferensi/konteks usang), keamanan (lupa input malicious, data sensitif).
  - Hasil eksperimen: access efficiency +8.49%, content quality +29.2% signal-to-noise ratio, 100% eliminasi risiko keamanan.
- Keterbatasan: preprint; angka dari eksperimen terkontrol sendiri; definisi "safety-triggered forgetting" perlu detail full text; belum ada benchmark standar untuk forgetting.
- Relevansi: menjawab sisi **memory decay/forgetting** yang jarang dibahas — penting untuk modul maintenance/retention policy pada automated memory (hindari memory store tumbuh tak terkendali).

## [T3-10] SimpleMem: Efficient Lifelong Memory for LLM Agents (bonus — "lifelong memory")
- Jiaqi Liu, Yaofeng Su, Peng Xia, Siwei Han, Zeyu Zheng, Cihang Xie, Mingyu Ding, Huaxiu Yao; 2026 (2026-01-05); arXiv preprint; DOI 10.48550/arXiv.2601.02553; arXiv:2601.02553
- Access: abstract (via Semantic Scholar)
- Temuan kunci: pipeline 3 tahap — Semantic Structured Compression (distilasi interaksi ke memory units multi-view), Online Semantic Synthesis (integrasi intra-sesi), Intent-Aware Retrieval Planning; klaim: +26.4% F1 rata-rata di LoCoMo, pengurangan token inferensi hingga 30×.
- Keterbatasan: preprint; angka dari evaluasi sendiri; fokus efisiensi token, belum memori multimodal/prosedural.
- Relevansi: opsi desain "lifelong memory" ringkas untuk research agent yang hemat token. (Catatan: ID "Lifelong Memory for LLMs 2411.14486" di brief tidak valid — paper itu adalah "The Impossible Test".)

---

## [T3-11] MemoryBank: Enhancing Large Language Models with Long-Term Memory (identitas asli "MemorySandbox (Zhong et al.)")
- Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, Yanlin Wang; 2023 (arXiv v1 2023-05-17, v3 2023-05-21); diterbitkan di **AAAI 2024**, pp. 19724–19731 (per daftar pustaka Zhou et al. 2026); arXiv:2305.10250; https://arxiv.org/abs/2305.10250
- Access: abstract (arXiv); PDF belum dibaca
- Temuan kunci:
  - Mekanisme memory jangka panjang untuk LLM: menyimpan memori relevan, **terus berevolusi via continuous memory updates**, memahami kepribadian user dari interaksi lampau.
  - **Memory updating mechanism terinspirasi Ebbinghaus Forgetting Curve**: AI dapat *lupa dan memperkuat* memori berdasarkan waktu berlalu + signifikansi relatif — implementasi early dari memory decay/forgetting berbasis kurva lupa.
  - Aplikasi: chatbot **SiliconFriend** (skenario AI companion jangka panjang); kompatibel ChatGPT & ChatGLM; evaluasi kualitatif (dialog user nyata) + kuantitatif (dialog simulasi; ChatGPT sebagai user berkarakter beragam).
- Keterbatasan: era pra-produksi (2023); evaluasi pada companion scenario; klasifikasi signifikansi memori bergantung prompt LLM; bukan benchmark standar (belum LoCoMo).
- Relevansi: **menjawab misteri brief**: "MemorySandbox (Zhong et al.)" kemungkinan besar adalah paper ini (satu-satunya paper memory agent 2024 berpenulis Wanjun Zhong yang ditemukan); sekaligus sumber rujukan memory decay berbasis Ebbinghaus yang lebih mapan daripada FSFM (preprint 2026). Catatan: pengguna menyepakati A-MEM sebagai pengganti "MemorySandbox"; MemoryBank dicatat di sini sebagai kandidat identitas asli + sumber forgetting.

---

## Keterbatasan round riset ini
- Full text dibaca untuk: Generative Agents, MemGPT, Survey 2404.13501, mem0, Zhou et al. 2026 (5 sumber). Abstract-only: LoCoMo, A-MEM, Santoro, FSFM, SimpleMem, MemoryBank (6 sumber) — klaim kuantitatif di dalamnya belum divalidasi lewat full text.
- Deskripsi dataset LOCOMO tidak konsisten antar sumber: LoCoMo paper (300 turn/9K token, ≤35 sesi) vs mem0 paper (±600 dialog/26K token) — perlu klarifikasi definisi unit (turn vs dialog) saat menulis BAB metode.
- Mem0 & Zhou mengevaluasi di testbed berbeda: mem0 klaim SOTA di metrik J (LLM-as-Judge), Zhou (EM/ROUGE) justru menempatkan Mem0 rendah (LoCoMo EM 4.1; LongMemEval Judge 16.7) — konflik metodologis yang harus dijelaskan di sintesis akhir.
- Jumlah sitasi adalah snapshot (Semantic Scholar/OpenAlex, 2026-08-03) dan dapat berubah.
- Tidak ada sumber konferensi peer-review untuk mem0, FSFM, SimpleMem, Zhou 2026 (preprint); A-MEM = NeurIPS 2025 (terverifikasi), MemoryBank = AAAI 2024.

## Rekomendasi pencarian berikutnya
1. (Sudah dilakukan round ini) Baca full text mem0 (2504.19413) & Zhou (2606.24775) — selesai, catatan diperbarui.
2. Baca full text MemoryBank (2305.10250) untuk detail forgetting curve (relevan untuk modul retention policy) dan konfirmasi ke penulis brief apakah "MemorySandbox" = MemoryBank.
3. Survey 2025–2026 yang ditemukan via daftar pustaka Zhou: Du 2026 "Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers" (2603.07670); Hu et al. 2025 "Memory in the Age of AI Agents" (2512.13564); Tang et al. 2026 "LLM Agent Memory: A Survey from a Unified Representation" (2603.0359) — pilih 1–2 untuk memperbarui taksonomi 2024.
4. Benchmark tambahan: LongMemEval (2410.10813) dan MemoryAgentBench (ICLR 2026) sebagai pembanding evaluasi di luar LoCoMo.
5. Cek Zep (2501.13956, temporal KG) sebagai pembanding sistem memory komersial yang menang di open-domain/temporal.
