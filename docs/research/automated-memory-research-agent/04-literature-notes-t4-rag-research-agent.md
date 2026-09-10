# Literature Notes T4 — RAG, Graph RAG, Knowledge Graph, Research Agents

Topik riset: Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent
Sub-topik: T4 — Retrieval-Augmented Generation (RAG), Graph RAG, knowledge graph, research agents
Peneliti: topic-researcher T4
Tanggal akses: 2026-08-03
Metode verifikasi: arXiv API resmi (export.arxiv.org), full text PDF (2 paper), OpenAlex API
Status metadata: semua arXiv ID diverifikasi langsung ke API arXiv (bukan dari ingatan)

---

## [T4-01] Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- Penulis: Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela
- Tahun: 2020. Venue: NeurIPS 2020 (dikonfirmasi dari field "comment" arXiv API: "Accepted at NeurIPS 2020"). arXiv: 2005.11401v4. URL: https://arxiv.org/abs/2005.11401
- Access: abstract (arXiv API); full text tersedia di https://arxiv.org/pdf/2005.11401
- Temuan kunci: Memperkenalkan RAG — model yang menggabungkan parametric memory (seq2seq pre-trained) dan non-parametric memory (dense vector index Wikipedia via neural retriever). Dua formulasi: RAG-Sequence (pasase sama untuk seluruh sequence) vs RAG-Token (pasase berbeda per token). Mencapai state-of-the-art pada tiga open-domain QA tasks, mengungguli parametric seq2seq dan arsitektur task-specific retrieve-and-extract. Pada language generation, RAG menghasilkan bahasa yang lebih spesifik, diverse, dan faktual dibanding baseline seq2seq parametric-only. Memotivasi provenance dan update knowledge yang masih jadi masalah terbuka.
- Keterbatasan: Evaluasi pada era pre-LLM (BART-family); non-parametric memory statis (Wikipedia dump); retrieval bergantung DPR; tidak membahas agentic workflow.
- Relevansi: Fondasi arsitektur RAG yang dipakai seluruh paper lanjutan (Graph RAG, Agentic RAG, RAG untuk literature review). Konsep parametric+non-parametric memory relevan dengan "automated memory" pada sistem target.

## [T4-02] From Local to Global: A Graph RAG Approach to Query-Focused Summarization
- Penulis: Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan Larson (Microsoft Research dkk.)
- Tahun: 2024. Venue: preprint arXiv (tidak ada field venue resmi di arXiv API; open-source di github.com/microsoft/graphrag). arXiv: 2404.16130v2 (update 2025-02-19). URL: https://arxiv.org/abs/2404.16130
- Access: FULL TEXT (PDF dibaca penuh)
- Temuan kunci: RAG vektor gagal pada global/sensemaking questions ("apa tema utama korpus?") karena itu tugas query-focused summarization (QFS). GraphRAG membangun graph index dua tahap dengan LLM: (1) entity knowledge graph dari dokumen sumber, (2) community summaries yang di-generate bottom-up dari hierarki komunitas (Leiden community detection). Saat query: map-reduce — tiap community summary menghasilkan partial response, lalu di-reduce menjadi global answer. Evaluasi LLM-as-a-judge dengan kriteria Comprehensiveness, Diversity, Empowerment + kontrol Directness (bukan "loyalty" — lihat catatan koreksi). Hasil (vs vector RAG): comprehensiveness win rate 72–83% (Podcast, p<.001) dan 72–80% (News, p<.001); diversity win rate 75–82% (Podcast) dan 62–71% (News). Validasi berbasis klaim (Claimify, 47.075 klaim unik): semua kondisi global > vector RAG dalam jumlah klaim (SS 25.23/26.50 vs C0–C3 31–34). C0 (root summaries) hemat token 9x–43x per query. Ukuran graph: Podcast 8.564 node/20.691 edge; News 15.754 node/19.520 edge.
- Keterbatasan: Hanya 2 korpus ~1 juta token; tanpa ground truth — memakai LLM-as-a-judge + statistik klaim; belum ada analisis fabrication rate (mis. SelfCheckGPT); indexing butuh biaya LLM besar (281 menit untuk Podcast dengan gpt-4-turbo); evaluasi terbatas pada pertanyaan global, bukan retrieval lokal.
- Relevansi: Template GraphRAG (entity KG + community summaries + map-reduce) sangat relevan untuk knowledge graph pada knowledge base pembelajaran adaptif; hasil kuantitatif comprehensiveness/diversity jadi dasar klaim perbandingan Graph RAG vs RAG biasa.

