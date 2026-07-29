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

## Study session

Roadmap aktif dapat menjalankan satu sesi belajar pada satu waktu untuk owner
lokal. Session menyimpan fokus, target dan durasi aktual, energi sebelum/sesudah,
mastery `0–1`, refleksi, serta daftar evidence. `idempotency_key` mencegah retry
WhatsApp atau MCP membuat sesi ganda.

Tool yang tersedia pada registry bersama:

| Tool | Fungsi |
|---|---|
| `learning_start_study_session` | Mulai atau lanjutkan sesi aktif |
| `learning_complete_study_session` | Simpan hasil dan tutup sesi secara idempotent |
| `learning_list_study_sessions` | Lihat riwayat sesi |
| `learning_get_study_progress` | Ringkas task, sesi, menit, dan mastery |
| `learning_generate_today_plan` | Buat fokus adaptif untuk hari ini |

Completion menulis progress dan event `learning_session_completed` dalam
transaksi SQLite yang sama. Retry completion tidak menggandakan progress atau
event.

## Adaptive today plan

Mode rencana berubah mengikuti state aktual:

- `start`: belum ada sesi; mulai dari pending task terkecil;
- `resume`: satu sesi masih aktif;
- `reinforce`: mastery terakhir di bawah 60%;
- `practice`: mastery 60–79%;
- `advance`: mastery minimal 80%.

Energi terakhir menyesuaikan timebox menjadi 15, 25, atau 35 menit. Fokus
adaptif juga masuk ke Personal Context internal LangGraph, sehingga WhatsApp dan
MCP membaca state pembelajaran yang sama.

Contoh natural request di WhatsApp:

```text
Mulai sesi belajar roadmap Graph RAG selama 25 menit, energi saya 3/5.
```

Setelah belajar:

```text
Selesaikan sesi 12: aktual 28 menit, mastery 0.7, energi 2/5. Saya masih bingung RRF.
```

Contoh melalui Codex, Claude Code, atau OpenCode:

```text
Gunakan MCP xninetzy untuk tampilkan study plan hari ini dan mulai sesi dengan idempotency key mcp-2026-07-29-graph-rag.
```
