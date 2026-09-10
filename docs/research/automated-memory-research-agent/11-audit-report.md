# Laporan Audit Adversarial — `10-final-paper.md`

- **Objek audit:** `docs/research/automated-memory-research-agent/10-final-paper.md` (857 baris)
- **Tanggal audit:** 2026-08-03
- **Metode:** inspeksi read-only baris-per-baris; verifikasi silang terhadap `03-source-matrix.csv`, `04-literature-notes-t1..t5`, `06-technical-notes.md`, `09-draft-bab1..4.md`, `09-daftar-pustaka.md`, dan repository Xninetzy OS (`services/ai/app/xninetzy/domains/it_learning/recall.py`).
- **Verdict: REVISE** — kualitas substansi tinggi dan kejujuran ilmiah terjaga, tetapi terdapat inkonsistensi internal (RQ, definisi M_sys) dan masalah sitasi yang harus diperbaiki sebelum dokumen dianggap final.

---

## 1. Ringkasan Eksekutif

Dokumen ini adalah rancangan arsitektur (design paper) yang **tidak mengklaim hasil eksperimen** — seluruh bagian evaluasi bersifat ex-ante dan dinyatakan eksplisit. Dari 12 kategori audit, 9 kategori lulus tanpa temuan material; 3 kategori memiliki temuan yang harus diperbaiki:

| Kategori | Status |
|---|---|
| 1. Kualitas sumber | ✅ Lulus (transparansi preprint vs peer-reviewed) |
| 2. Status akses | ✅ Lulus (status akses dicatat per sumber) |
| 3. Klaim vs repository | ✅ Lulus (FSRS tidak diklaim terpasang) |
| 4. Formula/implementasi | ✅ Lulus (SM-2 cocok dengan kode) |
| 5. Bahasa hasil | ✅ Lulus (tidak ada hasil palsu) |
| 6. Konsistensi RQ | ⚠️ **3 mismatch RQ di BAB III** |
| 7. Konsistensi definisi | ⚠️ **M_sys salah dipetakan di §3.4.1** |
| 8. Sitasi | ⚠️ **1 sitasi tanpa entri; 2 entri tanpa sitasi** |
| 9. Statistik/angka | ✅ Lulus (konsisten lintas dokumen) |
| 10. Data pribadi vs eksternal | ✅ Lulus (studi kasus dilabeli jelas) |
| 11. Kutipan | ✅ Lulus (terlacak ke catatan literatur) |
| 12. Pelabelan inferensi | ✅ Lulus (sintesis vs fakta dipisah) |

**Temuan terparah (wajib diperbaiki):**
1. §3.4.3 (baris 423) menyatakan penjadwal ulasan "menjawab RQ2" — seharusnya **RQ5**.
2. §3.5 (baris 488) menyatakan research agent "menjawab RQ5" — seharusnya **RQ2**.
3. §3.6 (baris 531) menyatakan rancangan evaluasi "menjawab RQ8" — seharusnya **RQ5**.
4. §3.4.1 (baris 391) memetakan M_sys = ⟨R,S,Q,U⟩ sebagai retrieval/storage/quality/update — bertentangan dengan §2.4.4 (baris 211) dan matriks T3-06 (R=Representation & Storage, S=Extraction, Q=Retrieval & Routing, U=Maintenance).
5. Sitasi "Yeung dan Yeung (2018)" (baris 185) **tidak memiliki entri** di daftar pustaka.
6. Entri "Mem0 AI (2025)" (baris 831) dan "Xninetzy OS (2026)" (baris 849) **tidak pernah disitasi** dalam bentuk author-date di tubuh dokumen.

---

## 2. Temuan per Kategori

### KATEGORI 1 — Kualitas sumber ✅
- **Positif:** §4.6 (baris 753) mengakui keseimbangan preprint vs peer-reviewed: sembilan temuan desain Zhou et al. (2026), mem0 (Chhikara et al., 2025), FSFM (Gu et al., 2026), SimpleMem (Liu et al., 2026) adalah preprint; A-MEM (Xu et al., 2025) sudah diterima NeurIPS 2025 dan MemoryBank (Zhong et al., 2024) di AAAI 2024.
- **Positif:** Baris 755 mengakui indikasi bias publikasi (studi bersampel kecil cenderung melaporkan efek lebih besar; Wang et al., 2026).
- **Positif:** Baris 753 mengakui heterogenitas dan konflik angka antar benchmark (LoCoMo vs LongMemEval; mem0 vs Zhou et al. pada metrik berbeda).

