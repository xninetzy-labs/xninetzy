# 04 — Literature Notes T2: Intelligent Tutoring Systems, Adaptive Learning, Knowledge Tracing, Learner Modeling

Tema: T2 — ITS, adaptive learning, knowledge tracing, learner modeling.
Metode: verifikasi metadata via paper_research (CrossRef, OpenAlex, arXiv, Semantic Scholar, dblp, Unpaywall); full text dibaca untuk Piech 2015 (arXiv PDF) dan Settles & Meeder 2016 (ACL Anthology PDF); sisanya berbasis abstract dari CrossRef/OpenAlex/Springer. Tanggal: 2026-08-03.

## T2-01 Bloom (1984) The 2 Sigma Problem
- Benjamin S. Bloom, 1984, Educational Researcher 13(6):4-16, DOI 10.3102/0013189X013006004, https://doi.org/10.3102/0013189X013006004
- Access: metadata (CrossRef) + abstract parsial (OpenAlex); full text closed (Unpaywall: is_oa=false, SAGE paywall).
- Temuan kunci: paper fondasional yang menamai "2 Sigma Problem" — membandingkan tiga kondisi: conventional (≈30 siswa/guru), mastery learning (formative test + corrective procedure), dan one-to-one tutoring (disertai formative feedback). Klaim terkenalnya: siswa dengan tutoring individual rata-rata ≈2 SD di atas conventional instruction; klaim ini dikonfirmasi sebagai klaim paper lewat judulnya sendiri serta kutipan full-text Piech et al. (2015: "learning gains for the average student on the order of two standard deviations") dan dirujuk VanLehn (2011, abstract: keyakinan human tutors d=2.0). Catatan: angka "1 sigma" untuk mastery learning TIDAK muncul di abstract yang saya akses — jangan dikutip tanpa verifikasi full text.
- Keterbatasan: bukan eksperimen terkontrol tunggal melainkan sintesis disertasi (Anania 1982/83, Burke 1984) dalam kondisi ideal; replikasi lapangan modern tidak mencapai 2σ (lihat VanLehn 2011).
- Relevansi: justifikasi teoretis mengapa sistem adaptif mengejar efektivitas tutoring; dasar narasi "gap 2 sigma" untuk riset.

## T2-02 VanLehn (2011) Relative Effectiveness of Human Tutoring, ITS, Other Tutoring Systems
- Kurt VanLehn, 2011, Educational Psychologist 46(4):197-221, DOI 10.1080/00461520.2011.611369, https://doi.org/10.1080/00461520.2011.611369
- Access: abstract lengkap (OpenAlex); full text closed (Unpaywall: is_oa=false).
- Temuan kunci: review eksperimen membandingkan human/computer/no tutoring; klasifikasi granularity interaksi: answer-based, step-based, substep-based. Keyakinan umum (answer-based d=0.3, ITS d=1.0, human tutor d=2.0) TIDAK terkonfirmasi: human tutoring d=0.79, ITS d=0.76 (hampir setara human), answer-based jauh lebih rendah. Efektivitas naik seiring granularity interaksi (step/substep > answer).
- Keterbatasan: komparasi antar studi dengan kontrol "no tutoring" yang heterogen; STEM-heavy; data lama (pra-2011).
- Relevansi: desain interaksi sistem adaptif kita — step-level feedback mendekati efektivitas tutor manusia; menetapkan ekspektasi effect size realistis (~0.76, bukan 2.0).

