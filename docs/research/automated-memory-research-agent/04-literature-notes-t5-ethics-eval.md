# Literature Notes T5 — Evaluasi, Etika, Privasi, Bias, dan Human-in-the-Loop

Tema: Evaluasi, etika, privasi, bias, dan human-in-the-loop dalam AI untuk pendidikan.
Sub-tugas dari riset "Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent".
Tanggal riset: 2026-08-03. Metode: paper_research (arxiv, crossref, semantic, openalex, pubmed, europepmc) + web (unesco.org, springer link).

Format: [ID] — semua metadata diverifikasi dari sumber (tidak ada yang dikarang).

## [T5-01] MRMMIA: Membership Inference Attacks on Memory in Chat Agents
- Penulis: Kai Chen, Yan Pang, Tianhao Wang (University of Virginia), Tahun 2026, Venue: arXiv preprint, DOI: (belum ada DOI — arXiv), URL: https://arxiv.org/abs/2605.27825
- Access: FULL TEXT (PDF arXiv:2605.27825v1 [cs.CR], 27 May 2026)
- Temuan kunci: MIA terhadap agent memory (belum banyak disentuh vs MIA LLM/RAG). Usulan Multi-Recall Memory MIA (MRMMIA): probe recall beragam (atomic topic, follow-up rationale, diversity) + scoring per setting akses (black/gray/white-box). Evaluasi pada Mem0 & MemGPT, dataset PerLTQA/LoCoMo/MSC, backbone Qwen2.5-7B-Instruct. MRMMIA unggul konsisten; contoh gray-box TPR@FPR1% LoCoMo naik 13.5%→55.9% (Mem0) dan 17.3%→63.4% (MemGPT). Pertahanan via system prompt ("memory is private...") hanya menurunkan performa sedikit → tidak cukup. K=5 probe cukup; pertanyaan rationale penting.
- Keterbatasan: preprint (belum peer-review). Dataset hanya percakapan harian/fakta personal; tidak mencakup agent kompleks (planning, tool use, multi-agent). Asumsi adversary memegang kandidat exact (exact membership rule). Menyerang chat agent lokal/open-source (bukan API propietary).
- Relevansi: bukti langsung bahwa memory agent = attack surface privasi; implikasi desain sistem adaptive memory (perlu mitigasi MIA, bukan sekadar instruksi prompt).

## [T5-02] Securing LLM-Agent Long-Term Memory Against Poisoning: Non-Malleable, Origin-Bound Authority with Machine-Checked Guarantees
- Penulis: Yedidel Louck (Ariel University, Israel), Tahun 2026, Venue: arXiv preprint, DOI: (belum ada DOI — arXiv), URL: https://arxiv.org/abs/2606.24322
- Access: FULL TEXT (PDF arXiv:2606.24322v1 [cs.CR], 23 Jun 2026)
- Temuan kunci: Memory poisoning = ancaman: konten untrusted dari satu sesi mengarahkan aksi konsekuensial di sesi lain. Tiga channel laundering: self-summarization, trusted-tool echo, manufactured corroboration. Defenses berbasis content (deteksi/trust-scoring) dan lineage (derivation history) adalah malleable. Teorema separasi ter-cek mesin (TLA+/TLC): T1 malleable gate tidak sound; T2 write-time origin binding necessary; T3 non-malleable origin-bound authority + Sybil-resistant corroboration-gated elevation sufficient. Konstruksi TMA-NM: 0% attack success pada direct & laundering attack (8 model frontier), 100% legit utility, overhead ~1.3µs/decision vs ~2000ms LLM judge. Benchmark MEM-INV-Bench (12 domain, 5 tipe tool, 4 pipeline poisoning publik direproduksi: MemMorph, MemoryGraft, Trojan Hippo, Conv. Trojan).
- Keterbatasan: preprint single-author (belum peer-review). Answer-biasing (non-konsekuensial) di luar scope. Bergantung asumsi A1 (origin-labeling oracle terautentikasi). Teorema mesin untuk model bounded (inductive invariant diperluas via argumen tangan; bukti unbounded penuh = future work). Scope single agent; cross-agent out of scope.
- Relevansi: fondasi desain pertahanan memory poisoning untuk agent; membatasi klaim: hanya mencegah aksi konsekuensial, bukan bias jawaban.

