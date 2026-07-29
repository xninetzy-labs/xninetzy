---
layout: ../../layouts/DocsLayout.astro
title: OS Inbox dan attention kernel
description: Tangkap input tanpa kehilangan konteks, proses menjadi commitment, dan pilih fokus dari state Xninetzy yang nyata.
section: Integrasi
---

OS kernel menutup celah antara “aku baru kepikiran sesuatu” dan “apa yang harus
aku kerjakan sekarang?”. Ia bukan transport baru. WhatsApp, internal LangGraph,
Codex, Claude Code, dan OpenCode memakai service serta tabel yang sama.

## Closed-loop yang didukung

```text
Capture → Understand → Plan → Execute → Review → Adapt
   │          │          │
OS Inbox   Triage     Attention queue
```

OS Inbox menerima input penting tanpa langsung memaksanya menjadi task. Triage
kemudian mengubah capture menjadi commitment eksplisit atau archive. Attention
queue menggabungkan task, deadline, prioritas, learning state, dan capture yang
belum diproses.

## Command WhatsApp

```text
/capture ide membuat mini project event sourcing
/capture pelajari materi klasifikasi minggu depan
/inbox
/triage 12 task
/triage 13 archive
/today
```

`/today` menampilkan fokus utama, alasan prioritas, next action, dan queue
berikutnya. Task overdue dan due hari ini mendapat bobot lebih tinggi. Learning
plan aktif ikut muncul selama tidak menduplikasi task yang sudah ada.

## Tool bersama

| Tool | Fungsi |
|---|---|
| `os_capture` | Menyimpan capture dan mengklasifikasikan jenisnya secara deterministik |
| `os_inbox` | Menampilkan capture berdasarkan status |
| `os_triage` | Memproses capture menjadi task atau archive |
| `os_today` | Menyusun attention queue lintas state OS |

Contoh dari Codex, Claude Code, atau OpenCode:

```text
Gunakan MCP xninetzy untuk memanggil os_capture dengan isi "pelajari CQRS".
Setelah itu tampilkan os_inbox dan os_today.
```

Field identitas seperti `chat_id` tidak terlihat pada schema MCP. MCP server
menyuntikkan principal trusted-local-owner agar caller tidak dapat memalsukan
scope transport.

## Replay safety

`os_capture` menerima `idempotency_key` melalui tool registry/MCP. Key yang sama
dengan isi yang sama mengembalikan capture awal; key yang sama untuk isi berbeda
ditolak. Satu capture hanya bisa diproses sekali.

Promosi ke task menyimpan empat perubahan dalam satu transaksi SQLite:

1. task bersama;
2. entity link dari capture ke task;
3. status capture `processed`;
4. ecosystem event untuk reducer.

Pemanggilan ulang mengembalikan target terdahulu dan tidak membuat task, link,
atau event kedua.

## Hubungan dengan konteks dan automation

Personal Context menyertakan tiga attention item teratas dan jumlah inbox yang
belum diproses. Morning briefing memakai sumber yang sama. Karena itu fokus yang
terlihat di WhatsApp konsisten dengan internal LangGraph dan client MCP.

## Batas saat ini

- Triage eksplisit baru mendukung target `task` dan `archive`.
- Klasifikasi capture bersifat deterministik dan sengaja konservatif.
- Attention queue belum memasukkan kalender eksternal atau estimasi kapasitas.
- Promote ke note/knowledge/goal akan ditambahkan melalui adapter domain yang
  tetap memakai invariant transaksi dan idempotensi yang sama.