## T2-03 Steenbergen-Hu & Cooper (2014) ITS Meta-Analysis (College)
- Saiying Steenbergen-Hu & Harris Cooper, 2014, Journal of Educational Psychology 106(2):331-347, DOI 10.1037/a0034752, https://doi.org/10.1037/a0034752
- Access: abstract lengkap (OpenAlex); full text closed (APA paywall).
- Temuan kunci: meta-analisis ITS untuk mahasiswa; 35 laporan, 39 studi, 22 tipe ITS (AutoTutor, ALEKS, XTutor-Expert System, WISE). (a) Efek positif moderat keseluruhan g = .32–.37; (b) ITS lebih rendah dari human tutoring tapi mengungguli semua metode lain (instruksi kelas tradisional, baca teks, CAI, lab/PR, no-treatment); (c) efektivitas tidak berbeda signifikan menurut tipe ITS/domain/cara keterlibatan; (d) studi lebih awal efeknya lebih besar dari studi lebih baru. Ada indikasi pentingnya guru/pedagogi dalam ITS-assisted learning.
- Keterbatasan: paywall; hanya pendidikan tinggi; rentang g lebar (.32-.37) — gunakan sebagai rentang, bukan titik tunggal.
- Relevansi: menyediakan rentang effect size yang bisa dikutip (g = .32–.37) untuk klaim "ITS memberi efek positif moderat di pendidikan tinggi".

## T2-04 Ma, Adesope, Nesbit & Liu (2014) ITS and Learning Outcomes Meta-Analysis
- Wenting Ma, Olusola O. Adesope, John C. Nesbit, Qing Liu, 2014, Journal of Educational Psychology 106(4):901-918, DOI 10.1037/a0037123, https://doi.org/10.1037/a0037123
- Access: abstract lengkap (OpenAlex); full text closed (APA paywall). DOI dikonfirmasi CrossRef (10.1037/a0037123; entri .supp terpisah).
- Temuan kunci: 107 effect size, 14.321 partisipan. ITS > teacher-led large-group instruction (g = 0.42), > non-ITS computer-based instruction (g = 0.57), > textbooks/workbooks (g = 0.35); TIDAK berbeda signifikan vs individualized human tutoring (g = −0.11) dan small-group instruction (g = 0.05). Efek positif signifikan di semua jenjang pendidikan, hampir semua domain, baik sebagai instruksi utama/suplemen/komponen/PR. Konsisten dengan analisis publication bias (klaim ITS relatif efektif tidak dijelaskan oleh bias).
- Keterbatasan: paywall; inklusi studi s.d. ~2012 (data pra-deep-learning).
- Relevansi: bukti kuantitatif terbesar untuk klaim efektivitas ITS; angka g = 0.42/0.57/0.35 dapat dikutip dengan konteks komparator.

## T2-05 Xu et al. (2019) ITS Reading Comprehension Meta-Analysis (BJET)
- Zhihong Xu, Kausalai (Kay) Wijekumar, Gilbert Ramirez, Xueyan Hu, Robin Irey, 2019, British Journal of Educational Technology 50(6):3119-3137, DOI 10.1111/bjet.12758, https://doi.org/10.1111/bjet.12758
- Access: abstract lengkap (CrossRef, jats-xml); full text via Wiley TDM link (tidak diunduh).
- Temuan kunci: 19 studi dari 13 publikasi, ±10.000 siswa K-12, 88 estimasi effect size (robust variance estimation). Overall random effect size ITS pada reading comprehension = 0.60 (95% CI 0.36–0.85, p<0.001, campuran standardized + researcher-designed). ITS vs human tutoring kecil: 0.20 (95% CI 0.02–0.38, p=0.036, n=21, semua standardized). ITS vs traditional instruction: 0.86 (mixed measures) dan 0.26 (standardized measures).
- Keterbatasan: hanya K-12 reading; perbedaan besar antara ukuran standardized vs researcher-designed menunjukkan risiko overestimate; saran penulis: studi banding versi ITS lama vs baru.
- Relevansi: bukti untuk domain pemahaman bacaan (relevan bila sistem kita mengadaptasi materi teks); ilustrasi moderator jenis tes.

