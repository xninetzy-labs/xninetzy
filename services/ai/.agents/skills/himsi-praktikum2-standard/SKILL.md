---
name: himsi-praktikum2-standard
description: SOP Praktikum 2 Redesain Web HIMSI UNAIR — ambil-pahami, planning, rancang, standarisasi riset dan build yang konsisten (tanpa skor teknis, tanpa BAB prefix, tanpa Daftar Pustaka/Lampiran).
metadata:
  owner: xninetzy
  version: "1.1.0"
---

# HIMSI Praktikum 2 — SOP Standar (ambil, pahami, planning, rancang, riset, build)

Proses baku untuk semua tugas Desain Interaksi Praktikum SII209 agar konsisten ke depan. Menggantikan v1.0.0 dengan penambahan langkah terstandar.

## 0. Standarisasi Riset & Build
- Riset: pahami materi dari Obsidian SII209, knowledge, memory, graph, lightning, dan video/yt-transcribe terkait Figma dan 9 prinsip
- Build: selalu pakai pipeline xninetzy-academic-artifact-pipeline (A4 2.3/2.5cm, Times New Roman hitam 12pt justify 1.15, H1 24 H2 16 H3 13, tabel D9D9D9, no header/footer, cover tanpa Dosen)

## 1. Ambil
- Ambil 6 halaman HIMSI UNAIR (Home, About Us, Akademik, Form, Curhat, Kritik Saran) via Playwright 1440x900
- Ambil tangkapan asli ke captures/himsi/ 6 PNG
- Ambil desain Figma Praktikum 2 Redesain Web HIMSI UNAIR https://www.figma.com/design/222hf7ewz9fCwjcHhWq88L/Untitled?node-id=8-3&p=f&t=srOsQuABJKV2gEEH-0 — ekspor 6 frame terpisah ke captures/figma/ (home, about, akademik, form, curhat, kritik), bukan 1 page full, judul bukan Untitled

## 2. Pahami
- Pahami Modul 1: Figma Frame, Grids 8-poin/960-poin, Shape Tools, kolaborasi real-time
- Pahami Modul 2: 9 prinsip (Tujuan, Informasi, Teks, Warna, Gambar, Navigasi, Layout, Pola F, Feedback) secara kualitatif tanpa angka skor Playwright
- Pahami materi via Obsidian, knowledge_search, graph_v3_search, dan OCR screenshot Figma (baca tiap frame untuk cek hero, stats, misi, layanan, berita, departemen, badge, tab/stepper, privacy)

## 3. Planning
- Tentukan struktur: PENDAHULUAN (1.1 Latar Belakang, 1.2 Tujuan Praktikum sesuai Modul, 1.3 Lingkup), PEMBAHASAN (2.1-2.6 per halaman asli, 2.7 Design System Global, 2.8 Rencana Redesain 2.8.1-2.8.6 before-after per 9 prinsip), KESIMPULAN, tautan Figma di bawah
- Tanpa prefix BAB (judul langsung PENDAHULUAN/PEMBAHASAN/KESIMPULAN), tanpa Daftar Pustaka/Lampiran, tanpa skor tabel Ringkasan Skor
- Siapkan TOC tanpa kalimat instruksi update manual

## 4. Rancang
- Rancang Design System global: Primary dari logo, Accent konsisten, semantic success/warning/error/info, tipografi Sans Serif H1 36-40 H2 24-28 dll, komponen Header sticky (dropdown Layanan), Footer sinkron, Card/Button/Feedback/Stepper konsisten

## 5. Build
- Generate DOCX via report/build_himsi_report.py (Times New Roman hitam, justify) → UNO PDF → QA (no header/footer, cover 5.5cm logo tanpa Dosen, no em dashes, file exists) → kirim DOCX+PDF ke admin via wa-media http://127.0.0.1:8899/
- Filename HEBAT: NIM_DITI2.pdf (187241037_DITI2.pdf) dari 187241037_DITI2_HIMSI.docx → siapkan via hebat_prepare_submission dan submit ke assign 121515

## 6. Kirim & Konsistensi
- Simpan pemahaman ini ke memory #162 dan skill ini agar pengerjaan selanjutnya langsung konsisten
- Sinkronkan skill ini dari opencode (~/.config/opencode/skills) ke code/xninetzy/services/ai/.agents/skills dan code/xninetzy/.agents/skills
- MCP dapat dipakai siapapun ke depan karena skill tersinkron di repo code/xninetzy dan opencode, dengan instruksi ambil-pahami-planning-rancang-riset-build yang terdokumentasi