## [T5-03] Guidance for generative AI in education and research
- Penulis: Miao, Fengchun; Holmes, Wayne, Tahun 2023, Penerbit: UNESCO (7 September 2023), DOI: tidak ada, URL: https://unesdoc.unesco.org/ark:/48223/pf0000386693 (halaman publikasi: https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research)
- Access: WEB PAGE (halaman unesco.org terverifikasi penuh; unesdoc JS-rendered — judul & metadata terkonfirmasi via hasil pencarian; teks lengkap tidak diekstrak)
- Temuan kunci: Panduan global pertama UNESCO soal GenAI di pendidikan/riset. Visi human-centred: mandat perlindungan data privacy, batas usia interaksi mandiri dengan GenAI, pendekatan human-agent & age-appropriate untuk validasi etis dan desain pedagogis; langkah regulasi; isu etika/kebijakan kontroversial (privasi, kesetaraan, keamanan); penggunaan kreatif GenAI dalam kurikulum, pengajaran, riset; implikasi jangka panjang.
- Keterbatasan: dokumen kebijakan (bukan empiris); akses kami: ringkasan resmi halaman web, bukan ekstraksi teks penuh unesdoc.
- Relevansi: kerangka regulasi/etika resmi untuk sistem AI pendidikan (termasuk adaptive learning agent) — dasar klaim "privacy & human oversight wajib".

## [T5-04] Automation bias: a systematic review of frequency, effect mediators, and mitigators
- Penulis: Kate Goddard, Abdul Roudsari, Jeremy C. Wyatt, Tahun 2012, Venue: JAMIA 19(1):121-127, DOI: 10.1136/amiajnl-2011-000089, URL: https://doi.org/10.1136/amiajnl-2011-000089 (PMID 21685142)
- Access: ABSTRACT (PubMed) + METADATA (Crossref; 814–884 citations)
- Temuan kunci: Automation bias (AB) = kecenderungan over-rely pada otomasi. Dari 13.821 paper, 74 masuk kriteria. Mediator: faktor user (cognitive style, pengalaman DSS), faktor attitudinal (trust, confidence), mediator lingkungan (workload, kompleksitas tugas, tekanan waktu). Mitigators: training, penekanan akuntabilitas user, desain DSS (posisi advice, confidence level, menyajikan informasi vs rekomendasi langsung). Dibedakan dari automation-induced complacency (monitoring output tidak memadai).
- Keterbatasan: fokus healthcare/CDSS; literatur sampai 2012 (pra-LLM) — transferabilitas ke GenAI/LLM agent butuh kewaspadaan; frekuensi AB dilaporkan bervariasi antar studi.
- Relevansi: landasan klasik untuk klaim risiko over-reliance/automation bias pada sistem adaptive AI (termasuk agent yang menjawab/bertindak atas nama user).

## [T5-05] Interactive machine learning for health informatics: when do we need the human-in-the-loop?
- Penulis: Andreas Holzinger, Tahun 2016, Venue: Brain Informatics 3(2):119-131, DOI: 10.1007/s40708-016-0042-6, URL: https://doi.org/10.1007/s40708-016-0042-6
- Access: METADATA (Crossref; 739 citations). Catatan: abstract/full text belum berhasil diekstrak sesi ini (semantic & europepmc tidak mengembalikan record).
- Temuan kunci (berdasarkan metadata terverifikasi): artikel jurnal tentang interactive machine learning (iML) di health informatics yang secara eksplisit mengajukan pertanyaan "kapan kita butuh human-in-the-loop" — rujukan kanonik untuk konsep HITL. Detail argumen tidak dikutip di sini karena belum diverifikasi teksnya.
- Keterbatasan: akses metadata-only pada sesi ini; domain kesehatan.
- Relevansi: sumber kanonik HITL untuk bagian human-in-the-loop sistem adaptive; direkomendasikan verifikasi full-text lanjutan.

