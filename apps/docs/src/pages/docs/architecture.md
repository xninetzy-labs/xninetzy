---
layout: ../../layouts/DocsLayout.astro
title: Arsitektur sistem
description: Service boundary, alur request, tool registry, persistence, dan alasan MCP dibagi menjadi dua transport.
section: Mulai
---

Xninetzy adalah monorepo dengan dua service runtime utama, satu terminal client, dan satu documentation app.

## Service boundary

```text
WhatsApp user
  ↓
WA engine / Baileys :8081
  ↓ POST /api/chat
AI service / FastAPI :8000
  ↓
LangGraph → direct | clarify | agent | workflow
  ↓
Tool registry → Obsidian | HEBAT | SQLite | FAISS | WA
```

### AI service

Lokasi `services/ai`. Service ini memiliki routing, prompt, provider registry, MCP stdio server, domain tools, database, knowledge, research, media extraction, HEBAT, Obsidian, serta approval.

### WA engine

Lokasi `services/wa-enggine`. Hanya proses ini yang memiliki socket Baileys, sehingga send message, media, contact, group, pin, dan label tetap berada di sini.

### CLI

Lokasi `apps/cli`. Terminal client memanggil endpoint `/api/chat` yang sama sehingga provider, memory, routing, dan tool tidak terduplikasi.

## Tiga jalur request

1. **Slash command** masuk ke command router deterministik.
2. **Multi-action request** menjadi workflow dengan status yang dapat diperiksa.
3. **Pesan natural** dirutekan LangGraph ke jawaban langsung, klarifikasi, atau ReAct agent.

## Tool registry sebagai source of truth

`services/ai/app/xninetzy/tools/registry.py` mengumpulkan seluruh tool. MCP adapter membaca katalog ini secara dinamis, jadi tool baru tidak membutuhkan wrapper MCP manual.

Adapter bertanggung jawab untuk:

- menormalisasi nama serta description;
- membuat JSON Schema dari signature/Pydantic;
- menyuntikkan context yang diizinkan;
- mengubah return value menjadi MCP content;
- menjaga exception agar tidak merusak protocol stream.

## Mengapa ada dua server tool

| Server | Transport | Pemilik | Isi |
|---|---|---|---|
| Xninetzy MCP | stdio | AI service | seluruh registry tool personal OS |
| WA tool server | HTTP MCP-style | WA engine | aksi yang membutuhkan socket WhatsApp |

Codex, Claude, dan OpenCode menjalankan MCP stdio. Ketika sebuah tool perlu mengirim pesan WhatsApp, AI service memanggil WA engine melalui `/mcp/call` dengan bearer token internal.

## Persistence

| Data | Host | Container |
|---|---|---|
| SQLite, FAISS, HEBAT | `services/ai/data` | `/app/data` |
| Obsidian | path pilihan user | `/app/obsidian-vault` |
| Media WhatsApp | named volume `wa-media` | `/app/data/wa-media` |
| Session WhatsApp | named volume `wa-session` | `/app/sessions` |

SQLite menyimpan state terstruktur. FAISS menyimpan embedding index. Markdown vault tetap menjadi source yang dapat dibaca manusia.

## Security boundary

- Admin ditentukan dengan JID eksplisit.
- Tool berisiko memakai approval atau confirmation.
- Obsidian membatasi path ke vault dan extension aman.
- Coding agent dibatasi allowed root, timeout, env allowlist, serta audit log.
- HEBAT submission tidak otomatis pada konfigurasi aman.
- WA HTTP tools memakai shared API key ketika diisi.

## Menambah fitur

Alur contributor yang direkomendasikan:

1. tentukan domain dan boundary data;
2. implementasikan service/tool tanpa coupling ke transport;
3. daftarkan tool pada registry;
4. tambah unit test pada domain terkait;
5. tambah test MCP schema/invocation bila signature baru;
6. perbarui dokumentasi dan contoh command.
