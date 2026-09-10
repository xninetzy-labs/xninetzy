# 00 — Project Plan

## Tujuan
Karya ilmiah lengkap: "Implementasi Sistem Pembelajaran Adaptif Berbasis Automated Memory dan Research Agent untuk Meningkatkan Personalisasi, Retensi Pengetahuan, dan Efektivitas Proses Belajar" — BAB I-IV + cover + abstrak + daftar pustaka, dengan rancangan sistem nyata, diagram, dan evaluasi yang diusulkan.

## Tool & Environment Audit (FASE 0)

### MCP tersedia
- xninetzy (memory, learning OS, Graph RAG, workflow) — connected
- paper_research (arXiv, Semantic Scholar, OpenAlex, CrossRef, dblp, DOAJ, dll) — connected
- web_search — connected
- youtube_search (yt-dlp) — connected
- context7 — connected
- markitdown — connected
- document_generator (DOCX/PDF) — connected
- powerpoint — connected

### Command audit
| tool | status | catatan |
|---|---|---|
| python3 | 3.12.3 OK | venv: /tmp/opencode/pdfenv |
| uv | 0.11.16 OK | dipakai utk dep sementara |
| node/npx | v24 OK | mermaid-cli via npx |
| google-chrome | OK | dipakai puppeteer (mermaid) |
| mmdc (mermaid CLI) | tidak terpasang | pakai npx -y @mermaid-js/mermaid-cli + puppeteer config |
| plantuml | tidak ada | fallback: source .puml disimpan, render sequence via mermaid; dicatat di validation |
| pandoc | TIDAK ADA | fallback: python-docx + reportlab |
| libreoffice/soffice | OK | fallback konversi |
| reportlab | 5.0.0 OK | PDF utama |
| python-docx | BELUM | akan diinstall di venv /tmp/opencode/pdfenv (bukan dep repo utama) |
| PIL | OK | |
| ghostscript gs | OK | QA PDF |
| ImageMagick convert | tidak ada | tidak dibutuhkan |

## Deliverables
00-10 md, 03-source-matrix.csv, references.bib, 4+ diagram (mmd/puml + PNG), final DOCX, final PDF (target ≥50 hal), validation-report.md, optional PPTX.

## Asumsi
- Data cover: placeholder (nama/NIM/matakuliah) karena belum disediakan.
- Tidak ada eksperimen nyata → gunakan "rancangan yang diusulkan", "expected outcome", "evaluation framework".
- Bahasa Indonesia akademik, sitasi APA 7.

## Keputusan output (user, 2026-08-03)
Output final disalin juga ke folder `generated_documents/` (alur Xninetzy yang sudah disepakati: reportlab/venv, QA struktural + render preview PNG untuk verifikasi visual user). Salinan kerja tetap di docs/research/.../output/.