### KATEGORI 2 — Status akses (access status)
- **Positif:** Baris 314 menyatakan "Setiap sumber dicatat status aksesnya karena status akses menentukan tingkat keyakinan klaim".
- **Positif:** Baris 521 menyatakan klaim dari abstrak/metadata dicatat dengan kualifikasi dan tidak digunakan sebagai dasar keputusan konsekuensial.
- **Catatan:** Tidak ada klaim yang dipresentasikan sebagai full-text padahal hanya abstrak — tidak ditemukan pelanggaran.

### KATEGORI 3 — Klaim vs repository
- **Positif:** Baris 691 menegaskan repository **tidak mengimplementasikan FSRS**; implementasi nyata adalah varian SM-2, dan setiap klaim menyebut "SM-2-style". Ini konsisten dengan inspeksi `recall.py::_next_schedule`.
- **Positif:** Baris 707 menyatakan mem0 belum terpasang di repository; perbandingan eksperimental dengan mem0 adalah rancangan (S3), bukan hasil.
- **Positif:** Baris 679 menyatakan seluruh komponen studi kasus terverifikasi melalui inspeksi read-only pada 2026-08-03 dan dicatat di technical notes 06 — "tidak ada fitur yang dikarang".

### KATEGORI 4 — Formula/implementasi
- **Positif:** Baris 689 mendeskripsikan `_next_schedule` sebagai implementasi langsung pola SM-2 (ease factor batas bawah 1,3; interval 1, 6, lalu `round(prev * ease)`; kualitas < 3 mereset repetitions; rumus ease identik SM-2). Ini cocok dengan kode aktual.
- **Positif:** Baris 156 dan 425–429 menyajikan formula FSRS-6 (R(t,S) = (1 + factor·t/S)^(−w20), factor = 0.9^(−1/w20) − 1) sebagai kerangka acuan, bukan klaim implementasi.

### KATEGORI 5 — Bahasa hasil (tidak ada hasil palsu)
- **Positif:** Baris 531: "Karena penelitian ini tidak melaksanakan eksperimen nyata, seluruh rancangan pada bagian ini bersifat ex-ante… Tidak ada data hasil yang dilaporkan pada bagian ini."
- **Positif:** Baris 609: "seluruh klaim yang menyangkut kinerja sistem di masa depan dinyatakan sebagai hipotesis dan rancangan, bukan hasil eksperimen."
- **Positif:** Baris 723 dan 729 menggunakan label "Keluaran yang diharapkan (expected)" untuk H2 dan H3.

### KATEGORI 6 — Konsistensi RQ ⚠️
**Temuan 6.1 (baris 423, §3.4.3):** "Penjadwal ulasan merupakan komponen kunci untuk menjawab **RQ2**" — padahal penjadwalan ulasan/retensi adalah **RQ5** (Tabel 4.1 baris 630: "Mengukur efektivitas sistem pada retensi, pemahaman, efisiensi, dan personalisasi (RQ5)"). RQ2 adalah research agent.

**Temuan 6.2 (baris 488, §3.5):** "Modul research agent dirancang untuk menjawab **RQ5**" — padahal research agent adalah **RQ2** (Tabel 4.1 baris 623: "Mengumpulkan, mengevaluasi, dan menyintesis materi (RQ2)").

**Temuan 6.3 (baris 531, §3.6):** "Rancangan evaluasi menjawab **RQ8**" — padahal kerangka evaluasi dual adalah **RQ5** (Tabel 4.1 baris 630). RQ8 adalah human-in-the-loop.

- **Catatan:** Kesalahan yang sama sudah ada di `09-draft-bab3.md` (sekitar baris 130 dan 195), sehingga ini **bukan regresi integrasi** melainkan error persisten dari draft.
- **Positif:** §5.1 (baris 777–783) menyajikan delapan kesimpulan yang menjawab RQ1–RQ8 secara berurutan dan konsisten dengan daftar RQ di §1.2 (baris 62–69) serta Tabel 4.1.

### KATEGORI 7 — Konsistensi definisi ⚠️
- **Temuan 7.1 (baris 391, §3.4.1):** "Representasi memori mengikuti kerangka empat modul M_sys = ⟨R, S, Q, U⟩ yang membedakan modul **retrieval (R), storage (S), quality (Q), dan update (U)**".
  - Bertentangan dengan §2.4.4 (baris 211): "(R) representasi dan penyimpanan memori, (S) ekstraksi, (Q) retrieval dan perutean, (U) pemeliharaan".
  - Bertentangan dengan matriks sumber T3-06 (Zhou et al., 2026).
  - Dampak: pembaca §3.4.1 mendapat definisi yang salah tentang makna keempat modul; modul "quality" dan "update" tidak ada dalam taksonomi sumber.
