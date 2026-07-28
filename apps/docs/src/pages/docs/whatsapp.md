---
layout: ../../layouts/DocsLayout.astro
title: Integrasi WhatsApp
description: Login, trigger chat, slash command, dokumen, gambar, OCR, dan tool WhatsApp internal.
section: Integrasi
---

WA engine memakai Baileys untuk linked-device session. Pesan yang memenuhi trigger diubah menjadi payload terstruktur, lalu dikirim ke AI service.

## Login

QR:

```dotenv
WA_LOGIN_MODE=qr
```

Pairing code:

```dotenv
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Pantau proses:

```bash
docker compose logs -f wa-enggine
```

Session disimpan pada named volume `wa-session` dalam Docker atau `WA_AUTH_DIR` saat lokal.

## Trigger private dan group

Private chat diproses langsung. Group diproses jika salah satu kondisi terpenuhi:

- bot di-mention;
- pesan memakai prefix, default `!`;
- user reply pesan bot;
- `WA_GROUP_ALLOW_ALL=true`.

Konfigurasi aman:

```dotenv
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

## Command penting

| Command | Fungsi |
|---|---|
| `/helper [topic]` | panduan kemampuan |
| `/today`, `/tasks`, `/goals` | life OS |
| `/research`, `/deep-research` | research |
| `/roadmaps`, `/study-today` | learning OS |
| `/media-info`, `/analyze-media` | attachment/reply |
| `/approvals`, `/approve`, `/reject` | human approval |
| `/llm list`, `/llm use` | provider/model |
| `/agent list`, `/agent use`, `/code` | coding runtime |

## Dokumen dan gambar

Kirim atau reply PDF, DOCX, TXT, CSV, JSON, spreadsheet, presentasi, atau gambar:

```text
ringkas dokumen ini
buat action item dari file yang aku reply
baca teks pada gambar ini lalu simpan ke Obsidian
jadikan PDF ini knowledge dan jawab berdasarkan isinya
```

Pipeline media:

1. WA engine mengunduh attachment ke shared durable storage.
2. Payload membawa metadata dan resolved path.
3. AI memvalidasi checksum, MIME, extension, dan ukuran.
4. Teks native diekstrak lebih dulu.
5. Gambar atau scanned PDF memakai OCR Tesseract sebagai fallback.
6. Hasil dapat diberikan ke agent, knowledge ingest, atau Obsidian tool.

Jika reply attachment tidak terbaca, jalankan `/media-info` dan periksa apakah file terlihat pada `WA_MEDIA_DIR` yang sama bagi kedua service.

## HTTP MCP-style tools

WA engine menyediakan tool untuk mengirim pesan, mengunduh media, membaca kontak, dan aksi group:

```bash
curl -H 'Authorization: Bearer <MCP_API_KEY>' \
  http://127.0.0.1:8081/mcp/tools
```

Contoh call:

```bash
curl -X POST http://127.0.0.1:8081/mcp/call \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <MCP_API_KEY>' \
  -d '{"tool":"send_text_message","input":{"jid":"628xxxxxxxxxx@s.whatsapp.net","text":"Halo"}}'
```

Isi `MCP_API_KEY` pada WA engine dan nilai yang sama sebagai `WA_MCP_API_KEY` pada AI service.

> Baileys bukan WhatsApp Business API resmi. Perubahan protokol atau kebijakan WhatsApp dapat memengaruhi koneksi.
