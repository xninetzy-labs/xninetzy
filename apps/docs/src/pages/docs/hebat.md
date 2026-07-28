---
layout: ../../layouts/DocsLayout.astro
title: HEBAT dan Moodle
description: Login aman, sinkronisasi course, download materi asli, pembacaan PDF, dan submission dengan konfirmasi.
section: Integrasi
---

Integrasi HEBAT memakai Playwright untuk authenticated browser session dan Moodle client untuk course, activity, resource, serta assignment.

## Konfigurasi

```dotenv
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
HEBAT_BROWSER_HEADLESS=true
HEBAT_AUTO_LOGIN=false
HEBAT_REQUIRE_CONFIRMATION=true
HEBAT_ALLOW_AUTO_SUBMIT=false
```

Simpan credential hanya di `.env` lokal dengan permission `600`. Jangan commit browser profile, cookie, storage state, atau hasil download course.

## Setup browser

```bash
cd services/ai
uv sync
uv run playwright install chromium
```

Image Docker AI sudah menyiapkan dependency browser yang dibutuhkan.

## Alur penggunaan

```text
login hebat
sync course hebat
cek course hebat
masuk ke course Pembelajaran Mesin dan tampilkan activity
download semua PDF dari Pembelajaran Mesin
baca seluruh PDF lalu buat roadmap lengkap di Obsidian
```

Gunakan nama course yang cukup spesifik. Tool dapat mencari course dari cache lokal setelah sync.

## Download materi

File ditempatkan pada:

```text
services/ai/data/hebat/downloads/<course-id>/<activity>/<filename>
```

Downloader meng-resolve halaman resource Moodle sampai URL file asli `pluginfile.php`. Content-Type, magic bytes, serta extension diperiksa agar halaman login atau HTML redirect tidak disimpan sebagai PDF.

## Membaca materi

PDF reader mengambil text native. Jika PDF merupakan scan, media pipeline dapat memakai OCR. Setelah text tersedia, agent dapat:

- membuat ringkasan per materi;
- mengurutkan prerequisite;
- menghasilkan roadmap;
- membuat note konsep di vault;
- ingest chunks ke knowledge base.

## Assignment dan submission

Upload submission adalah aksi berisiko. Guard meliputi:

- admin identity;
- allowlist extension;
- batas ukuran file;
- file harus berada pada allowed path;
- confirmation token;
- `HEBAT_ALLOW_AUTO_SUBMIT=false` sebagai default.

Jangan menonaktifkan confirmation hanya demi convenience. Preview file serta course/assignment target sebelum menyetujui.

## Debug aman

Dari WhatsApp:

```text
/hebat-debug
```

Atau periksa service:

```bash
docker compose logs --tail=200 ai
```

Debug output tidak seharusnya mencetak password/cookie. Periksa:

1. base/login URL dapat dijangkau;
2. credential ada tanpa whitespace tidak sengaja;
3. Chromium terpasang;
4. browser profile writable;
5. session belum kedaluwarsa;
6. portal tidak sedang maintenance atau mengubah selector.

## Penggunaan yang bertanggung jawab

Integrasi ini bersifat personal. Hormati kebijakan institusi dan rate limit. Jangan membagikan session, cookie, materi berlisensi, atau mengotomatisasi submission tanpa review pemilik.
