---
layout: ../../layouts/DocsLayout.astro
title: Backup dan restore
description: Membuat, memverifikasi, meretensi, dan memulihkan state Xninetzy dengan aman.
section: Operasional
---

Backup Xninetzy mencakup snapshot konsisten SQLite serta `faiss.index` dan
`faiss_map.json` jika tersedia. Setiap snapshot memiliki manifest SHA-256.
Credential, `.env`, cookie, session WhatsApp, browser profile, course download,
dan Obsidian vault tidak disalin. Backup vault dan secret harus dikelola
terpisah.

## Konfigurasi

```dotenv
BACKUP_DIR=/app/data/backups
BACKUP_RETENTION=14
```

Direktori backup berisi data pribadi dan diabaikan Git. Simpan salinan kedua di
media terenkripsi yang hanya dapat dibaca pemilik.

## Membuat dan memeriksa snapshot

Untuk stack Docker, jalankan di container agar `/app/data` menunjuk volume yang
benar:

```bash
docker compose exec ai uv run python scripts/xninetzy_backup.py create
docker compose exec ai uv run python scripts/xninetzy_backup.py list
docker compose exec ai uv run python scripts/xninetzy_backup.py verify <backup-name>
```

Untuk host mode, jalankan dari `services/ai` setelah `SQLITE_PATH`,
`VECTOR_DATA_DIR`, dan `BACKUP_DIR` diarahkan ke path host.

`create` menggunakan SQLite online backup API agar database tidak disalin secara
mentah ketika WAL aktif. Snapshot lama dipangkas setelah jumlahnya melewati
`BACKUP_RETENTION`.

## Restore

Restore adalah operasi eksplisit dan tidak berjalan tanpa `--confirm`:

```bash
docker compose exec ai uv run python scripts/xninetzy_backup.py verify <backup-name>
docker compose stop ai wa-enggine
docker compose run --rm --no-deps ai uv run python scripts/xninetzy_backup.py restore <backup-name> --confirm
docker compose up -d ai wa-enggine
```

One-off container memakai volume yang sama tetapi tidak menjalankan FastAPI atau
background loop. Command
memvalidasi seluruh checksum terlebih dahulu dan mengganti file target secara
atomik, tetapi tidak dapat menjamin konsistensi jika service lain tetap menulis.

## Recovery drill

Minimal setiap bulan:

1. buat snapshot baru;
2. verifikasi checksum;
3. restore ke direktori staging, bukan data aktif;
4. buka SQLite dan validasi jumlah task/note/event;
5. validasi invariant FAISS melalui test atau startup service;
6. catat tanggal, backup ID, hasil, dan operator di log operasional.

Backup belum lengkap sebelum restore pernah diuji. Jangan menaruh secret di log
drill atau menyalin snapshot personal ke repository.
