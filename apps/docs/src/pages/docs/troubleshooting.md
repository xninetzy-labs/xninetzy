---
layout: ../../layouts/DocsLayout.astro
title: Troubleshooting
description: Diagnosis cepat untuk provider, WhatsApp, media, Obsidian, HEBAT, MCP, permission, dan docs build.
section: Operasional
---

Mulai dari health check dan boundary terdekat. Jangan langsung menghapus session, database, atau volume.

## Model tidak dapat dihubungi

```text
/llm list
```

Periksa enabled provider, allowlist model, base URL, credential, dan restart service setelah `.env` berubah. Jalankan script Flaz lagi jika perlu:

```bash
cd services/ai
uv run python scripts/configure_flaz.py
```

## QR atau pairing code tidak muncul

```bash
docker compose logs -f wa-enggine
```

Pastikan `WA_LOGIN_MODE` valid. Pairing membutuhkan `WA_PHONE_NUMBER`. Jangan hapus volume session sebelum memastikan session memang rusak.

## Bot tidak merespons group

```dotenv
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

Mention bot, reply pesan bot, atau gunakan prefix `!`.

## Dokumen/gambar tidak terbaca

1. reply attachment lalu jalankan `/media-info`;
2. periksa file ada di shared `WA_MEDIA_DIR`;
3. pastikan AI dan WA melihat storage yang sama;
4. periksa MIME, extension, checksum, serta limit ukuran;
5. pastikan Tesseract dan language pack tersedia untuk OCR;
6. untuk scanned PDF, pastikan fallback OCR aktif.

## AI tidak dapat memakai tool WhatsApp

```bash
curl -s http://127.0.0.1:8081/health
```

Pastikan `socket_ready=true`, `WA_MCP_BASE_URL` benar, dan `WA_MCP_API_KEY` sama dengan `MCP_API_KEY`.

## Obsidian gagal menulis

- `OBSIDIAN_VAULT_HOST_PATH` harus absolute dan ada.
- UID/GID container harus memiliki akses.
- `OBSIDIAN_ALLOW_WRITE=true`.
- Input tool menggunakan path relatif.
- Extension harus masuk allowlist.
- Vault tidak sedang read-only/mounted salah.

## HEBAT login/download gagal

```text
/hebat-debug
```

Periksa credential, Chromium, write permission browser profile, expiry session, maintenance portal, perubahan selector, dan apakah hasil download memiliki magic bytes file yang benar.

## MCP tidak muncul dari folder lain

Uji dari `/tmp`:

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

Jika command masih memakai `services/ai` relatif, migrasikan ke global config dengan absolute path. Jika repository dipindah, update path ketiga client.

### Claude pending approval

Entry `.mcp.json` project memerlukan approval. Untuk penggunaan global, pastikan output `claude mcp get xninetzy` menunjukkan `Scope: User config`.

### OpenCode tidak connected

```bash
opencode debug paths
opencode debug config
```

Periksa `~/.config/opencode/opencode.jsonc`, JSON syntax, path `uv`, timeout, dan dependency Python.

### MCP protocol error

Stdout hanya untuk protocol frame. Arahkan logging aplikasi ke stderr. Jalankan targeted test:

```bash
cd services/ai
uv run pytest -q tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

## Permission denied SQLite/download

Periksa `HOST_UID`, `HOST_GID`, ownership `services/ai/data`, dan owner vault. Jangan bergantian menjalankan service sebagai root dan user biasa.

## Port sudah digunakan

```bash
ss -ltnp | grep -E ':8000|:8081'
docker compose ps
```

Stop instance yang tidak dipakai. Jangan menjalankan local dan Docker pada port yang sama.

## Docs build gagal

```bash
cd apps/docs
node --version
yarn install --frozen-lockfile
yarn check
yarn build
```

Astro 7 membutuhkan Node 22.12 atau lebih baru. Hapus cache hanya setelah membaca error; jangan menghapus source atau lockfile.

## Informasi untuk laporan bug

Sertakan:

- command yang dijalankan;
- expected vs actual result;
- status health;
- versi Python/Node/client;
- log yang sudah disanitasi;
- scope: host/Docker, private/group, text/media;
- test minimal yang gagal.

Jangan sertakan API key, password, cookie, JID pribadi, atau isi dokumen sensitif.