## [T4-03] Retrieval-Augmented Generation for Large Language Models: A Survey
- Penulis: Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, Meng Wang, Haofen Wang
- Tahun: 2023 (arXiv 2312.10997v5, update 2024-03-27). Venue: preprint arXiv (comment API: "Ongoing Work"). DOI (OpenAlex): 10.48550/arxiv.2312.10997. URL: https://arxiv.org/abs/2312.10997
- Access: FULL TEXT (PDF dibaca penuh). Sitasi (OpenAlex, 2026-08-03): ~691
- Temuan kunci: Memetakan 3 paradigma RAG: Naive RAG (indexing → retrieval → generation), Advanced RAG (menambahkan strategi pre-retrieval dan post-retrieval), Modular RAG (modul search/memory/routing/predict/task adapter; pola iterative & adaptive retrieval, mis. FLARE, Self-RAG). Kerangka tripartit: Retrieval, Generation, Augmentation. Pre-retrieval = optimasi indexing (chunking, metadata, structural/KG index) + query optimization (expansion, rewriting, routing, HyDE); post-retrieval = reranking + context selection/compression (LLMLingua, RECOMP). Survey meninjau >100 studi, mencakup 26 task dan hampir 50 dataset evaluasi. Diskusi RAG vs fine-tuning: RAG unggul untuk knowledge update real-time; FT untuk adaptasi gaya.
- Keterbatasan: Survey (bukan eksperimen); taksonomi berubah cepat mengikuti literatur; angka evaluasi bersifat deskriptif atas benchmark yang ada.
- Relevansi: Kerangka tahapan RAG (pre-retrieval/retrieval/post-retrieval/generation) yang dipakai sebagai struktur taksonomi di makalah utama; modul "Memory" pada Modular RAG relevan dengan automated memory.

## [T4-04] Automated Literature Review Using NLP Techniques and LLM-Based Retrieval-Augmented Generation
- Penulis: Nurshat Fateh Ali, Md. Mahdi Mohtasim, Shakil Mosharrof, T. Gopi Krishna
- Tahun: 2024. Venue: preprint arXiv (comment API berisi keywords saja, tanpa venue). arXiv: 2411.18583v1 (2024-11-27). URL: https://arxiv.org/abs/2411.18583
- Access: abstract (arXiv API); full text tersedia
- Temuan kunci (dari abstract): Membandingkan 3 pendekatan otomatisasi literature review dari input PDF: frequency-based (spaCy), transformer (Simple T5), dan RAG + LLM (GPT-3.5-turbo), diuji pada dataset SciTLDR dengan metrik ROUGE. GPT-3.5-turbo mencapai ROUGE-1 tertinggi 0.364; transformer kedua; spaCy terakhir. GUI dibangun untuk sistem terbaik (LLM-based).
- Keterbatasan: Dataset kecil/domain tunggal (SciTLDR); evaluasi hanya ROUGE (n-gram overlap), tidak mengukur kesahihan fakta; satu model LLM diuji; preprint tanpa peer review.
- Relevansi: Bukti langsung penerapan RAG untuk riset otomatis (automated literature review) — komponen "research agent" pada sistem target; angka ROUGE-1 0.364 bisa jadi baseline perbandingan.