- **Positif:** Baris 765 (Bab V) menyebut "Formalisasi M_sys = ⟨R, S, Q, U⟩ (Zhou et al., 2026)" tanpa salah memetakan — konsisten dengan §2.4.4.

### KATEGORI 8 — Sitasi ⚠️
- **Temuan 8.1 (sitasi tanpa entri):** "Yeung dan Yeung (2018)" disitasi di baris 185 (dua masalah konsistensi DKT) tetapi **tidak ada entri** di daftar pustaka (baris 795–857). Ini satu-satunya sitasi tanpa entri yang terdeteksi.
- **Temuan 8.2 (entri tanpa sitasi):** "Mem0 AI. (2025)" (baris 831) tidak pernah disitasi dalam bentuk author-date di tubuh dokumen; tubuh selalu merujuk "mem0 (Chhikara et al., 2025)".
- **Temuan 8.3 (entri tanpa sitasi):** "Xninetzy OS. (2026)" (baris 849) tidak pernah disitasi sebagai "(Xninetzy OS, 2026)"; tubuh merujuk studi kasus dengan "T6-06" (technical notes) dan nama sistem tanpa tahun.
- **Positif (disambiguasi Huang):** Kedua entri Huang tersitasi — "Huang, X., Xu, dan Liu (2025)" (meta-analisis ITS, entri baris 818) disitasi di baris 179 (k = 30, g = 0.86), 269, dan 755; "Huang et al. (2025)" (survei hallucination ACM TOIS, entri baris 817) disitasi di baris 624, 740, 779. Tidak ada entri Huang yang orphan.
- **Positif:** Yan, Clark, dan Bjork (2016) disitasi di baris 130 — bukan orphan.
- **Positif:** Anki (2024), Ye et al. (2023), Wozniak (1990), Wang et al. (2026) semuanya tersitasi.

### KATEGORI 9 — Statistik/angka
- **Positif:** Cepeda et al. (2006): "839 pengukuran distributed practice dari 317 eksperimen" konsisten di baris 42 dan 122.
- **Positif:** Ma et al. (2014): "107 ukuran efek dengan 14.321 partisipan" konsisten di baris 46 dan 179; g = 0.42/0.57/0.35/−0.11 konsisten.
- **Positif:** Kulik & Fletcher (2016): median 0.66 dari 50 evaluasi terkontrol (baris 179).
- **Positif:** Xu et al. (2019): 0.60 (95% CI 0.36–0.85), campuran 0.86 vs terstandar 0.26 (baris 179).
- **Positif:** Huang-Xu-Liu (2025): k = 30, g = 0.86 (baris 179).
- **Positif:** Piech et al. (2015): AUC 0.86 vs 0.69 (Assistments), 0.85 vs 0.68 (Khan Academy) (baris 185).
- **Positif:** Chen et al. (2026): gray-box TPR@FPR1% naik 13.5%→55.9% (Mem0) dan 17.3%→63.4% (MemGPT) (baris 259, 741).
- **Positif:** mem0 LoCoMo: overall J Mem0g 68.44, latency p95 1.44 s, token ~7k (baris 207, 227, 661) — konsisten dengan catatan literatur T3.

### KATEGORI 10 — Data pribadi vs eksternal
- **Positif:** Baris 102: "validasi kelayakan teknis dibatasi pada studi kasus Xninetzy OS, sebuah sistem personal learning OS yang berjalan lokal milik penulis" — dilabelasi jelas sebagai data pribadi, bukan bukti eksternal.
- **Positif:** Baris 679: path repository dicatat; seluruh klaim studi kasus dirujuk ke technical notes 06 (T6-06) sebagai sumber internal yang terverifikasi.
- **Positif:** Tidak ada data pribadi pengguna lain yang disebut.

### KATEGORI 11 — Kutipan
- **Positif:** Kutipan langsung tidak ditemukan; seluruh klaim parafrase dengan angka yang dapat dilacak ke catatan literatur (lihat Kategori 9).
- **Catatan:** Tidak ada tanda kutip literal yang perlu verifikasi halaman.

