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
| `learning_define_concept` | Tambahkan konsep serta relasi prerequisite/milestone/task |
| `learning_record_concept_evidence` | Catat evidence idempotent dan update mastery |
| `learning_get_concept_map` | Lihat graph konsep dan readiness roadmap |

Completion menulis progress dan event `learning_session_completed` dalam
transaksi SQLite yang sama. Retry completion tidak menggandakan progress atau
event.

## Concept graph dan evidence

Setiap milestone roadmap sekarang menjadi konsep typed. Konsep berurutan
terhubung sebagai prerequisite, lalu task hari pertama dipetakan ke konsep yang
relevan. Roadmap lama di-backfill secara idempotent saat migration startup.

```text
roadmap
  -> milestone
  -> concept
       -> prerequisite concept
       -> learning task
       -> study session
       -> evidence
       -> mastery 0..1
```

Evidence memiliki idempotency key dan payload hash. Retry dengan payload sama
tidak mengubah mastery dua kali; key sama dengan payload berbeda ditolak.
Evidence pertama menetapkan baseline mastery. Evidence berikutnya memakai
weighted update `40% mastery lama + 60% score baru`. Nilai minimal 80% berstatus
`mastered`, sedangkan prerequisite baru dianggap siap pada minimal 70%.

Penyelesaian study session otomatis menghasilkan evidence untuk konsep yang
terikat pada sesi tersebut dalam transaksi yang sama. Concept graph kemudian
mengarahkan today plan, review mingguan, attention queue, dan Personal Context
ke konsep lemah berikutnya.

WhatsApp dapat membaca map dengan:

```text
/concepts <roadmap-id>
```

Codex, Claude Code, OpenCode, dan LangGraph memakai tiga tool registry yang sama.
Reference evidence adalah data lokal dan bukan sumber grounded otomatis; klaim
knowledge tetap harus melewati `knowledge_answer` dan citation validation.

## Active recall dan spaced repetition

Recall card terikat ke satu konsep dan menyimpan pertanyaan, expected answer,
keyword jawaban eksplisit, serta referensi sumber opsional. Pertanyaan yang jatuh
tempo dapat dibaca tanpa mengekspos expected answer:

```text
/recall
/recall <roadmap-id>
```

Jawab dari WhatsApp dengan confidence `1–5`:

```text
/recall answer <card-id> <confidence> <jawaban>
```

Grading bersifat deterministik berdasarkan coverage keyword, bukan keputusan
LLM. Expected answer baru ditampilkan setelah jawaban disimpan agar recall tidak
bocor sebelum attempt. Confidence dicatat sebagai metacognitive signal tetapi
tidak digunakan untuk menaikkan skor correctness.

Scheduling mengikuti aturan SM-2 yang dibatasi:

- quality di bawah `3` menghitung lapse, mengulang setelah satu hari, dan
  mereset repetition;
- review berhasil pertama dijadwalkan satu hari;
- review berhasil kedua dijadwalkan enam hari;
- review berikutnya menggunakan interval sebelumnya dan ease factor minimal
  `1.3`.

Attempt, perubahan jadwal, concept evidence, mastery, dan event completion
ditulis dalam satu transaksi. Retry pada hari dan payload yang sama tidak
menggandakan attempt. MCP caller dapat memberikan `idempotency_key` eksplisit;
WhatsApp command menggunakan key turunan dari kartu, tanggal lokal, confidence,
dan jawaban.

Recall due muncul sebelum sesi baru pada adaptive today plan, mendapat prioritas
khusus di OS attention queue, masuk ke Personal Context, dan diringkas dalam
weekly review. Sesi belajar yang masih aktif tetap didahulukan agar state tidak
ditinggalkan setengah jalan.

Tool registry bersama:

| Tool | Fungsi |
|---|---|
| `learning_create_recall_card` | Buat kartu immutable untuk satu konsep |
| `learning_due_recall` | Lihat pertanyaan yang jatuh tempo |
| `learning_submit_recall_answer` | Grade, evidence, mastery, dan schedule atomik |

## Adaptive today plan

Mode rencana berubah mengikuti state aktual:

- `start`: belum ada sesi; mulai dari pending task terkecil;
- `resume`: satu sesi masih aktif;
- `reinforce`: mastery terakhir di bawah 60%;
- `practice`: mastery 60–79%;
- `advance`: mastery minimal 80%.

Jika concept graph tersedia, planner hanya memilih konsep yang seluruh
prerequisite-nya telah mencapai ambang readiness. Fokus konsep terlemah juga
masuk ke Personal Context dan review aktual.

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
