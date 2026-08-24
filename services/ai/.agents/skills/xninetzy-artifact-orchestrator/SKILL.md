---
name: xninetzy-artifact-orchestrator
description: Build long DOCX, PDF, PPTX, and spreadsheet artifacts through staged research, writing, integration, generation, and QA.
metadata:
  owner: xninetzy
  version: "1.4.0"
---

# Artifact Orchestration — General Foundation

Pondasi umum untuk semua artifact HEBAT agar konsisten, MCP dapat dipakai siapapun.

## Pipeline

```text
requirements
-> template analysis
-> source ledger
-> outline or slide architecture
-> bounded section workers
-> integration
-> evidence audit
-> artifact generator
-> physical and visual QA
-> checkpoint
```

## Document contract — GENERAL STANDARD

Define:

* page size: A4 (21.0 x 29.7 cm)
* margins: top/bottom 2.3cm, left/right 2.5cm
* heading hierarchy: H1 24pt bold, H2 16pt bold, H3 13pt bold, all black 000000, Times New Roman
* body: Times New Roman, black 000000, 12pt, justify, line spacing 1.5, widow control
* table header: light gray D9D9D9 text black, fixed layout, cm*567 twips, no wrapping
* caption: 9pt italic 555555 centered
* no header/footer, different_first_page false, no em dashes
* cover: single logo 5.5cm centered — full page dari atas ke bawah, title di atas, logo di tengah (jarak atas 72pt bawah 36pt), Nama|NIM 16pt, Dosen wajib ada (ambil dari memory #163), tanpa icon kelompok (jika berkelompok tulis "Kelompok 4" tanpa daftar anggota, jika perlu daftar pakai 1. NIM Nama), PROGRAM STUDI etc. 12-14pt
* TOC: field TOC \o "1-3" tanpa kalimat instruksi, judul tanpa prefix BAB dan tanpa em dash
* Daftar Pustaka: judul lebih informatif "DAFTAR PUSTAKA DAN SUMBER RUJUKAN TERKAIT" dengan kategori terstruktur bila diminta
* Kesimpulan: dari pembahasan awal hingga akhir, kenapa tema dipilih, fokus pemahaman prinsip bukan membandingkan tools
* target length: per assignment
* citation style: per assignment
* required tables and figures: per assignment
* template rules: single logo, no em dash, numbered team if needed, 1.5 line spacing, justify black 12pt
* section owners: per assignment
* output formats: DOCX + PDF via LibreOffice UNO, PPTX via python-pptx for slide decks

## Cover branding rule (mandatory) — GENERAL

Cover 1 halaman penuh:

```text
LAPORAN TEMA PROYEK / DESAIN INTERAKSI (24/16pt, centered, top 48pt)
EcoTrack Platform ... (16pt bold)
[LOGO UNAIR 5.5cm centered, space 72/36pt, di tengah halaman]
Kelompok 4 (12pt bold, tanpa daftar anggota)
Dosen: Barry Nuqoba, S.Si., M.Kom., Ph.D. (12-14pt)
PROGRAM STUDI SISTEM INFORMASI
FAKULTAS SAINS DAN TEKNOLOGI
UNIVERSITAS AIRLANGGA
SURABAYA
2026 (14pt bold)
```

* Logo asset: `/home/misbahul45/code/xninetzy/assets/branding/logo-unair.png` (512x512 RGBA PNG; do not regenerate).
* Placement: SINGLE centered 5.5cm, di tengah halaman (bukan double).
* Spacing: title top 48pt, logo 72/36pt, Nama|NIM 12/12pt, Dosen 24pt, metadata 4/6pt — muat 1 halaman.
* Wajib Dosen: ambil dari memory #163 sesuai matkul (SII209 I4 = Barry Nuqoba, SII208 I1 = Endah Purwanti, dll).
* Tanpa em dash, tanpa icon.

## Slide contract — FUTURISTIC TECH / AI STARTUP PITCH DECK

Untuk HEBAT Tugas 2 SII208 (resume Ch 4,5,6 + 20 contoh interaksi):

* Canvas: 16:9 widescreen, background pure black #000000
* Primary text: white #FFFFFF, Secondary: light gray #CCCCCC
* Accent: electric blue #245BFF, violet #7B3FF2, magenta highlight
* Headline: extra-bold geometric sans-serif, white, uppercase, tight spacing
* Body: light/regular sans-serif, white/gray, generous letter spacing
* Cards: dark rounded rectangle, thin white/blue border, minimal shadow
* Illustration: neon light trails (blue→purple→magenta), glowing curves, abstract tech
* Layout: asymmetric, generous negative space (70% black + 20% white + 10% neon), rounded corners

Every slide:

```yaml
purpose:
headline:
key_message:
evidence:
visual:
citation:
speaker_note:
transition:
```

## Integration

Resolve: repetition, terminology mismatch, conflicting numbers, citation numbering, uneven depth, missing requirements, cross-references.

## Completion

Verify: file exists, non-zero size, correct type, expected content, no placeholder, no truncation, citation present, exact path, cover 1 halaman tengah, Times New Roman 12pt 1.5 justify hitam.

Do not claim visual quality without inspecting a preview.
