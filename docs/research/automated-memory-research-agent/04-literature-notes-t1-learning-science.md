# Literature Notes T1 — Learning Science & Cognitive Foundations

Tema: Landasan kognitif untuk automated memory dalam pembelajaran (spacing effect, retrieval practice, desirable difficulties, cognitive load, konsolidasi memori, dan penjadwalan optimal).
Sub-tugas dari riset "Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent".
Tanggal riset: 2026-08-03. Metode: paper_research (crossref, arxiv, openalex, dblp) + web (Wikipedia untuk metadata edisi buku klasik, arXiv API langsung).

Format: [ID] — semua metadata diverifikasi dari sumber (tidak ada yang dikarang; DOI hanya ditulis jika benar-benar ditemukan di database).

**Catatan koreksi brief riset:** "Ye et al. (2024) A stochastic shortest path algorithm... (FSRS)" — tahun yang benar adalah **2022** (KDD '22, DOI 10.1145/3534678.3539081, dblp YeSC22). Tidak ditemukan versi arXiv 2024 (query arXiv API: `"spaced repetition" AND "shortest path"` → 0 hasil; `FSRS` → tidak ada paper FSRS yang relevan).

---

## [T1-EBB] Memory: A Contribution to Experimental Psychology
- Hermann Ebbinghaus, 1885 (Jerman: *Über das Gedächtnis*); terjemahan Inggris 1913 oleh Henry A. Ruger & Clara E. Bussenius, New York: Teachers College Press (reprint Dover 1964), Buku. DOI: 10.1037/10011-000 (PsycBooks/APA), URL: https://doi.org/10.1037/10011-000 — lihat juga reprint 2013: Annals of Neurosciences 20(4), DOI 10.5214/ans.0972.7531.200408; salinan klasik: https://psychclassics.yorku.ca/Ebbinghaus/
- Access: METADATA (CrossRef: DOI 10.1037/10011-000, publisher Teachers College Press, 1913) + WEB PAGE (Wikipedia "Hermann Ebbinghaus" untuk konfirmasi sejarah edisi: asli 1885, terjemahan Ruger & Bussenius 1913 Teachers College, reprint Dover). Teks penuh tidak dibaca sesi ini.
- Temuan kunci: (1) Forgetting curve — retensi meluruh eksponensial; penurunan tercepat pada ~20 menit pertama dan signifikan hingga jam pertama, melandai setelah ~1 hari. (2) Savings (penghematan) — materi yang pernah dipelajari lebih cepat dipelajari ulang, bukti residu memori di bawah ambang recall sadar. (3) Mendokumentasikan spacing effect dan serial position effect (primacy/recency) dengan nonsense syllables (2.300 suku kata CVC).
- Keterbatasan: subjek tunggal (n=1, dirinya sendiri) — validitas internal baik tapi generalisasi terbatas; materi nonsense syllables (validitas ekologis rendah untuk belajar bermakna); hanya mengukur rote memory, bukan pemahaman/transfer.
- Relevansi: fondasi kurva lupa (forgetting curve) yang dipakai model memori modern (termasuk estimasi retention di scheduler spaced repetition); dasar klaim "jadwal review harus mengikuti dinamika decay".

## [T1-KR08] The Critical Importance of Retrieval for Learning
- Jeffrey D. Karpicke & Henry L. Roediger III, 2008, Science 319(5865):966-968. DOI: 10.1126/science.1152408, URL: https://doi.org/10.1126/science.1152408
- Access: ABSTRACT (CrossRef — abstract lengkap terverifikasi). Full text paywalled (Science/AAAS).
- Temuan kunci: (1) Repeated testing setelah item berhasil dijawab menghasilkan efek positif besar pada delayed recall; repeated studying tidak berpengaruh. (2) Mahasiswa memprediksi performa mereka secara tidak berkorelasi dengan performa aktual — ketidaksadaran metakognitif akan manfaat retrieval practice. (3) Menegaskan peran retrieval practice dalam konsolidasi learning.
- Keterbatasan: satu eksperimen lab dengan materi kosa kata bahasa asing; rentang retensi terbatas; tidak membahas kondisi implementasi digital.
- Relevansi: bukti utama untuk fitur "active recall/retrieval practice" pada automated memory agent; juga menunjukkan perlu feedback/judgment otomatis karena self-assessment user tidak reliabel.

## [T1-CEP06] Distributed Practice in Verbal Recall Tasks: A Review and Quantitative Synthesis
- Nicholas J. Cepeda, Harold Pashler, Edward Vul, John T. Wixted, Doug Rohrer, 2006, Psychological Bulletin 132(3):354-380. DOI: 10.1037/0033-2909.132.3.354 (sesuai brief — terverifikasi), URL: https://doi.org/10.1037/0033-2909.132.3.354
- Access: ABSTRACT (OpenAlex — abstract lengkap; OpenAlex menyediakan pdf OA via eScholarship) + METADATA (CrossRef, 1334+ citations).
- Temuan kunci: (1) Meta-analisis 839 pengukuran distributed practice dari 317 eksperimen dalam 184 artikel. (2) ISI (interstudy interval) dan retention interval bekerja bersama: ISI yang menghasilkan retensi maksimal **meningkat seiring bertambahnya retention interval**. (3) Efek spacing (massed vs spaced) dan lag (kurang vs lebih spasi) keduanya signifikan memengaruhi final-test retention; efek expanding ISI dianalisis.
- Keterbatasan: fokus tugas verbal recall (tidak mencakup semua domain/materi kompleks); efek gabungan ISI×RI berarti "satu jadwal optimal universal" tidak ada.
- Relevansi: dasar empiris untuk desain scheduler adaptif — interval review harus disesuaikan dengan target retention interval (dipakai literatur FSRS/Leitner modern).

## [T1-DUN13] Improving Students' Learning With Effective Learning Techniques
- John Dunlosky, Katherine A. Rawson, Elizabeth J. Marsh, Mitchell J. Nathan, Daniel T. Willingham, 2013, Psychological Science in the Public Interest 14(1):4-58. DOI: 10.1177/1529100612453266 (sesuai brief — terverifikasi), URL: https://doi.org/10.1177/1529100612453266
- Access: ABSTRACT (CrossRef — abstract lengkap terverifikasi) + METADATA (2285 citations). PDF tersedia di SAGE (pdf_url), belum dibaca penuh sesi ini.
- Temuan kunci: (1) Evaluasi 10 teknik belajar: **practice testing dan distributed practice = high utility** (generalisasi luas lintas usia, materi, kriteria tugas, termasuk konteks pendidikan). (2) Elaborative interrogation, self-explanation, interleaved practice = moderate utility. (3) Summarization, highlighting, keyword mnemonic, imagery, rereading = low utility (banyak dipakai siswa tapi tidak konsisten meningkatkan performa).
- Keterbatasan: review naratif-terstruktur (bukan meta-analisis dengan pooled effect size); ratings bersifat judgmental berdasarkan kriteria generalisasi; fokus teknik yang "mudah dipakai siswa", bukan sistem otomatis.
- Relevansi: peta teknik mana yang layak diotomasi (testing + spacing) vs tidak (rereading/highlighting) dalam adaptive learning agent.

## [T1-RED16] Unbounded Human Learning: Optimal Scheduling for Spaced Repetition
- Siddharth Reddy, Igor Labutov, Siddhartha Banerjee, Thorsten Joachims, 2016, KDD '16 (Proceedings of the 22nd ACM SIGKDD), arXiv:1602.07032. DOI: 10.1145/2939672.2939850, URL: https://arxiv.org/abs/1602.07032
- Access: ABSTRACT (arXiv API) + METADATA (arXiv; DOI terverifikasi). Full text OA tersedia di arXiv (PDF), belum dibaca penuh sesi ini.
- Temuan kunci: (1) Mining log spaced-repetition software untuk menetapkan ketergantungan fungsional retensi pada reinforcement dan delay (model memori empiris). (2) Model stokastik: queueing network model sistem Leitner + heuristic approximation yang menghasilkan masalah optimasi penjadwalan review yang tractable. (3) Eksperimen Mechanical Turk memverifikasi prediksi kualitatif: fase transisi tajam (phase transition) pada hasil belajar saat rate introduksi item baru dinaikkan.
- Keterbatasan: model disederhanakan (queueing/Leitner), bukan model memori per-item presisi; validasi utamanya prediksi kualitatif, bukan akurasi retensi per individu.
- Relevansi: jembatan pertama learning science → optimasi komputasional penjadwalan; dasar argumen "jadwal review dapat diformalkan sebagai masalah optimasi".

## [T1-FSRS22] A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling
- Junyao Ye, Jingyong Su, Yilong Cao, 2022 (BUKAN 2024), KDD '22, pp. 4381-4390. DOI: 10.1145/3534678.3539081, URL: https://doi.org/10.1145/3534678.3539081 (dblp: https://dblp.org/rec/conf/kdd/YeSC22)
- Access: ABSTRACT (OpenAlex) + METADATA (OpenAlex & dblp). Tidak ada versi arXiv (dikonfirmasi via arXiv API; paper KDD paywalled, full text tidak dibaca).
- Temuan kunci: (1) Memory model ber-properti Markov dibangun dari 220 juta log perilaku memori siswa (time-series features). (2) Scheduler dijamin meminimalkan review cost via stochastic shortest path (SSP) algorithm. (3) Peningkatan performa 12.6% dibanding state-of-the-art; sudah dideploy di aplikasi belajar bahasa online MaiMemo (jutaan siswa). Ini adalah paper FSRS (Free Spaced Repetition Scheduler) asli.
- Keterbatasan: evaluasi berbasis log internal MaiMemo (bukan RCT eksperimental dengan kelompok kontrol pedagogis); metrik "review cost" = efisiensi, belum tentu ekuivalen dengan hasil belajar jangka panjang.
- Relevansi: bukti penerapan optimasi penjadwalan (SSP) pada skala industri; fondasi teknis FSRS yang relevan untuk "automated memory" agent.

## [T1-BJ94] Memory and Metamemory Considerations in the Training of Human Beings
- Robert A. Bjork, 1994, dalam Metacognition: Knowing About Knowing (J. Metcalfe & A. P. Shimamura, Eds.), MIT Press, pp. 185-206. DOI: 10.7551/mitpress/4561.003.0011, URL: https://doi.org/10.7551/mitpress/4561.003.0011
- Access: METADATA (CrossRef — MIT Press chapter, 734 citations). Teks penuh tidak dibaca sesi ini.
- Temuan kunci (metadata + literatur sekunder terverifikasi): memperkenalkan distingsi storage strength vs retrieval strength dan konsep **desirable difficulties** — kondisi yang memperlambat akuisisi tampak (spacing, testing, interleaving, variasi) meningkatkan retensi dan transfer jangka panjang; sistem memori manusia optimal bila dilatih dalam kondisi sulit tersebut.
- Keterbatasan: chapter konseptual (bukan data primer); klaim detail argumen belum diverifikasi dari teks penuh sesi ini.
- Relevansi: sumber kanonik istilah "desirable difficulties" — pembenaran kognitif bahwa kesulitan terkelola dalam sistem adaptive (bukan kemudahan maksimal) justru baik untuk belajar.

## [T1-BJ11] Making Things Hard on Yourself, But in a Good Way: Creating Desirable Difficulties to Enhance Learning
- Elizabeth Ligon Bjork & Robert A. Bjork, 2011, dalam Psychology and the Real World: Essays Illustrating Fundamental Contributions to Society (M. A. Gernsbacher, R. W. Pew, L. M. Hough, J. R. Pomerantz, Eds.), Worth Publishers. DOI: tidak tersedia (buku bab tanpa DOI), URL: https://doi.org/10.1037/e669392012-005 (PsycEXTRA terkait) / OpenAlex W2463230187 (675 citations)
- Access: METADATA (OpenAlex record dengan abstract singkat; tidak ada DOI — dicatat apa adanya, tidak dikarang).
- Temuan kunci: (1) Pembelajar mudah tertipu tentang efektivitas belajarnya sendiri (impresi subjektif ≠ learning aktual). (2) Kondisi yang tampaknya mempercepat akuisisi sering tidak mendukung retensi jangka panjang; desirable difficulties (spacing, testing, interleaving, variasi konteks) menghasilkan learning yang lebih tahan lama dan lebih mudah ditransfer.
- Keterbatasan: chapter sintesis populer-ilmiah (bukan studi empiris baru); tidak ada DOI resmi — sitasi perlu memakai informasi buku asli.
- Relevansi: dasar klaim desain: sistem automated memory sebaiknya sengaja mempertahankan "difficulty" yang produktif, bukan menghaluskan semua hambatan.

## [T1-SW88] Cognitive Load During Problem Solving: Effects on Learning
- John Sweller, 1988, Cognitive Science 12(2):257-285. DOI: 10.1207/s15516709cog1202_4, URL: https://doi.org/10.1207/s15516709cog1202_4
- Access: ABSTRACT (CrossRef — abstract lengkap; 7008 citations).
- Temuan kunci: (1) Means-ends problem solving konvensional mengonsumsi kapasitas pemrosesan kognitif besar sehingga tidak tersedia untuk schema acquisition. (2) Skema (domain-specific schemas) adalah pembeda utama expert vs novice. (3) Dasar Cognitive Load Theory: kapasitas working memory terbatas; desain instruksi harus mengelola beban kognitif.
- Keterbatasan: kerangka diusulkan untuk problem solving/instruksi (bukan memori jangka panjang/retensi); kritik modern soal pengukuran cognitive load.
- Relevansi: batasan desain: sistem adaptive tidak boleh membebani working memory berlebih (mis. review yang terlalu padat/multitasking) — trade-off dengan desirable difficulties.

## [T1-SW11] Cognitive Load Theory (chapter)
- John Sweller, 2011, dalam Psychology of Learning and Motivation Vol. 55 (J. P. Mestre & B. H. Ross, Eds.), Elsevier, pp. 37-76. DOI: 10.1016/B978-0-12-387691-1.00002-8, URL: https://doi.org/10.1016/B978-0-12-387691-1.00002-8
- Access: METADATA (CrossRef — Elsevier chapter, 1597 citations). Abstract tidak tersedia; teks penuh tidak dibaca sesi ini.
- Temuan kunci (metadata terverifikasi): tinjauan lengkap Cognitive Load Theory (elemen interaktivitas, intrinsic/extraneous/germane load, worked-example effect) — versi modern yang diperbarui dari Sweller 1988.
- Keterbatasan: akses metadata-only sesi ini.
- Relevansi: referensi modern CLT untuk membingkai trade-off beban kognitif dalam desain adaptive review.

## [T1-SLP13] About Sleep's Role in Memory
- Björn Rasch & Jan Born, 2013, Physiological Reviews 93(2):681-766. DOI: 10.1152/physrev.00032.2012, URL: https://doi.org/10.1152/physrev.00032.2012
- Access: ABSTRACT (CrossRef — abstract lengkap; 2462 citations).
- Temuan kunci: (1) Tidur berperan AKTIF (bukan pasif) dalam konsolidasi memori: system consolidation — reaktivasi representasi memori saat slow-wave sleep (SWS) mentransformasi memori hippocampus-dependent untuk integrasi ke long-term store; REM sleep menstabilkan. (2) Otak tidur dioptimalkan untuk konsolidasi; otak terjaga untuk encoding. (3) Prinsip offline consolidation berlaku lintas sistem (termasuk non-hippocampal dan imunologis).
- Keterbatasan: sebagian besar bukti mekanistik dari model hewan/paradigma lab; ukuran efek perilaku bervariasi; tidak ada resep praktis penjadwalan review berbasis tidur.
- Relevansi: "automated memory" manusia tidak hanya soal jadwal tampil — proses offline (tidur) ikut menentukan retensi; implikasi: jadwal review yang menabrak waktu tidur (mis. belajar larut malam) kurang optimal.

## [T1-LAT21] A Meta-Analytic Review of the Benefit of Spacing out Retrieval Practice Episodes on Retention
- Alice Latimier, Hugo Peyre, Franck Ramus, 2021, Educational Psychology Review 33(3):959-987. DOI: 10.1007/s10648-020-09572-8 (online 7 Okt 2020), URL: https://doi.org/10.1007/s10648-020-09572-8 (preprint: 10.31234/osf.io/kzy7u)
- Access: METADATA (CrossRef — versi terbit) + ABSTRACT (preprint PsyArXiv, 29 studi).
- Temuan kunci: (1) Meta-analisis 29 studi tentang manfaat **menspasikan episode retrieval practice** (kombinasi dua desirable difficulties: retrieval + spacing) terhadap retensi akhir. (2) Spacing out episode retrieval practice meningkatkan retensi vs massed; menganalisis parameter jadwal (lag, jumlah sesi). (3) Bukti langsung bahwa interaksi spacing×retrieval itu produktif dan dapat diukur meta-analitik.
- Keterbatasan: jumlah studi terbatas (29); variabilitas protokol antar studi; fokus materi verbal sederhana.
- Relevansi: meta-analisis mutakhir (2020-2026) yang paling dekat dengan skenario automated memory: jadwal review + retrieval practice digabung.

## [T1-AGR21] Retrieval Practice Consistently Benefits Student Learning: A Systematic Review of Applied Research in Schools and Classrooms
- Pooja K. Agarwal, Ludmila D. Nunes, Janell R. Blunt, 2021, Educational Psychology Review 33(4):1409-1453. DOI: 10.1007/s10648-021-09595-9, URL: https://doi.org/10.1007/s10648-021-09595-9 (preprint: 10.31234/osf.io/xe9kv)
- Access: METADATA (CrossRef) + ABSTRACT (preprint PsyArXiv — 156 citations versi jurnal).
- Temuan kunci: (1) Skrining ~2.000 abstrak; 50 eksperimen kelas dikode, 49 effect sizes, total n=5.374; mayoritas (57%) menunjukkan manfaat retrieval practice medium-besar. (2) Manfaat konsisten lintas jenjang pendidikan, bidang, desain, format tes, delay, dan timing feedback. (3) Peringatan: hanya 6% eksperimen di negara non-WEIRD.
- Keterbatasan: hanya riset terapan sekolah/kelas (bukan lab); bias WEIRD kuat; kualitas studi bervariasi.
- Relevansi: bukti ekologis retrieval practice di konteks nyata; sekaligus caveat generalisasi lintas budaya untuk sistem AI pendidikan.

## [T1-BAC25] Harnessing Generative AI to Boost Active Retrieval and Retention in MOOCs with Spaced Repetition
- Younes-Aziz Bachiri, Hicham Mouncif, Belaid Bouikhalene, 2025, Knowledge Management & E-Learning: An International Journal (KM&EL). DOI: 10.34105/j.kmel.2025.17.018, URL: https://doi.org/10.34105/j.kmel.2025.17.018
- Access: ABSTRACT (CrossRef — abstract lengkap; 2 citations).
- Temuan kunci: (1) Sistem berbasis GenAI yang menghasilkan learning cards untuk active recall + spaced repetition di MOOC. (2) Hasil uji dengan mahasiswa & instruktur: peningkatan retensi memori dan kepuasan; expert review menilai kartu akurat dan relevan. (3) Tantangan yang diidentifikasi: personalisasi dan kompleksitas bahasa.
- Keterbatasan: uji skala kecil (pilot); kepuasan/self-report; belum ada perbandingan RCT dengan jadwal non-adaptif.
- Relevansi: contoh langsung "automated memory + research agent" di konteks pendidikan digital: AI menghasilkan materi retrieval, jadwal spacing; validasi awal keterpakaian.

## [T1-YAN16] Memory and Metamemory Considerations in the Instruction of Human Beings Revisited: Implications for Optimizing Online Learning
- Veronica X. Yan, Courtney M. Clark, Robert A. Bjork, 2016, dalam Remembering: Attributions, Processes, and Control in Human Memory (D. S. Lindsay et al., Eds.), Routledge. DOI: 10.4324/9781315625737-12, URL: https://doi.org/10.4324/9781315625737-12
- Access: ABSTRACT (OpenAlex — abstract lengkap) + METADATA.
- Temuan kunci: (1) Pengembang learning technology (dan pembelajar/instruktur) sering tidak memahami strategi apa yang efektif untuk long-term learning. (2) Kondisi yang mendukung akuisisi cepat & performa tinggi saat training sering TIDAK mendukung retensi jangka panjang — berlaku juga untuk modul online yang "fun and easy". (3) Merujuk Bjork et al. (2013) & Soderstrom & Bjork (2015) untuk review.
- Keterbatasan: chapter konseptual; contoh platform online terbatas (pra-LLM).
- Relevansi: jembatan desirable difficulties → desain teknologi pembelajaran online; argumen untuk "jangan optimalkan kemudahan" dalam sistem adaptive.

## [T1-MUR25] A Meta-Analytic Review of the Effectiveness of Spacing and Retrieval Practice for Mathematics Learning (COUNTEREVIDENCE)
- Ewan Murray, Silke Melanie Goebel, Aidan J. Horner, 2025, preprint OSF. DOI: 10.31219/osf.io/wdahf_v1, URL: https://doi.org/10.31219/osf.io/wdahf_v1
- Access: ABSTRACT (CrossRef — preprint 30 Jul 2025; full text OA di OSF).
- Temuan kunci: (1) Spacing vs massed untuk matematika: g = 0.26 (25 studi, 49 efek) — efek kecil-sedang; lebih besar untuk materi terisolasi (g=0.38) daripada dalam course (g=0.24). (2) Testing vs restudy: g = 0.22 dengan 95% CI melewati nol → **testing effect tidak robust** di domain matematika (6 studi, 20 efek). (3) Efek mungkin lebih kecil daripada domain lain.
- Keterbatasan: preprint (belum peer-review); jumlah studi testing kecil; matematika ≠ semua domain.
- Relevansi: counterevidence penting — jangan mengklaim testing/spacing berlaku seragam; sistem adaptive perlu kalibrasi per domain/materi.

## [T1-HIN14] Retrieval (Sometimes) Enhances Learning: Performance Pressure Reduces the Benefits of Retrieval Practice (COUNTEREVIDENCE)
- Scott R. Hinze & David N. Rapp, 2014, Applied Cognitive Psychology 28(4):597-606. DOI: 10.1002/acp.3032, URL: https://doi.org/10.1002/acp.3032
- Access: ABSTRACT (CrossRef — abstract lengkap; 53 citations).
- Temuan kunci: (1) Kuis high-stakes (tekanan performa) → performa final test lebih buruk daripada kuis low-stakes; hanya kuis low-stakes yang unggul atas kontrol rereading. (2) Performa kuis itu sendiri setara antar kondisi (siswa beradaptasi), tapi manfaat retensi hilang di bawah tekanan. (3) Manfaat retrieval practice dapat terganggu oleh kondisi bertekanan.
- Keterbatasan: 2 eksperimen lab; tekanan dimanipulasi via stakes kuis; domain materi teks.
- Relevansi: peringatan desain: retrieval practice di sistem digital harus low-stakes (tanpa konsekuensi/penilaian menekan) agar manfaatnya muncul.

---

## Ringkasan klaim learning science yang dapat dikutip
1. **Kurva lupa & spacing**: retensi meluruh eksponensial setelah belajar (Ebbinghaus, 1885); distributed practice secara robust meningkatkan retensi jangka panjang, dan ISI optimal bertambah seiring panjangnya retention interval yang ditargetkan (Cepeda et al., 2006; Dunlosky et al., 2013).
2. **Retrieval practice (testing effect)**: pengujian berulang setelah suatu item berhasil diproduksi meningkatkan delayed recall secara besar, sedangkan studi ulang tidak; mahasiswa tidak menyadari hal ini (Karpicke & Roediger, 2008). Practice testing + distributed practice = teknik ber-utility tertinggi (Dunlosky et al., 2013), konsisten di riset kelas (Agarwal et al., 2021).
3. **Desirable difficulties & metamemory**: kondisi yang memperlambat akuisisi tampak (spacing, testing, interleaving) meningkatkan retensi jangka panjang; judgment pembelajar tentang learning-nya sendiri tidak reliabel (Bjork, 1994; Bjork & Bjork, 2011) — implikasi: sistem otomatis perlu memutuskan jadwal, bukan menyerahkan ke self-assessment user.
4. **Penjadwalan optimal sebagai masalah optimasi**: model memori empiris (retensi ↑ dengan reinforcement, ↓ dengan delay) dapat diformalkan; penjadwalan review = masalah optimasi yang solvable (queueing/Leitner: Reddy et al., 2016; stochastic shortest path dengan model Markov dari 220M log: Ye et al., 2022, FSRS, +12.6% vs SOTA).
5. **Batasan kognitif & proses offline**: kapasitas working memory membatasi akuisisi skema (Sweller, 1988); konsolidasi memori berlanjut secara aktif saat tidur (SWS reactivation; Rasch & Born, 2013) — desain jadwal adaptive harus menghormati keduanya.

## Counterevidence / keterbatasan yang harus disebut
- **Testing effect tidak seragam antar domain**: untuk matematika g=0.22 dengan CI melewati nol (tidak robust; Murray et al., 2025, preprint) — klaim "testing selalu menang" tidak aman.
- **Tekanan merusak manfaat retrieval**: manfaat retrieval practice hilang pada kondisi high-stakes/bertekanan (Hinze & Rapp, 2014) → sistem harus low-stakes.
- **Bias WEIRD & heterogenitas efek**: hanya 6% eksperimen retrieval practice di kelas dari negara non-WEIRD (Agarwal et al., 2021); meta-analisis spacing menunjukkan heterogenitas besar dan efek lebih kecil di beberapa domain (Latimier et al., 2021; Murray et al., 2025).
- **Data klasik terbatas**: Ebbinghaus n=1 pada nonsense syllables (generalizability rendah); efek spacing/retrieval paling kuat diukur pada retensi verbal sederhana, bukan pemahaman kompleks.
