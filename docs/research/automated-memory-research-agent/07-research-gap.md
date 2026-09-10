# 07 — Research Gap

Tanggal: 2026-08-03. Berbasis sintesis 63 sumber terverifikasi (03-source-matrix.csv).

## 1. Konsensus literatur (yang sudah mapan)
1. Retrieval practice + distributed practice = teknik belajar paling efektif (Dunlosky et al., 2013; Karpicke & Roediger, 2008; Agarwal et al., 2021) — namun efek bervariasi per domain dan kondisi (Murray et al., 2025; Hinze & Rapp, 2014).
2. Penjadwalan ulasan adalah masalah optimasi yang dapat diformalkan (Reddy et al., 2016; Ye et al., 2022/FSRS; Settles & Meeder, 2016/HLR) — model trainable mengungguli heuristik tetap (SM-2).
3. ITS efektif dengan effect size moderat (VanLehn d=0.76; Ma g=0.42–0.57; Steenbergen-Hu g=0.32–0.37; Kulik & Fletcher 0.66 SD), sensitif terhadap jenis pengukuran (Xu et al., 2019).
4. Arsitektur memory agent LLM sudah matang: memory stream + reflection (Park et al., 2023), virtual context management (MemGPT, 2023), pipeline extract-update ADD/UPDATE/DELETE (mem0, 2025), kerangka M_sys=<R,S,Q,U> + 9 findings desain (Zhou et al., 2026).
5. RAG/GraphRAG efektif untuk knowledge-grounded answer (Lewis et al., 2020; Edge et al., 2024; Gao et al., 2023); agentic RAG dan riset otomatis mulai mapan (Singh et al., 2025; Ali et al., 2024; Lu et al., 2024).

## 2. Gap yang diisi riset ini
| # | Gap | Bukti gap | Kontribusi yang diusulkan |
|---|---|---|---|
| G1 | Belum ada arsitektur yang mengintegrasikan **penjadwalan memori berbasis model kognitif (FSRS/HLR)** dengan **memory layer agent LLM** dalam satu sistem pembelajaran adaptif. Literatur memori agent (mem0, MemGPT, A-MEM) tidak menyentuh learning science; literatur spacing (FSRS, HLR) tidak memakai agent memory. | Catatan T3 vs T1/T2; Zhou et al. (2026) tidak membahas spaced repetition; Ye et al. (2022) tidak membahas agent/LLM. | Arsitektur **Automated Memory Manager** dengan scheduler berbasis model DSR (FSRS-style) yang bertindak sebagai modul maintenance memory agent. |
| G2 | Evaluasi memory agent menggunakan benchmark percakapan (LoCoMo, LongMemEval) — **belum ada evaluasi retensi belajar jangka panjang** (retention test lintas hari/minggu) untuk sistem memory belajar. | T3-03, T3-04, T3-06: metrik J/EM/ROUGE untuk percakapan. | Kerangka evaluasi dual: (a) kualitas memori (retrieval, groundedness), (b) hasil belajar (retensi, mastery, transfer) dengan retention interval mengikuti Cepeda et al. (2006). |
| G3 | Research agent (RAG untuk riset) dan learning agent (ITS/spaced repetition) dikembangkan terpisah; **belum ada loop adaptif** yang memutuskan kapan agen riset harus dijalankan berdasarkan gap pengetahuan learner. | T4 (RAG/research) vs T2 (ITS) tidak saling merujuk; roadmap/concept graph (T6) tidak punya research orchestrator. | Modul **Research Orchestrator** yang dipicu oleh gap mastery (prerequisite-unmet concept) dan menghasilkan materi terverifikasi sebelum masuk memory. |
| G4 | Human-in-the-loop dibahas sebagai prinsip etika (UNESCO 2023; Holzinger 2016; Goddard 2012) tetapi **belum ada pola operasional HITL untuk siklus hidup memory** (kapan approval wajib: ingest, konsolidasi, penghapusan, penerbitan materi). | T5; Xninetzy HITL hanya untuk aksi akademik/roadmap activation. | Lapisan **Human Approval Layer** dengan tier approval eksplisit pada titik keputusan konsekuensial (mirip safety tiers AGENTS.md). |
| G5 | Privasi memory agent adalah attack surface baru (MIA: MRMMIA 2026; poisoning: TMA-NM 2026) — sistem belajar yang menyimpan profil learner harus mempertimbangkan mitigasi, belum ada desain pembelajaran yang mengadopsinya. | T5-01, T5-02. | Kebijakan privasi: minimalisasi data, origin-bound provenance, review log, opsi forget/export. |

## 3. Counterevidence & risiko yang harus diakui dalam paper
- Testing effect tidak robust di semua domain (matematika g=0.22, CI lintas nol — Murray et al., 2025 preprint).
- Tekanan (high-stakes) merusak manfaat retrieval (Hinze & Rapp, 2014) → desain low-stakes.
- Long-context LLM sering kompetitif dengan memory system (Zhou et al., 2026 Finding 1) → klaim harus hati-hati, memory perlu justifikasi efisiensi + personalisasi.
- Konsolidasi agresif merusak retensi (Finding 6/9 Zhou 2026) → desain konservatif.
- Mem0 vs Zhou melaporkan angka kontradiktif (LoCoMo EM 4.1 vs klaim SOTA) → perbedaan metodologi evaluasi; disebut sebagai keterbatasan benchmarking.
- Bias WEIRD (Agarwal et al., 2021): generalisasi lintas budaya perlu hati-hati.
- Tidak ada eksperimen nyata di riset ini → seluruh BAB 4 menggunakan bahasa rancangan yang diusulkan (proposed), skenario, dan hipotesis evaluasi.

## 4. Pernyataan kebaruan (novelty claim, dibatasi)
"Riset ini mengusulkan arsitektur referensi yang menyatukan (1) automated memory berbasis model memori kognitif yang dapat dilatih (FSRS-style DSR), (2) research agent ber-grounding yang mengisi gap konsep, dan (3) loop adaptif berbasis concept graph dengan mastery-gated progression, dilengkapi lapisan HITL dan evaluasi retensi jangka panjang — integrasi yang belum ditemukan pada literatur yang diverifikasi (snapshot 2026-08-03)."