### KATEGORI 12 — Pelabelan inferensi
- **Positif:** Baris 179: "Sintesis yang aman adalah: ITS efektif dengan effect size moderat (kisaran g = 0.32–0.86…)" — inferensi dinyatakan eksplisit.
- **Positif:** Baris 691: "keputusan ini justru sejalan dengan bukti…" — inferensi desain dipisahkan dari bukti.
- **Positif:** Baris 531 dan 609: seluruh klaim kinerja masa depan dilabeli sebagai hipotesis/rancangan.

---

## 3. Masalah (Issue List)

### Blocking (harus diperbaiki sebelum final)
| ID | Severity | Lokasi | Masalah | Perbaikan |
|---|---|---|---|---|
| B1 | Tinggi | baris 423 | §3.4.3 menyatakan penjadwal ulasan menjawab RQ2 | Ganti menjadi RQ5 |
| B2 | Tinggi | baris 488 | §3.5 menyatakan research agent menjawab RQ5 | Ganti menjadi RQ2 |
| B3 | Tinggi | baris 531 | §3.6 menyatakan evaluasi menjawab RQ8 | Ganti menjadi RQ5 |
| B4 | Tinggi | baris 391 | M_sys dipetakan sebagai retrieval/storage/quality/update | Samakan dengan §2.4.4: R=Representation & Storage, S=Extraction, Q=Retrieval & Routing, U=Maintenance |
| B5 | Sedang | baris 185 | Yeung & Yeung (2018) disitasi tanpa entri daftar pustaka | Tambahkan entri (Yeung, C.-K., & Yeung, D.-Y. (2018). Addressing two problems in deep knowledge tracing…) |
| B6 | Sedang | baris 831 | Entri "Mem0 AI (2025)" tidak pernah disitasi | Hapus entri atau sitasi di tubuh (mis. pada §2.3.3 saat membahas mem0) |
| B7 | Sedang | baris 849 | Entri "Xninetzy OS (2026)" tidak pernah disitasi dalam bentuk author-date | Hapus entri atau tambahkan sitasi "(Xninetzy OS, 2026)" di §4.3 |

### Non-blocking (disarankan)
| ID | Severity | Lokasi | Masalah | Saran |
|---|---|---|---|---|
| N1 | Rendah | baris 320, 328, 701 | Sitasi internal "T6-06" (technical notes) dipakai sebagai sitasi di tubuh | Pertahankan karena sudah didisklosur (baris 679), tetapi pertimbangkan daftar lampiran technical notes di daftar pustaka |
| N2 | Rendah | baris 624, 740, 779 | "Huang et al. (2025)" (survei hallucination) dan "Huang, X., Xu, & Liu (2025)" (ITS) bisa membingungkan pembaca | Pertahankan disambiguasi eksplisit "Huang, X. et al." untuk ITS di semua kemunculan |
| N3 | Rendah | baris 387 | "Modul automated memory dirancang untuk menjawab RQ1–RQ4" — RQ2 (research agent) tidak dicakup modul ini | Pertimbangkan "RQ1, RQ3, RQ4" agar presisi |
| N4 | Rendah | seluruh | Tidak ada kutipan literal; tidak ada halaman | Tidak wajib, tetapi tambahkan halaman jika kutipan literal ditambahkan |

---

## 4. Rekomendasi

1. **Perbaiki 3 mismatch RQ (B1–B3)** dengan mengacu Tabel 4.1 sebagai kanon: RQ2 = research agent, RQ5 = efektivitas/retensi, RQ8 = HITL.
2. **Perbaiki pemetaan M_sys (B4)** di §3.4.1 agar konsisten dengan §2.4.4 dan sumber asli (Zhou et al., 2026).
3. **Lengkapi daftar pustaka (B5)** dengan entri Yeung & Yeung (2018) — verifikasi metadata via sumber primer (paper DKT consistency).
4. **Hapus atau sitasi entri orphan (B6, B7):** "Mem0 AI (2025)" dan "Xninetzy OS (2026)".
5. **Jalankan ulang audit sitasi** setelah perbaikan: pastikan setiap entri daftar pustaka tersitasi minimal sekali dan setiap sitasi memiliki entri.
6. **Pertahankan praktik baik yang sudah ada:** pelabelan ex-ante, transparansi preprint, status akses, dan pemisahan inferensi — ini adalah kekuatan dokumen.

---

## 5. Daftar Entri Tak Tersitasi / Sitasi Tanpa Entri

### Sitasi tanpa entri (cited, missing from daftar pustaka)
| Sitasi | Lokasi | Status |
|---|---|---|
| Yeung & Yeung (2018) | baris 185 | **MISSING** — tidak ada entri di daftar pustaka |

