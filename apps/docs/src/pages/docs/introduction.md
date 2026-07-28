---
layout: ../../layouts/DocsLayout.astro
title: Pengenalan Xninetzy
description: Memahami Xninetzy sebagai Personal Learning OS, bukan sekadar chatbot WhatsApp.
section: Mulai
---

Xninetzy adalah **WhatsApp-first Personal Learning OS dan Life OS**. Sistem ini menghubungkan percakapan, knowledge base, catatan, tugas kampus, reminder, serta coding agent melalui satu registry tool yang sama.

## Masalah yang diselesaikan

Informasi personal biasanya tersebar: materi kuliah ada di Moodle, insight ada di chat, catatan ada di Obsidian, dan tugas teknis ada di repository. Xninetzy memberi satu pintu masuk untuk:

- menangkap informasi dari pesan, dokumen, PDF, atau gambar;
- mencari dan mengembangkan catatan Obsidian;
- membaca course serta materi HEBAT/Moodle;
- membuat roadmap, task, goal, dan reminder;
- melakukan research dan menyimpan hasilnya;
- memberi Codex, Claude Code, serta OpenCode akses tool yang sama melalui MCP.

## Prinsip desain

### Local-first, single-owner

Konfigurasi default ditujukan untuk satu pemilik pada mesin atau private network. SQLite, FAISS, session WhatsApp, browser profile HEBAT, dan media disimpan lokal.

### Natural language, deterministic escape hatch

Pesan biasa diproses melalui LangGraph. Slash command seperti `/llm`, `/approve`, atau `/today` melewati jalur deterministik agar aksi penting tidak bergantung pada interpretasi model.

### Human in the loop

Draft roadmap tidak otomatis aktif. Upload tugas, overwrite tertentu, dan aksi berdampak besar memakai confirmation token atau approval admin.

### Provider freedom

Flaz adalah default, bukan lock-in. Provider dipilih dari registry dan preferensi user dapat diubah tanpa mengganti kode agent.

## Apa yang bukan Xninetzy

Xninetzy bukan SaaS multi-tenant siap internet. HTTP API memiliki shared-secret
dan owner guard, tetapi model deployment tetap lokal/single-owner. Ia juga bukan
pengganti backup vault, LMS resmi, atau WhatsApp Business API.

> Jalankan di loopback atau private network. Baca [panduan keamanan](/docs/security/) sebelum membuka port ke mesin lain.

## Komponen utama

| Komponen | Teknologi | Tanggung jawab |
|---|---|---|
| AI service | Python, FastAPI, LangGraph | Routing, agent, tool registry, memory, HEBAT, Obsidian, MCP |
| WA engine | Node.js, TypeScript, Baileys | Socket WhatsApp, media, trigger group, HTTP MCP-style tools |
| Terminal CLI | Ink, React | Client alternatif ke `/api/chat` |
| Docs | Astro | Dokumentasi statis untuk operator dan contributor |

## Pilih jalur berikutnya

- Baru memasang project: buka [Quick start](/docs/getting-started/).
- Ingin memilih model: buka [Provider LLM](/docs/providers/).
- Ingin memakai vault: buka [Obsidian](/docs/obsidian/).
- Ingin memakai coding client dari folder mana pun: buka [MCP global](/docs/mcp/).
- Ingin memahami batas keamanan: buka [Keamanan](/docs/security/).
