# Document Studio Markdown dialect

Contents: front matter; document blocks; deck rules; layouts; examples.

## Front matter

```yaml
---
title: Analisis Sistem Informasi Akademik
subtitle: Laporan Tugas Rekayasa Perangkat Lunak
author: [Nama Satu, Nama Dua]
student_id: [187221001, 187221002]
course: Rekayasa Perangkat Lunak
lecturer: Dr. Nama Dosen, M.Kom.
program: Program Studi Teknik Informatika
faculty: Fakultas Sains dan Teknologi
institution: Universitas Airlangga
date: Surabaya, 2026
logo: assets/logo.png
theme: academic-hebat
toc: true
cover: true
---
```

All keys are optional. `title` enables the cover and the title slide. `logo` and image paths are relative to the Markdown file.

## Document blocks

| Markdown | Result |
|---|---|
| `#`, `##`, `###` | Heading 1–3 (also table-of-contents entries) |
| blank-line separated text | paragraph (justified in `academic-hebat`) |
| `**bold**`, `*italic*`, `` `code` ``, `[text](https://…)` | inline styles and real hyperlinks |
| `- item`, indented `  - sub` | bullets, up to four levels |
| `1. item` | numbered list |
| `Tabel: caption` or `Table: caption` above a table | numbered caption ("Tabel 1.") |
| GFM pipe table with `:---:` / `---:` | styled table, header repeats on new pages |
| `![caption](path.png)` on its own line | centered figure with numbered caption |
| fenced code block | monospace shaded block |
| `> quote` | indented italic quote |
| `\pagebreak` | page break |

## Deck rules

- Slides split on `---` lines when present; otherwise every H1/H2 starts a slide.
- The first heading of a slide is its title.
- `|||` on its own line splits the slide into two columns.
- `Notes: …` (or `Catatan: …`) becomes speaker notes.
- `<!-- layout: section -->` forces a layout: `section`, `content`, `table`, `image`, `columns`, `code`.
- Inferred layouts: an H1 with at most one short paragraph becomes a section slide; a table becomes a table slide; an image with text becomes text-left, image-right.

## Example deck section

```markdown
## Temuan Utama

- Waktu respons turun 40% setelah caching
- Error rate stabil di bawah 0,5%

|||

![Grafik latensi](charts/latency.png)

Notes: Sebutkan bahwa angka diambil dari log produksi Oktober.
```