### Entri tanpa sitasi (in daftar pustaka, never cited)
| Entri | Lokasi | Status |
|---|---|---|
| Mem0 AI (2025) | baris 831 | **ORPHAN** — tubuh merujuk Chhikara et al. (2025) |
| Xninetzy OS (2026) | baris 849 | **ORPHAN** — tubuh merujuk T6-06, bukan "(Xninetzy OS, 2026)" |

### Verifikasi positif (bukan orphan)
- Huang, L. et al. (2025) — disitasi (baris 624, 740, 723)
- Huang, X., Xu, & Liu (2025) — disitasi (baris 179, 269, 755)
- Yan, V. X. et al. (2016) — disitasi (baris 130)
- Anki (2024) — disitasi (baris 156, 168, 171, 655)
- Ye et al. (2023) — disitasi (baris 156, 171, 655)
- Wozniak (1990) — disitasi (baris 146, 162, 171, 314, 378, 446, 452, 655, 689, 783)
- Wang et al. (2026) — disitasi (baris 755, 769, 787)
- Seluruh 63 entri lainnya terverifikasi tersitasi (lihat lampiran verifikasi per entri di bawah).

---

## 6. Lampiran — Status Sitasi per Entri Daftar Pustaka

| # | Entri (baris) | Status |
|---|---|---|
| 795 | Abdelmagied et al. (2025) | ✅ disitasi (245, 281, 626) |
| 796 | Agarwal et al. (2021) | ✅ disitasi (44, 269, 622, 769, 787) |
| 797 | Alatrash et al. (2025) | ✅ disitasi (189, 316, 625) |
| 798 | Ali et al. (2024) | ✅ disitasi (249, 269, 623) |
| 799 | Anki (2024) | ✅ disitasi (156, 168, 171, 655) |
| 800 | Bachiri et al. (2025) | ✅ disitasi (275, 284) |
| 801 | Bjork & Bjork (2011) | ✅ disitasi (42, 130, 691) |
| 802 | Bjork (1994) | ✅ disitasi (42, 130) |
| 803 | Bloom (1984) | ✅ disitasi (46, 177) |
| 804 | Cepeda et al. (2006) | ✅ disitasi (42, 122, 314, 365, 630, 729, 781, 787) |
| 805 | Chen et al. (2026) | ✅ disitasi (259, 286, 316, 590, 629, 741, 769, 781, 787) |
| 806 | Chhikara et al. (2025) | ✅ disitasi (205, 227, 269, 280, 284, 314, 408, 661, 729, 753) |
| 807 | Corbett & Anderson (1995) | ✅ disitasi (314, 400, 625, 779) |
| 808 | Dunlosky et al. (2013) | ✅ disitasi (42, 122, 269, 314, 363, 365, 377, 622) |
| 809 | Ebbinghaus (1913) | ✅ disitasi (314) |
| 810 | Edge et al. (2024) | ✅ disitasi (50, 269, 334, 399, 484, 626, 675) |
| 811 | Gao et al. (2023) | ✅ disitasi (50, 269, 334, 482, 527, 547, 623, 675) |
| 812 | Ghosh et al. (2020) | ✅ disitasi (185, 314, 372) |
| 813 | Goddard et al. (2012) | ✅ disitasi (286, 781, 783) |
| 814 | Gu et al. (2026) | ✅ disitasi (478, 586, 753) |
| 815 | Hinze & Rapp (2014) | ✅ disitasi (44, 269, 691, 747, 761, 783) |
| 816 | Holzinger (2016) | ✅ disitasi (286, 314, 747, 783) |
| 817 | Huang, L. et al. (2025) | ✅ disitasi (624, 723, 740, 779) |
| 818 | Huang, X., Xu, & Liu (2025) | ✅ disitasi (179, 269, 755) |
| 819 | Karpicke & Roediger (2008) | ✅ disitasi (42, 128, 269, 314, 363, 365, 377, 622, 691, 761) |
| 820 | Kitto & Knight (2019) | ✅ disitasi (261, 632, 787) |
| 821 | Kulik & Fletcher (2016) | ✅ disitasi (46, 179, 269, 755) |
| 822 | LangChain (2025) | ✅ disitasi (320, 328, 627, 701) |
| 823 | Latimier et al. (2021) | ✅ disitasi (122) |
| 824 | Lewis et al. (2020) | ✅ disitasi (50, 269, 334, 482, 623, 675, 723, 740, 779) |
| 825 | Liu, J. et al. (2026) | ✅ disitasi (753) |
| 826 | Liu, Q., & Khalil (2023) | ✅ disitasi (261, 629, 741) |
| 827 | Louck (2026) | ✅ disitasi (259, 286, 316, 336, 402, 408, 478, 521, 525, 586, 590, 669, 742, 761, 769, 781, 787) |
| 828 | Lu et al. (2024) | ✅ disitasi (249, 269, 284) |
| 829 | Ma et al. (2014) | ✅ disitasi (46, 179, 269, 755) |
| 830 | Maharana et al. (2024) | ✅ disitasi (630, 729, 765, 781, 787) |
| 831 | **Mem0 AI (2025)** | ❌ **ORPHAN** |
| 832 | Miao & Holmes (2023) | ✅ disitasi (286, 314, 484, 747, 761, 783, 787) |
| 833 | Murray et al. (2025) | ✅ disitasi (44, 269, 729, 781) |
| 834 | Packer et al. (2023) | ✅ disitasi (269, 314, 779, 781) |
| 835 | Park et al. (2023) | ✅ disitasi (269, 314, 398, 779, 781) |
| 836 | Piech et al. (2015) | ✅ disitasi (185, 314, 400, 625) |
| 837 | Rasch & Born (2013) | ✅ disitasi (44, 138) |
| 838 | Reddy et al. (2016) | ✅ disitasi (142, 269) |
| 839 | Santoro et al. (2016) | ✅ disitasi (193) |
| 840 | Settles & Meeder (2016) | ✅ disitasi (142, 162, 269, 284, 314, 423, 632) |
| 841 | Singh et al. (2025) | ✅ disitasi (50, 249, 269, 314, 488, 623, 627, 779) |
| 842 | Steenbergen-Hu & Cooper (2014) | ✅ disitasi (46, 179, 269, 755) |
| 843 | Sweller (1988) | ✅ disitasi (44, 136, 376, 397, 747) |
| 844 | Sweller (2011) | ✅ disitasi (136, 376, 397, 747) |
| 845 | Thakur et al. (2021) | ✅ disitasi (249, 484, 547, 626, 723) |
| 846 | VanLehn (2011) | ✅ disitasi (46, 177, 269) |
| 847 | Wang et al. (2026) | ✅ disitasi (755, 769, 787) |
| 848 | Wozniak (1990) | ✅ disitasi (146, 162, 171, 314, 378, 446, 452, 655, 689, 783) |
| 849 | **Xninetzy OS (2026)** | ❌ **ORPHAN** |
| 850 | Xu, W. et al. (2025) | ✅ disitasi (753) |
| 851 | Xu, Z. et al. (2019) | ✅ disitasi (179, 269, 755) |
| 852 | Yan et al. (2016) | ✅ disitasi (130) |
| 853 | Ye et al. (2022) | ✅ disitasi (156, 162, 168, 171, 269, 284, 314, 378, 423, 425, 446, 452, 632, 655, 783, 787) |
| 854 | Ye et al. (2023) | ✅ disitasi (156, 171, 655) |
| 855 | Zhang et al. (2024) | ✅ disitasi (193, 399, 478, 781) |
| 856 | Zhong et al. (2024) | ✅ disitasi (753) |
| 857 | Zhou et al. (2026) | ✅ disitasi (211, 213, 269, 286, 316, 402, 478, 527, 630, 632, 661, 675, 729, 753, 765, 781, 787) |

**Ringkasan sitasi:** 63 entri daftar pustaka; 61 tersitasi, 2 orphan (Mem0 AI, Xninetzy OS); 1 sitasi tanpa entri (Yeung & Yeung, 2018).

---

## 7. Kesimpulan

Dokumen `10-final-paper.md` memiliki kualitas substansi yang baik: kejujuran ilmiah terjaga (tidak ada hasil palsu, FSRS tidak diklaim terpasang, status akses dicatat), statistik konsisten, dan pelabelan inferensi jelas. Namun, **tujuh temuan blocking** (3 mismatch RQ, 1 mismatch definisi M_sys, 1 sitasi tanpa entri, 2 entri tanpa sitasi) mengharuskan **REVISE** sebelum dokumen dianggap final. Perbaikan bersifat mekanis dan tidak mengubah substansi rancangan.

*Laporan ini disusun oleh evidence-auditor pada 2026-08-03 berdasarkan inspeksi read-only. Seluruh nomor baris merujuk `10-final-paper.md` versi saat audit.*