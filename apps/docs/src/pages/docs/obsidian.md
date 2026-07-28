---
layout: ../../layouts/DocsLayout.astro
title: Obsidian dan knowledge
description: Hubungkan vault, kelola note, ingest knowledge, dan pertahankan guard path yang aman.
section: Integrasi
---

Obsidian adalah lapisan knowledge yang dapat dibaca serta diedit manusia. Xninetzy tidak membutuhkan plugin Obsidian khusus; ia bekerja langsung pada file Markdown di vault yang di-mount.

## Konfigurasi

```dotenv
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/vault
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
```

Pastikan user container memiliki akses baca/tulis ke vault. Gunakan `HOST_UID` dan `HOST_GID`, bukan `chmod 777`.

## Kemampuan note

Tool registry mendukung operasi seperti:

- list, search, read, create, append, dan overwrite;
- frontmatter dan tag;
- heading serta section;
- backlink dan unresolved link;
- todo, MOC, serta daily note;
- backup sebelum overwrite.

Contoh dari WhatsApp atau MCP:

```text
buat note Learning/REST API.md dengan konsep dan latihan
cari semua note tentang machine learning
tambahkan hasil review ke Daily/2026-07-28.md
buat MOC untuk folder Data Analytics
```

Semua path tool harus **relatif terhadap vault**:

```text
Learning/Pembelajaran Mesin/KNN.md
```

Jangan kirim `/home/user/vault/...` atau `/app/obsidian-vault/...` sebagai input tool.

## Guard filesystem

Integrasi menolak:

- absolute path;
- traversal `..`;
- path yang terlihat seperti credential;
- extension yang tidak diizinkan;
- delete ketika `OBSIDIAN_ALLOW_DELETE=false`.

Backup overwrite mencegah kehilangan tidak sengaja, tetapi bukan pengganti backup vault terjadwal.

## Knowledge base

Knowledge ingest mengubah teks atau file menjadi chunks dan menyimpannya pada FAISS. Semantic search dapat dipakai agent untuk mengambil context yang relevan.

```text
jadikan file yang aku kirim sebagai knowledge
cari knowledge yang menjelaskan gradient descent
jawab pertanyaan ini hanya berdasarkan materi Pembelajaran Mesin
```

Jika source adalah note, Graph RAG dapat menghubungkan topik, source, roadmap, task, dan note.

## Roadmap ke vault

Workflow yang disarankan:

1. download atau ingest materi sumber;
2. buat outline konsep besar;
3. generate draft roadmap dan review urutannya;
4. buat note konsep per milestone;
5. hubungkan note melalui MOC;
6. approve aktivasi roadmap;
7. lakukan weekly review.

Membuat roadmap tidak otomatis mengubah vault kecuali request juga meminta pembuatan note. Aktivasi roadmap membutuhkan approval admin.

## MCP

Coding client yang terhubung global dapat memakai vault dari folder mana pun:

```text
Gunakan MCP xninetzy untuk mencari note tentang data analytics dan tampilkan backlink-nya.
```

Client tetap tunduk pada guard yang sama seperti WhatsApp.