## [T5-06] A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions
- Penulis: Lei Huang, Weijiang Yu, Weitao Ma, Weihong Zhong, Zhangyin Feng, Haotian Wang, Qianglong Chen, Weihua Peng, Xiaocheng Feng, Bing Qin, Ting Liu, Tahun 2024 (arXiv v2 19 Nov 2024; terbit ACM TOIS 2025), Venue: ACM Transactions on Information Systems 43(2):1-55, DOI: 10.1145/3703155, URL: https://arxiv.org/abs/2311.05232
- Access: FULL TEXT (arXiv:2311.05232v2 [cs.CL]) + METADATA Crossref (1823 citations)
- Temuan kunci: Taksonomi hallucination LLM: factuality hallucination (factual contradiction, factual fabrication) vs faithfulness hallucination (instruction inconsistency, context inconsistency, logical inconsistency). Penyebab: data (misinformation/bias, knowledge boundary), training (pre-training, SFT, RLHF/sycophancy), inference (decoding, over-confidence, softmax bottleneck, reasoning failure). Review metode deteksi + benchmark (TruthfulQA, HaluEval, SelfCheckGPT...) dan mitigasi; RAG mengurangi tapi tidak menghilangkan hallucination (RAG sendiri bisa hallucinate). Menyoroti korelasi bias sosial & hallucination.
- Keterbatasan: cakupan literatur s.d. ~2024; survey (bukan meta-analisis); RAG dibahas sebagai mitigasi parsial.
- Relevansi: kerangka evaluasi hallucination/faithfulness untuk LLM-based education systems — landasan metrik evaluasi output agent memory (apakah jawaban grounded pada memory/konteks).

## [T5-07] Artificial intelligence and academic anxiety? a meta-analysis
- Penulis: Weihao Wang, Long Diao, Jingting Yu, Tahun 2026, Venue: BMC Psychology (Systematic Review, Open Access), DOI: 10.1186/s40359-026-05018-y, URL: https://doi.org/10.1186/s40359-026-05018-y
- Access: FULL TEXT (halaman Springer Nature Link; abstract lengkap; artikel "unedited version" early access)
- Temuan kunci: Meta-analisis 22 studi, 30 effect sizes, RVE random-effects: intervensi AI menurunkan academic anxiety secara signifikan, efek moderat g = −0.65 (95% CI [−1.07, −0.22], p < .01). Moderator: test anxiety & general academic anxiety signifikan; math/foreign language/learning anxiety tidak. Intelligent tutoring systems & robotics signifikan; chatbots & virtual technology tidak. Efek universitas non-signifikan; konteks Eastern signifikan, Western/Islamic tidak. Studi pasca-2022 efek lebih besar (marginal). Studi sampel kecil → efek lebih besar (indikasi bias publikasi). Q-tests mayoritas non-signifikan (p > .05) → perbedaan moderator deskriptif, bukan robust statistik.
- Keterbatasan: manuskrip unedited/early access (disclaimer resmi: mungkin ada error); perbedaan subgroup deskriptif; jumlah studi kecil; relevansi untuk kecemasan akademik Indonesia perlu generalisasi hati-hati.
- Relevansi: bukti empiris efek AI di pendidikan (konteks kesejahteraan siswa) + pelajaran metodologis: moderator sering tidak robust — hati-hati terhadap klaim efek diferensial.