## T2-06 Piech et al. (2015) Deep Knowledge Tracing (DKT)
- Chris Piech, Jonathan Spencer, Jonathan Huang, Surya Ganguli, Mehran Sahami, Leonidas Guibas, Jascha Sohl-Dickstein, 2015, NeurIPS (NIPS 2015), arXiv:1506.05908, DOI 10.48550/arXiv.1506.05908, https://arxiv.org/abs/1506.05908
- Access: FULL TEXT dibaca (arXiv PDF, v1 19 Jun 2015).
- Temuan kunci: model RNN/LSTM untuk knowledge tracing tanpa encoding domain expertise. AUC: Assistments 0.86 vs best prior (BKT*) 0.69 (gain 25%) vs marginal 0.62; Khan Academy 0.85 vs BKT 0.68 (marginal 0.63); data simulasi: LSTM menyamai oracle. Tidak butuh expert annotations; bisa untuk desain kurikulum (MDP, expectimax; MDP-8 > blocking > mixing) dan discovery struktur antar-exercise. Keterbatasan yang diakui penulis: butuh data sangat besar (cocok online education, bukan kelas kecil); representasi latensi high-dimensional kurang interpretable.
- Keterbatasan (dari literatur lanjutan): dua masalah DKT didokumentasikan Yeung & Yeung (2018, DOI 10.1145/3231644.3231647): gagal merekonstruksi input (prediksi mastery bisa turun setelah jawaban benar) dan inkonsistensi prediksi lintas time-step; regularisasi memperbaikinya.
- Relevansi: landasan knowledge tracing modern untuk learner modeling di sistem adaptif; baseline AUC yang bisa dikutip (0.86 vs 0.69).

## T2-07 Kulik & Fletcher (2016) Effectiveness of ITS (RER Review)
- James A. Kulik & J. D. Fletcher, 2016, Review of Educational Research 86(1):42-78, DOI 10.3102/0034654315581420, https://doi.org/10.3102/0034654315581420
- Access: abstract lengkap (CrossRef); full text SAGE paywall (URL pdf tersedia di metadata).
- Temuan kunci: meta-analisis 50 evaluasi terkontrol; median efek = 0.66 SD (50th→75th percentile). Besar efek sangat tergantung jenis tes: locally developed vs standardized (alignment instruksi-tes penentu hasil). Enam evaluasi kontrol nonkonvensional dan empat implementasi cacat menghasilkan efek kecil — hasil evaluasi dipengaruhi kualitas implementasi dan kontrol.
- Keterbatasan: median (bukan mean); tidak memilah granularity interaksi; kualitas implementasi tidak selalu dilaporkan di studi primer.
- Relevansi: angka 0.66 SD (median) sering dikutip — kontekstualisasikan dengan moderator jenis tes; pelajaran desain evaluasi (alignment & fidelity).

## T2-08 Huang, Xu & Liu (2025) Effects of ITS on Educational Outcomes
- Xiaoli Huang, Wei Xu, Ruijia Liu, 2025, International Journal of Distance Education Technologies 23(1):1-25, DOI 10.4018/ijdet.368420, https://doi.org/10.4018/ijdet.368420
- Access: abstract lengkap (CrossRef); full text IGI Global (paywall, tanpa pdf_url).
- Temuan kunci: meta-analisis (Stata 18.0) lintas negara & jenjang; k = 30 studi, g = 0.86 keseluruhan. ITS signifikan memperbaiki learning attitudes dan test scores, tapi efek pada knowledge acquisition, learner motivation, performance, dan problem-solving skills kurang konklusif. Efek bervariasi antar negara dan jenjang (tidak ada hubungan signifikan jenjang-efektivitas). Desain tertentu — game-integrated ITS dan ITS dengan worked examples — tampak lebih positif.
- Keterbatasan: k kecil (30); heterogenitas tinggi; perlu cek definisi outcome; jurnal niche (IGI) — cross-check dengan meta-analisis lain.
- Relevansi: bukti terbaru (2025); menekankan moderator desain (game/worked examples) — berguna untuk argumen desain sistem adaptif.

