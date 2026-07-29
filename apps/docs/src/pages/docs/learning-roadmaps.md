---
layout: ../../layouts/DocsLayout.astro
title: Adaptive learning roadmap
description: Roadmap 7, 14, dan 30 hari yang berbeda struktur, level-aware, serta terhubung ke sumber knowledge.
section: Integrasi
---

Planner roadmap tidak lagi memakai template 14 hari untuk semua permintaan.
Durasi, level, dan evidence menghasilkan strategi yang berbeda.

| Durasi | Fase | Strategi |
|---|---:|---|
| ≤ 7 hari | 4 | sprint |
| 8–14 hari | 5 | balanced |
| > 14 hari | 6 | deep-practice |

Setiap fase memiliki rentang hari, fokus, dan outcome. Seluruh hari selalu
tercakup dari hari pertama sampai durasi akhir. Level `advanced` mengubah fase
awal menjadi audit prerequisite/fondasi, bukan mengulang pengantar beginner.

## Source-aware planning

`learning_create_roadmap` menerima `source_ids` opsional. Tanpa ID eksplisit,
sistem mencari sumber knowledge internal yang relevan. Referensi dibatasi,
di-deduplicate, disimpan pada metadata roadmap, dan dibuat sebagai
`learning_resources` dengan URI internal:

```text
xninetzy://knowledge/source/<id>
```

Jika evidence internal tidak ada, draft menyatakan bahwa sumber masih perlu
dicari dan divalidasi. Planner tidak menyamarkan pengetahuan model umum sebagai
isi vault.

## Aktivasi dan progress

Draft tetap membutuhkan approval. Setelah aktivasi, item hari pertama menjadi
shared task. Penyelesaian task dari WhatsApp atau MCP memperbarui learning task,
progress, milestone, dan status roadmap melalui reducer idempotent.
