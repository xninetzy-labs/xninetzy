---
layout: ../../layouts/DocsLayout.astro
title: Quick start
description: Dari clone repository sampai chat WhatsApp pertama dengan jalur Docker yang reproducible.
section: Mulai
---

Jalur Docker adalah cara termudah untuk menjalankan AI service dan WA engine secara konsisten. Compose saat ini bersifat **Linux-first** karena memakai host networking.

## Prasyarat

- Linux host dengan Docker Engine dan Docker Compose plugin.
- Flaz API key atau credential provider LLM lain.
- Absolute path menuju Obsidian vault.
- Akun WhatsApp yang dapat ditautkan sebagai linked device.

Untuk development lokal, gunakan Python 3.11+, `uv`, Node.js 22.12+, Yarn 1.22, Chromium Playwright, dan Tesseract untuk OCR.

## 1. Siapkan environment

Dari root repository:

```bash
cp .env.example .env
chmod 600 .env
```

Jangan menaruh password, token, cookie, atau API key asli di `.env.example`.

## 2. Masukkan Flaz API key dengan aman

```bash
cd services/ai
uv run python scripts/configure_flaz.py
cd ../..
```

Script memakai prompt `getpass`, tidak mencetak key, menulis `.env` secara atomik, dan menjaga permission `600`.

Konfigurasi default:

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
```

## 3. Hubungkan data host

Cari identitas user host:

```bash
id -u
id -g
```

Isi `.env`:

```dotenv
HOST_UID=1000
HOST_GID=1000
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/obsidian-vault
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
ADMIN_NAMES=your_name
APP_TIMEZONE=Asia/Jakarta
```

`OBSIDIAN_VAULT_HOST_PATH` harus absolute. Compose menolak start ketika nilainya kosong.

## 4. Pilih login WhatsApp

QR mode:

```dotenv
WA_LOGIN_MODE=qr
```

Atau pairing code:

```dotenv
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Nomor memakai kode negara tanpa `+`, spasi, atau tanda baca.

## 5. Jalankan service

```bash
docker compose config -q
docker compose up --build -d ai wa-enggine
docker compose ps
docker compose logs -f wa-enggine
```

Selesaikan QR atau pairing melalui **WhatsApp → Linked devices**.

## 6. Verifikasi health

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8081/health
```

AI service seharusnya mengembalikan:

```json
{"status":"ok","service":"xninetzy-ai"}
```

Health WA menampilkan status socket serta koneksi WhatsApp.

## 7. Coba dari WhatsApp

```text
/helper
buat roadmap belajar machine learning 14 hari
ingatkan aku besok jam 08.00 untuk review tugas
simpan ringkasan percakapan ini ke Obsidian
```

## Development lokal

AI service:

```bash
cd services/ai
uv sync
uv run playwright install chromium
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

WA engine di terminal kedua:

```bash
cd services/wa-enggine
yarn install --frozen-lockfile
yarn dev
```

Jangan jalankan instance Docker dan lokal bersamaan pada port atau akun WhatsApp yang sama.
