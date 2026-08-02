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
Tool registry → OS kernel | Obsidian | HEBAT | SQLite | FAISS | WA
```

### AI service

Lokasi `services/ai`. Service ini memiliki routing, prompt, provider registry, MCP stdio server, domain tools, database, knowledge, research, media extraction, HEBAT, Obsidian, serta approval.

### WA engine

Lokasi `services/wa-enggine`. Hanya proses ini yang memiliki socket Baileys, sehingga send message, media, contact, group, pin, dan label tetap berada di sini.

### CLI

Lokasi `apps/cli`. Terminal client memanggil endpoint `/api/chat` yang sama sehingga provider, memory, routing, dan tool tidak terduplikasi.

### Streaming dan activity CLI

CLI memakai SSE `/api/chat/stream` dengan request ID per pesan. Hanya satu request, `AbortController`, listener stream, dan timer Thinking yang aktif untuk satu giliran. Delta jawaban dibuffer sebelum dirender sehingga input tidak dibuat ulang pada setiap token. Event lama diabaikan bila request sudah selesai atau dibatalkan.

Panel **AI Thinking** berada di atas composer dan menampilkan durasi serta ringkasan tahap routing, workflow, ReAct, tool, dan riset. Event tidak boleh memuat chain-of-thought tersembunyi, credential, prompt mentah, argumen tool, atau output tool yang belum dipercaya. Tekan `Ctrl+T` untuk membuka ringkasan aktivitas dan `Escape` untuk membatalkan request aktif.

### Stabilitas renderer CLI

Ink memakai reconciliation React untuk memperbarui terminal. Flicker sebelumnya berasal dari timer status dan backdrop animasi yang mengubah parent tree, perubahan properti composer selama request, serta pembaruan delta tanpa lifecycle request yang ketat. Implementasi saat ini mempertahankan ID widget dan callback input, memoize header, backdrop, composer, conversation, dan footer, serta membatasi tick 100 ms dan 200 ms ke glyph spinner dan label waktu. Satu listener resize dimiliki root, streaming dibuffer 50 ms, dan scroll atau layout tidak dipicu oleh timer.

Lifecycle run memakai state `queued`, `planning`, `thinking`, `tool-running`, `waiting-approval`, `streaming`, lalu satu state terminal. Transisi ilegal dan event dengan request ID lama diabaikan. Activity digabung berdasarkan identitas stabil dan heartbeat SSE menjaga request panjang tetap aktif tanpa menampilkan reasoning internal.

### Timeout CLI dan workflow

| Variable | Default | Boundary |
|---|---:|---|
| `XNINETZY_THINK_TIMEOUT_SECONDS` | 120 | waktu sampai token pertama untuk chat normal |
| `XNINETZY_INACTIVITY_TIMEOUT_SECONDS` | 60 | waktu tanpa SSE event atau heartbeat |
| `XNINETZY_TOOL_TIMEOUT_SECONDS` | 180 | direct registry tool |
| `XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS` | 20 | koneksi dan katalog MCP eksternal |
| `XNINETZY_MCP_CALL_TIMEOUT_SECONDS` | 180 | satu call MCP eksternal |
| `XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS` | 900 | keseluruhan deep research dan stream CLI terkait |
| `XNINETZY_STREAM_TIMEOUT_SECONDS` | 300 | keseluruhan stream chat normal |
| `XNINETZY_SLOW_REQUEST_WARNING_SECONDS` | 45 | ambang label warning tanpa screen tint |

Timeout dan cancellation menghentikan reader, timer, dan listener, mempertahankan output parsial yang sudah diterima, serta menolak event terlambat.

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

## Single-owner state dan closed loop

Goal, task, roadmap, habit, workout, HEBAT, knowledge, dan event adalah state
milik instalasi—bukan milik satu transport. `chat_id` tetap direkam untuk asal,
delivery, serta conversation memory, tetapi tidak memecah entity owner. Karena
itu roadmap yang dibuat lewat MCP tetap terlihat dan dapat diselesaikan lewat
WhatsApp.

```text
HEBAT assignment ─represented_by→ shared task ─reminded_by→ reminder
roadmap item     ─represented_by→ shared task
                                      ↓ task_completed event
                           goal progress + roadmap progress
                                      ↓
                            Personal Context v2
```

Event ditulis lebih dahulu, lalu reducer mengonsumsinya dalam transaksi SQLite
dan menulis consumption marker. Event yang belum memiliki marker diputar ulang
saat AI startup. Completion task sendiri hanya menghasilkan event ketika status
benar-benar berubah, sehingga request ulang tidak menambah progress dua kali.

Scheduled jobs memakai tabel run yang sama untuk semua interface. Daily/weekly
key mencegah briefing dibuat dua kali, lease memulihkan job internal yang
terputus, dan weekly review menghitung event nyata. Detail operasional tersedia
di [Automation](/docs/automation/).

## OS Inbox dan attention kernel

OS Inbox adalah boundary antara capture dan commitment. WhatsApp, LangGraph,
MCP, Codex, Claude Code, dan OpenCode memanggil tool registry yang sama:

```text
input penting
  → os_capture
  → os_inbox_items
  → os_triage ──→ task bersama ──→ event/reducer
              └─→ archive

tasks + learning state + inbox
  → deterministic scoring
  → os_today / Personal Context / morning briefing
```

Capture dengan idempotency key yang sama tidak membuat row atau event kedua.
Promosi capture menulis task, entity link, perubahan status, dan event dalam
satu transaksi. Detail kontraknya tersedia di [OS kernel](/docs/os-kernel/).

## Security boundary

- Admin ditentukan dengan JID eksplisit.
- Chat API memerlukan bearer key dan owner JID pada single-owner mode.
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
