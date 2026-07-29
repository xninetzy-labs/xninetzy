---
layout: ../../layouts/DocsLayout.astro
title: Local data per installation
description: Model SQLite per owner, runtime-data isolation, migration, backup, dan sanitasi repository open-source.
section: Operasional
---

Setiap instalasi Xninetzy memiliki SQLite sendiri. Repository tidak membawa
database contoh, database pemilik, WAL/SHM, FAISS, session Moodle, hasil download,
atau snapshot analisis.

```text
clone A → services/ai/data/xninetzy.sqlite3 milik owner A
clone B → services/ai/data/xninetzy.sqlite3 milik owner B
```

Database dibuat dan dimigrasikan otomatis saat AI service startup. State tidak
dibagi melalui Git, Codex config, Claude config, atau OpenCode config. MCP client
pada satu mesin menunjuk instalasi lokal yang dikonfigurasi untuk mesin tersebut.

## Aturan repository

Seluruh `services/ai/data/**` diabaikan Git kecuali file kebijakan
`services/ai/data/README.md`. Ini meliputi:

- SQLite, `-wal`, dan `-shm`;
- FAISS index/map yang merepresentasikan knowledge pribadi;
- HEBAT browser profile, cookie/state, download, dan debug HTML;
- web-analysis snapshot/report;
- media WhatsApp dan backup lokal.

Sebelum commit:

```bash
git status --short
git ls-files services/ai/data
```

Output `git ls-files` seharusnya hanya menampilkan
`services/ai/data/README.md`.

## Memindahkan instalasi

Gunakan [Backup dan restore](/docs/backup-restore/), bukan commit database. Backup
memiliki checksum dan restore confirmation. Transfer snapshot lewat media
terenkripsi, batasi akses ke owner, lalu hapus salinan sementara.

## Jika data pernah ter-push

Menghapus file pada commit terbaru tidak menghapus blob dari history. Sebelum
repository dibuat publik:

1. revoke atau rotate session/credential yang mungkin terekspos;
2. buat clone cadangan privat;
3. sanitasi history dengan tool seperti `git filter-repo`;
4. force-push hanya setelah koordinasi dengan seluruh collaborator;
5. jalankan secret scan dan periksa kembali `git ls-files`;
6. minta collaborator membuat clone baru setelah history berubah.

History rewrite bersifat destruktif dan tidak dijalankan otomatis oleh Xninetzy.