## T2-09 Corbett & Anderson (1995) Bayesian Knowledge Tracing (sumber tambahan 1)
- Albert T. Corbett & John R. Anderson, 1995, User Modeling and User-Adapted Interaction 4(4):253-278 (terbit online Des 1994), DOI 10.1007/BF01099821, https://doi.org/10.1007/BF01099821
- Access: abstract lengkap (halaman Springer); full text paywall (subscription).
- Temuan kunci: model learner modeling paling berpengaruh sebelum deep learning — BKT pada ACT Programming Tutor (APT): cognitive model production-rule ("ideal student model") memungkinkan tutor menyelesaikan latihan bersama siswa; tutor memelihara estimasi probabilitas siswa telah mempelajari tiap rule (knowledge tracing) dan menyajikan urutan latihan individual sampai "mastered" tiap rule; model "quite successful" memprediksi test performance. (Formulasi HMM binary per-konsep dijelaskan juga di Piech 2015 §2.1.)
- Keterbatasan: representasi biner per-konsep (tidak menangkap interdependensi konsep), asumsi tidak lupa, butuh konsep dilabeli ahli (semua dikritik oleh pendekatan DKT).
- Relevansi: fondasi learner modeling adaptif (model + policy mastery) — konsep "individualized sequence until mastery" langsung terkait rancangan sistem.

## T2-10 Settles & Meeder (2016) Trainable Spaced Repetition (HLR/Duolingo) (sumber tambahan 2)
- Burr Settles & Brendan Meeder, 2016, Proceedings of ACL 2016 (Vol 1: Long Papers), pp. 1848-1858, DOI 10.18653/v1/P16-1174, https://aclanthology.org/P16-1174/
- Access: FULL TEXT dibaca (ACL Anthology PDF).
- Temuan kunci: Half-Life Regression (HLR) — spaced repetition trainable untuk language learning; menggabungkan forgetting curve Ebbinghaus (p = 2^(−Δ/h)) dengan fitur interaksi + lexeme tags; dilatih pada 12,9 juta instance log Duolingo. HLR memotong MAE ≥45% vs baseline Leitner dalam memprediksi recall; AUC terbaik justru Leitner (0.542 vs HLR 0.538) — HLR unggul di MAE/COR_h. Eksperimen user terkontrol (n≈1 juta; n=3,3 juta): HLR vs Leitner menaikkan daily retention any-activity +0.3% (ns) dan menurunkan practice −7.3%*; HLR-lex vs HLR: any activity +12.0%*, lessons +1.7%*, practice +9.5%* (p<0.001) → dideploy; dikaitkan dengan pertumbuhan 5% month-on-month active users. Bobot model menunjukkan kata sulit (irregular/rare) vs mudah (cognates) — insight personalisasi.
- Keterbatasan: AUC rendah (~0.54) karena tugas noisy & recall tinggi (p̄=0.859); overfitting fitur lexeme (cold-start bahasa baru); metrik retention/engagement, bukan learning outcome langsung.
- Relevansi: jembatan langsung ke "automated memory" — model memori (half-life) yang dapat dilatih untuk penjadwalan ulasan adaptif; bukti bahwa personalisasi scheduling meningkatkan engagement.

## T2-11 Ghosh, Heffernan & Lan (2020) Context-Aware Attentive Knowledge Tracing (AKT) (sumber tambahan 3)
- Aritra Ghosh, Neil T. Heffernan, Andrew Lan, 2020, KDD '20, DOI 10.1145/3394486.3403282, https://doi.org/10.1145/3394486.3403282
- Access: abstract lengkap (OpenAlex); PDF via ACM (dl.acm.org pdf link di metadata; tidak diunduh).
- Temuan kunci: AKT menggabungkan attention-based neural KT dengan komponen interpretable terinspirasi model kognitif/psikometrik: monotonic attention dengan exponential decay + context-aware relative distance + similarity antar soal; regularisasi Rasch pada concept/question embeddings (menangkap perbedaan individu antar soal tanpa parameter berlebih). Mengungguli metode KT existing hingga 6% AUC pada benchmark; case study menunjukkan interpretability → potensi automated feedback & personalization.
- Keterbatasan: evaluasi offline (AUC pada benchmark), bukan randomized learning outcome; klaim personalization masih potensial.
- Relevansi: state-of-the-art knowledge tracing yang interpretable — jawaban atas kritik interpretability DKT; model embedding soal/konsep yang bisa diadopsi arsitektur sistem.