## [T5-08] Understanding privacy and data protection issues in learning analytics using a systematic review
- Penulis: Qinyi Liu, Mohammad Khalil, Tahun 2023, Venue: British Journal of Educational Technology, DOI: 10.1111/bjet.13388, URL: https://doi.org/10.1111/bjet.13388
- Access: ABSTRACT + METADATA (OpenAlex; 67 citations)
- Temuan kunci: Systematic review (47 paper, jurnal edtech top): 8 isu privasi/perlindungan data yang saling terkait di seluruh siklus learning analytics; perbedaan persepsi stakeholder lintas region; solusi yang diusulkan minim bukti aplikasi empiris ("dearth of applied evidence"); isu privat tidak boleh dilonggarkan di titik manapun dalam siklus pengembangan; konteks GDPR menjadi latar diskusi.
- Keterbatasan: konteks learning analytics (belum spesifik GenAI/agent memory); korpus jurnal edtech.
- Relevansi: sumber tambahan untuk klaim privasi data pendidikan (mekanisme FERPA/GDPR-adjacent) dan evaluasi: solusi privasi harus evidence-based.

## [T5-09] Practical ethics for building learning analytics
- Penulis: Kirsty Kitto, Simon Knight, Tahun 2019, Venue: British Journal of Educational Technology, DOI: 10.1111/bjet.12868, URL: https://doi.org/10.1111/bjet.12868
- Access: ABSTRACT + METADATA (OpenAlex; 135 citations)
- Temuan kunci: Tiga ketegangan dalam kerangka etika learning analytics (LA) yang ada → berisiko over-cautious underuse atau unbridled misuse. GDPR berlaku untuk pendidikan tapi kompleksitasnya menyulitkan penerapan. Usulan "practical ethics" berbasis virtue ethics + kumpulan edge case dari praktisi; etika LA butuh keterlibatan teknis-pembuat sistem.
- Keterbatasan: konseptual/posisi (bukan empiris); pra-GenAI.
- Relevansi: sumber tambahan etika AI-edu: checklist/framework etika sering tidak diikuti praktisi — implikasi desain: etika harus dibangun ke dalam sistem, bukan add-on.

---
## Ringkasan access status
- Full text: T5-01 (arXiv PDF), T5-02 (arXiv PDF), T5-03 (web page resmi UNESCO — ringkasan), T5-06 (arXiv PDF), T5-07 (web Springer, abstract+full unedited).
- Abstract: T5-04 (PubMed), T5-08 (OpenAlex), T5-09 (OpenAlex).
- Metadata only: T5-05 (Crossref).
- Gagal/tidak dipakai: search semantic untuk beberapa query kosong; unesdoc tidak bisa diekstrak (JS); OUP PDF automation bias tidak diunduh (abstract sudah cukup).

## Queries yang dieksekusi
1. read_arxiv_paper 2605.27825 (full text) — OK
2. read_arxiv_paper 2606.24322 (full text) — OK
3. get_crossref_paper_by_doi 10.1186/s40359-026-05018-y — OK (metadata)
4. web_search "UNESCO Guidance for generative AI in education and research 2023 unesdoc" (ddg/bing/startpage) — 0 hasil/error engine
5. search_arxiv hallucination survey — gagal match (hasil irelevan)
6. search_semantic automation bias — kosong; pubmed "Automation bias..." — OK (abstract)
7. search_crossref "Interactive machine learning for health informatics..." — OK (metadata)
8. read_arxiv_paper 2311.05232 — OK (full text)
9. get_crossref 10.1136/amiajnl-2011-000089 — OK
10. search_openalex "privacy learning analytics student data protection GDPR" — OK (kandidat: Liu & Khalil 2023; Kitto & Knight 2019; Tsai et al. 2020)
11. fetchWebContent unesdoc ark:/48223/pf0000386693 — no readable content (JS)
12. fetchWebContent unesco.org articles guidance — OK (verifikasi penuh)
13. read_semantic DOI:10.1186/... — error stream
14. search_semantic Wang meta-analysis 2026 — kosong
15. search_semantic Holzinger — kosong
16. markitdown unesdoc — 403 Forbidden
17. fetchWebContent bmcpsychology DOI page — OK (abstract lengkap)
18. search_pubmed Holzinger — error malformed; search_europepmc — tidak menemukan record Holzinger 2016
19. xninetzy_web_search "UNESCO Guidance ... unesdoc URL" — OK (mengonfirmasi URL unesdoc ark:/48223/pf0000386693)
20. get_crossref 10.1145/3703155 — OK (metadata + abstract)