## [T4-05] Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG
- Penulis: Aditi Singh, Abul Ehtesham, Saket Kumar, Tala Talaei Khoei, Athanasios V. Vasilakos
- Tahun: 2025 (arXiv 2501.09136v4, update 2026-04-01). Venue: preprint arXiv (tanpa field venue). URL: https://arxiv.org/abs/2501.09136
- Access: abstract (arXiv API); full text tersedia
- Temuan kunci: Agentic RAG menyematkan autonomous agents ke pipeline RAG dengan design pattern: reflection, planning, tool use, multi-agent collaboration. Taksonomi arsitektur berdasarkan agent cardinality, control structure, autonomy, dan knowledge representation. RAG tradisional statis tidak adaptif untuk multi-step reasoning; Agentic RAG mengelola strategi retrieval dinamis, refinement kontekstual iteratif, dan workflow dari sequential sampai adaptive collaboration. Aplikasi: healthcare, finance, education, enterprise document processing. Mengidentifikasi open research challenges.
- Keterbatasan: Survey konseptual; tidak ada benchmark/angka evaluasi; ekosistem cepat berubah; preprint.
- Relevansi: Jembatan konseptual RAG → research agent multi-agent; aplikasi "education" disebut eksplisit; pola planning/tool-use menjadi dasar desain research agent pada sistem target.

## [T4-06] The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery
- Penulis: Chris Lu, Cong Lu, Robert Tjarko Lange, Jakob Foerster, Jeff Clune, David Ha
- Tahun: 2024 (arXiv 2408.06292v3, update 2024-09-01). Venue: preprint arXiv (tanpa field venue). URL: https://arxiv.org/abs/2408.06292
- Access: abstract (arXiv API); full text tersedia
- Temuan kunci (dari abstract): Framework pertama untuk scientific discovery otomatis penuh: frontier LLM menghasilkan ide riset, menulis kode, menjalankan eksperimen, memvisualisasi hasil, menulis paper ilmiah, lalu menjalankan simulated review process. Berulang secara open-ended. Diterapkan pada 3 subfield ML (diffusion modeling, transformer language modeling, learning dynamics). Biaya <$15 per paper. Automated reviewer divalidasi mendekati performa manusia dalam menilai paper; paper yang dihasilkan melewati acceptance threshold top ML conference menurut automated reviewer.
- Keterbatasan: Preprint (belum peer review venue); evaluasi memakai automated reviewer sendiri (self-assessment), belum konfirmasi acceptance nyata; hasil di subfield ML terbatas; klaim biaya bergantung harga API.
- Relevansi: Varian "research agent" otonom; menjadi state of the art untuk bab riset-otomatis; keterbatasan evaluasinya menguatkan pentingnya evaluasi grounded (mis. dengan retrieval/evidence).

## [T4-07] BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models
- Penulis: Nandan Thakur, Nils Reimers, Andreas Rücklé, Abhishek Srivastava, Iryna Gurevych
- Tahun: 2021. Venue: NeurIPS 2021 Dataset and Benchmark Track (dikonfirmasi field "comment" arXiv API). arXiv: 2104.08663v4. URL: https://arxiv.org/abs/2104.08663
- Access: abstract penuh (arXiv API); full text tersedia
- Temuan kunci (dari abstract): Benchmark IR heterogen: 18 dataset dari beragam task/domain; mengevaluasi 10 sistem retrieval (lexical, sparse, dense, late-interaction, re-ranking). Hasil: BM25 baseline yang robust; re-ranking dan late-interaction rata-rata terbaik zero-shot namun komputasi mahal; dense/sparse retrieval efisien tapi sering di bawah, menyisakan ruang perbaikan generalisasi. Termasuk metrik standard retrieval (nDCG, recall) sebagai acuan evaluasi precision/recall.
- Keterbatasan: Fokus zero-shot IR (retrieval stage), bukan end-to-end RAG; dataset 2021 (beberapa usang); tidak mencakup evaluasi generation/faithfulness.
- Relevansi: Acuan evaluasi kualitas retrieval (precision/recall, zero-shot generalization) untuk komponen retrieval pada sistem pembelajaran adaptif; mendukung klaim "retrieval harus dievaluasi terpisah dari generation".

