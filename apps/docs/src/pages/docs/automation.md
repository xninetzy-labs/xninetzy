---
layout: ../../layouts/DocsLayout.astro
title: Automation dan scheduled jobs
description: Morning briefing, evening check-in, weekly review, periodic HEBAT sync, lease, retry, dan status delivery.
section: Operasional
---

Automation Xninetzy menutup loop `Capture → Understand → Plan → Execute →
Review → Adapt`. Pesan terjadwal dibangun dari state aktual—task, deadline,
roadmap, habit, goal, workout, event, serta freshness—bukan template LLM tanpa
bukti.

## Konfigurasi

```dotenv
OS_SCHEDULER_ENABLED=true
OS_SCHEDULER_STARTUP_DELAY_SECONDS=30
OS_SCHEDULER_POLL_SECONDS=60
OS_JOB_LEASE_SECONDS=900
OS_JOB_RETRY_DELAY_SECONDS=300
OS_NOTIFY_CHAT_ID=628xxxxxxxxxx@s.whatsapp.net

MORNING_BRIEFING_ENABLED=true
MORNING_BRIEFING_HOUR=7
EVENING_CHECKIN_ENABLED=true
EVENING_CHECKIN_HOUR=20
WEEKLY_REVIEW_ENABLED=true
WEEKLY_REVIEW_WEEKDAY=6
WEEKLY_REVIEW_HOUR=20

HEBAT_PERIODIC_SYNC_ENABLED=false
HEBAT_SYNC_INTERVAL_MINUTES=60
```

Jam mengikuti `APP_TIMEZONE`; weekday memakai format Python, yaitu Senin `0`
hingga Minggu `6`. Target delivery dipilih dari `OS_NOTIFY_CHAT_ID`, lalu
`HEBAT_NOTIFY_CHAT_ID`, lalu `ADMIN_JID`.

Periodic HEBAT sync default-nya mati karena membuka authenticated Moodle session.
Aktifkan hanya setelah login stabil, target owner benar, dan rate limit sudah
ditinjau.

## Jenis job

| Job | Idempotency key | Isi |
|---|---|---|
| Morning briefing | owner + tanggal | task, deadline, roadmap, freshness HEBAT |
| Evening check-in | owner + tanggal | task selesai, habit, prompt review |
| Weekly review | owner + ISO week | event nyata, goal, dan progress roadmap |
| HEBAT sync | interval bucket | assignment, shared task, dan reminder deadline |

## Lease dan delivery safety

Setiap run disimpan di SQLite sebelum bekerja. Job internal yang terputus dapat
diambil ulang setelah lease habis. HEBAT sync yang gagal memakai persisted
backoff dan attempt count.

Untuk pesan WhatsApp, Xninetzy menyimpan `delivery_started` beserta isi pesan
sebelum memanggil WA engine. Ini mencegah retry otomatis setelah restart. Jika
respons socket hilang, status menjadi `delivery_uncertain`: pesan mungkin sudah
diterima WhatsApp sehingga sistem tidak mengirim ulang secara buta. Operator
harus memeriksa chat lalu menentukan tindakan manual.

Saat AI restart, run lama yang masih berstatus `delivery_started` otomatis
direkonsiliasi menjadi `delivery_uncertain` sebelum scheduler mengambil job baru.

## Memeriksa status

Dari natural chat atau MCP client, panggil tool:

```text
os_job_status
```

Tool menampilkan target, freshness HEBAT, status, attempt, dan error terakhir.
Status utama:

- `running`: sedang dikerjakan dan memiliki lease;
- `delivery_started`: pengiriman sudah dimulai;
- `delivered`: WA engine menerima pengiriman;
- `succeeded`: job internal selesai;
- `failed`: gagal dan dapat memiliki jadwal retry;
- `delivery_uncertain`: hasil pengiriman ambigu dan perlu pemeriksaan manual.

## Freshness

HEBAT dianggap stale ketika timestamp sync terakhir melewati dua kali
`HEBAT_SYNC_INTERVAL_MINUTES`. Morning briefing selalu mengungkapkan status ini;
data stale tidak ditampilkan seolah-olah deadline pasti terbaru.