## Catatan konflik & counterevidence lintas sumber
- Klaim Bloom "2σ" tidak terkonfirmasi: VanLehn (2011) menemukan human tutoring d=0.79 dan ITS step-based d=0.76 (bukan 2.0/1.0). Steenbergen-Hu & Cooper (2014) juga menemukan human tutoring sedikit lebih baik dari ITS (selisih tidak signifikan di Ma et al. 2014: g=−0.11).
- Efek ITS sensitif terhadap alat ukur: Xu et al. (2019) 0.86 (mixed) vs 0.26 (standardized); Kulik & Fletcher (2016) menyatakan alignment tes-instruksi penentu hasil. Hati-hati mengutip angka tunggal tanpa menyebut jenis ukuran.
- Tren menurun: Steenbergen-Hu & Cooper (2014) studi awal > studi baru; relevan untuk klaim "ITS efektif" di era modern.
- Huang et al. (2025, g=0.86, k=30) lebih tinggi dari meta-analisis lama — heterogenitas & definisi outcome perlu diperiksa sebelum dikutip berdampingan dengan Ma et al. (2014).
- DKT: unggul prediksi tapi (a) butuh data besar, (b) dua masalah konsistensi (Yeung & Yeung 2018, DOI 10.1145/3231644.3231647), (c) interpretability — AKT (2020) menjawab sebagian.

## Effect sizes yang terverifikasi (dari abstract/full text yang diakses)
- VanLehn 2011: human tutoring d=0.79; ITS (step-based) d=0.76; keyakinan answer/ITS/human d=0.3/1.0/2.0 tidak terkonfirmasi.
- Steenbergen-Hu & Cooper 2014: g = 0.32–0.37 (college).
- Ma et al. 2014: g = 0.42 (vs teacher-led), 0.57 (vs non-ITS CBI), 0.35 (vs textbooks); 0.05 (vs small-group, ns); −0.11 (vs human tutoring, ns).
- Xu et al. 2019: overall 0.60 (CI 0.36–0.85); vs human tutoring 0.20 (CI 0.02–0.38); vs traditional 0.86/0.26 (mixed/standardized).
- Kulik & Fletcher 2016: median 0.66 SD (50th→75th percentile).
- Huang et al. 2025: g = 0.86 (k=30).
- Piech et al. 2015: AUC 0.86 (Assistments) vs 0.69 prior best; 25% gain.
- Settles & Meeder 2016: MAE ↓ ≥45% vs Leitner; retention +12.0% (any activity, HLR-lex).

## Gap & rekomendasi langkah riset berikutnya
1. Cek full text VanLehn (2011) & Steenbergen-Hu (2014) untuk moderator (jenis tes, granularity) bila perlu dikutip dalam.
2. Bandingkan definisi outcome Huang et al. (2025) vs Ma et al. (2014) sebelum menyajikan rentang g (0.32–0.86) — heterogenitas besar.
3. Untuk bagian "automated memory": eksplorasi FSRS (scheduling modern) dan DALEK/SLAM Duolingo bila tersedia di round 2 — DALEK tidak ditemukan via OpenAlex/Semantic Scholar (query "DALEK machine learning platform Duolingo" kosong); verifikasi lewat pencarian web/dblp.
4. Knowledge tracing modern: pertimbangkan juga survei Abdelrahman et al. (2022, ACM CSUR, DOI 10.1145/3569576, terverifikasi di OpenAlex) untuk peta metode KT.