## [T4-08] Leveraging Graph Retrieval-Augmented Generation to Support Learners' Understanding of Knowledge Concepts in MOOCs
- Penulis: Mohamed Abdelmagied, Mohamed Amine Chatti, Shoeb Joarder, Qurat Ul Ain, Rawaa Alatrash
- Tahun: 2025. Venue: EMOOCs 2025 (dikonfirmasi field "comment" arXiv API: "Accepted at EMOOCs 2025"). arXiv: 2505.10074v2. URL: https://arxiv.org/abs/2505.10074
- Access: abstract penuh (arXiv API); full text tersedia
- Temuan kunci (dari abstract): Graph RAG pipeline yang memakai Educational Knowledge Graphs (EduKGs) dan Personal Knowledge Graphs (PKGs) untuk membimbing pemahaman konsep di MOOC platform CourseMapper. Dua komponen: (1) PKG-based Question Generation untuk rekomendasi pertanyaan personalisasi kontekstual; (2) EduKG-based Question Answering yang memanfaatkan relasi antar konsep untuk menjawab pertanyaan pilihan learner. Evaluasi: 3 expert instructors pada 3 MOOC berbeda; hasil menunjukkan potensi Graph RAG untuk pengalaman belajar personal.
- Keterbatasan: Evaluasi dengan ahli (kecil, n=3 instructor, 3 MOOC); studi persepsi/kelayakan, belum ada metrik pembelajaran kuantitatif; platform spesifik (CourseMapper).
- Relevansi: Paper kunci untuk "knowledge graph pendidikan": kombinasi langsung Graph RAG + EduKG + PKG + personalisasi — sangat dekat dengan sistem target (adaptive learning + memory personal).

## [T4-09] Inferring Prerequisite Knowledge Concepts in Educational Knowledge Graphs: A Multi-criteria Approach
- Penulis: Rawaa Alatrash, Mohamed Amine Chatti, Nasha Wibowo, Qurat Ul Ain
- Tahun: 2025. Venue: IJCKG 2025 (dikonfirmasi field "comment" arXiv API: "Accepted at IJCKG 2025"). arXiv: 2509.05393v1. URL: https://arxiv.org/abs/2509.05393
- Access: abstract penuh (arXiv API); full text tersedia
- Temuan kunci (dari abstract): Prerequisite relationships (PR) penting untuk urutan belajar adaptif, tapi sulit dianotasi manual. Metode unsupervised inferensi PR dengan 10 kriteria (document-based, Wikipedia hyperlink-based, graph-based, text-based) digabung voting algorithm. Hasil: precision lebih tinggi dari metode existing, tetap scalable, mendukung sequence-aware learning di CourseMapper.
- Keterbatasan: Fokus inferensi PR (satu jenis relasi); validasi pada benchmark + platform sendiri; belum menguji dampak pada hasil belajar.
- Relevansi: Mendukung desain knowledge graph untuk adaptasi urutan konsep (prerequisite) — langsung berkaitan dengan adaptive learning loop pada sistem target.

---

## Catatan koreksi terhadap brief
1. Brief menyebut Graph RAG (T4-02) melaporkan "answer comprehensiveness/loyalty". Fakta dari full text v2: kriteria evaluasi adalah Comprehensiveness, Diversity, Empowerment, dan Directness (kontrol). Kata "loyalty" TIDAK muncul sebagai kriteria di paper ini. Jangan mengutip "loyalty" untuk Edge et al. 2024.
2. Brief menyebut tahapan RAG Gao et al. sebagai "pre-retrieval, retrieval, post-retrieval, generation". Fakta dari full text: Naive RAG = indexing–retrieval–generation; Advanced RAG menambahkan optimasi pre-retrieval (indexing & query) dan post-retrieval (rerank & context compression); survey juga memetakan paradigma Modular RAG dan tripartit retrieval–generation–augmentation.

## Sumber diverifikasi namun tidak dipakai di catatan inti (tidak ada klaim)
- OpenAlex menghubungkan Gao et al. ke DOI arXiv 10.48550/arxiv.2312.10997; versi jurnal IEEE TKDE tidak diverifikasi di sesi ini (jangan dikutip tanpa verifikasi).
- Semantic Scholar API rate-limited (HTTP 429) saat sesi ini; jumlah sitasi hanya tersedia untuk Gao survey via OpenAlex (~691).

## Gap / saran pencarian lanjutan
- Perlu verifikasi versi jurnal Gao et al. (IEEE TKDE 2024?) jika ingin mencantumkan venue jurnal.
- Paper "loyalty" pada Graph RAG (mis. evaluasi faithfulness GraphRAG) perlu dicari terpisah jika klaim tersebut dibutuhkan.
- ChemCrow (autonomous chemistry agent) belum diverifikasi — kandidat tambahan untuk research agent domain science.
