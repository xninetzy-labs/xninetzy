# 08 — Outline Makalah (10-final-paper.md)

Format: naskah akademik Bahasa Indonesia, A4, Times New Roman 12pt, spasi 1.5, sitasi APA 7, target ≥ 50 halaman PDF (≈ 18.000–22.000 kata).

## HALAMAN COVER (hal. i)
- Judul: "Implementasi Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent untuk Meningkatkan Personalisasi, Retensi Pengetahuan, dan Efektivitas Proses Belajar"
- (Placeholder identitas — user harus mengisi sendiri; TIDAK dikarang)

## ABSTRAK (hal. ii, 200–300 kata ID + EN)
- Latar, metode (desain arsitektur berbasis literatur), hasil utama rancangan, rekomendasi, kata kunci: adaptive learning; automated memory; spaced repetition; research agent; RAG; knowledge graph; human-in-the-loop.

## DAFTAR ISI + DAFTAR GAMBAR + DAFTAR TABEL

## BAB I PENDAHULUAN (≈2.500 kata)
1.1 Latar Belakang — kurva lupa & retrieval practice (Ebbinghaus 1913; Karpicke & Roediger 2008; Dunlosky 2013; Cepeda 2006); gap 2 sigma & ITS (Bloom 1984; VanLehn 2011; Ma 2014); LLM memory & research agent (Park 2023; MemGPT; mem0; RAG); masalah: memori statis, tidak adaptif, sumber tidak terverifikasi.
1.2 Rumusan Masalah (RQ1–RQ8 dari 01-research-questions.md)
1.3 Tujuan Penelitian (8 tujuan sesuai RQ)
1.4 Manfaat Penelitian (teoretis, praktis, kebijakan)
1.5 Batasan Penelitian (tidak ada eksperimen nyata; desain berbasis literatur; Bahasa Indonesia; studi kasus Xninetzy OS)

## BAB II TINJAUAN PUSTAKA (≈7.000 kata)
2.1 Landasan Kognitif Pembelajaran (2.1.1 kurva lupa & spacing; 2.1.2 retrieval practice & desirable difficulties; 2.1.3 beban kognitif & konsolidasi tidur) — T1
2.2 Penjadwalan Ulasan Otomatis (2.2.1 SM-2; 2.2.2 HLR; 2.2.3 FSRS/SSP; perbandingan tabel) — T1/T2/T6
2.3 Sistem Tutor Cerdas & Adaptive Learning (2.3.1 ITS & effect size; 2.3.2 knowledge tracing BKT/DKT/AKT; 2.3.3 concept graph & prerequisite) — T2
2.4 Automated Memory untuk Agent LLM (2.4.1 memory stream & reflection; 2.4.2 virtual context management; 2.4.3 extract-update pipeline; 2.4.4 kerangka M_sys dan 9 temuan desain; 2.4.5 forgetting & maintenance; perbandingan tabel sistem) — T3
2.5 Retrieval-Augmented Generation & Research Agent (2.5.1 paradigma RAG; 2.5.2 GraphRAG & knowledge graph pendidikan; 2.5.3 agentic RAG & riset otomatis) — T4
2.6 Evaluasi, Etika, Privasi, dan HITL (2.6.1 evaluasi groundedness & hallucination; 2.6.2 privasi & MIA/poisoning; 2.6.3 etika & human-in-the-loop) — T5
2.7 Penelitian Terdahulu & Posisi Riset (tabel perbandingan; research gap G1–G5 dari 07-research-gap.md)

## BAB III METODE DAN PERANCANGAN (≈5.500 kata)
3.1 Metode Penelitian (design science research / prototype-based; alur: analisis literatur → pemetaan kebutuhan → arsitektur → validasi pakar → keterbatasan)
3.2 Arsitektur Umum Sistem (Gambar system-architecture) + deskripsi 6 lapisan
3.3 Siklus Belajar Adaptif (Gambar adaptive-learning-loop; langkah Assess→Model→Gap→Research→Plan→Teach→Practice→Evaluate→Reflect→Consolidate→Adapt)
3.4 Perancangan Automated Memory (modul; memory lifecycle Gambar memory-lifecycle; representasi; policy konservatif; scheduler DSR formula FSRS; integrasi dengan recall)
3.5 Perancangan Research Agent (sub-agen: web/paper/video/verifier/synthesizer; alur sequence Gambar agent-sequence; kriteria verifikasi sumber)
3.6 Perancangan Evaluasi (3.6.1 skenario uji yang diusulkan — simulasi kurva retensi; 3.6.2 metrik: retention rate, mastery, groundedness, citation validity, latency, token cost; 3.6.3 instrument kuesioner yang diusulkan)
3.7 Etika & HITL (tier approval; minimalisasi data; origin provenance)

## BAB IV ANALISIS DAN PEMBAHASAN (≈4.500 kata)
4.1 Pemetaan Kebutuhan → Komponen (tabel)
4.2 Analisis Desain terhadap Literatur (tabel perbandingan desain vs 9 findings Zhou 2026; vs FSRS; vs mem0)
4.3 Studi Kasus: Penerapan pada Xninetzy OS (komponen nyata terverifikasi — dari 06-technical-notes.md; TIDAK mengarang; gap FSRS→SM-2 diakui)
4.4 Skenario Pengujian yang Diusulkan (3 skenario + hipotesis H1–H3)
4.5 Analisis Risiko & Mitigasi (tabel risiko: hallucination, privacy MIA/poisoning, over-reliance, bias)
4.6 Keterbatasan Penelitian
4.7 Implikasi (praktis, teoretis, arah riset lanjutan)

## BAB V PENUTUP (≈700 kata)
5.1 Kesimpulan (menjawab RQ1–RQ8)
5.2 Saran

## DAFTAR PUSTAKA (semua 63 entri references.bib, APA 7, alfabetis)

## LAMPIRAN (bila muat)
- Lampiran A: Daftar sumber dengan status akses (ringkas)
- Lampiran B: Rincian parameter FSRS/SM-2 (dari 06-technical-notes.md)

## Gambar (4): system-architecture, adaptive-learning-loop, agent-sequence, memory-lifecycle
## Tabel (≥8): perbandingan scheduler, effect size ITS, perbandingan sistem memory, 9 findings, pemetaan kebutuhan, risiko, skenario, dll.

## Konvensi penulisan
- Sitasi APA: (Penulis, Tahun). Semua klaim angka harus merujuk entri source matrix; angka dari abstract-only diberi catatan "berdasarkan abstrak".
- Bahasa rancangan untuk yang belum diuji: "diusulkan", "dirancang", "skenario", "hipotesis", "expected".
- Dilarang mengarang: nama, NIM, data eksperimen, kutipan halaman, angka yang tidak ada di notes.
