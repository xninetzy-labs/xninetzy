---
layout: ../../layouts/DocsLayout.astro
title: Coding agents dari WhatsApp
description: Konfigurasikan Codex, Claude Code, atau OpenCode sebagai runtime coding dengan workspace, timeout, dan audit boundary.
section: AI & developer tools
---

Coding runtime menjalankan CLI lokal terhadap repository. Fitur ini terpisah dari provider LLM chat dan memiliki risiko lebih tinggi karena dapat membaca atau mengubah file.

## Persyaratan

- Binary runtime terpasang pada host AI service.
- CLI sudah login secara interaktif oleh pemilik.
- Workspace dan allowed root menggunakan absolute path.
- Admin WhatsApp memakai JID eksplisit.
- AI service berjalan di host, bukan container standar tanpa binary/session.

## Konfigurasi

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=codex
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/xninetzy
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_MAX_OUTPUT_CHARS=30000
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_REQUIRE_XNINETZY_MCP=true
CODING_AGENT_MCP_SERVER_NAME=xninetzy
CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS=15
```

Jangan memakai `/`, home directory, atau directory luas sebagai allowed root.

## Penggunaan

```text
/agent list
/agent use codex
/code jalankan test terkait reminder dan jelaskan kegagalannya
```

Pilih runtime lain:

```text
/agent use claude-code
/agent use opencode
```

Preference runtime disimpan per user. Hanya runtime yang masuk allowlist dapat dipilih.

## Guard eksekusi

Runtime wrapper:

- tidak membangun command melalui shell interpolation;
- membatasi current working directory pada allowed root;
- meneruskan environment minimal;
- membatasi durasi serta panjang output;
- menyimpan audit run;
- menolak non-admin ketika `CODING_AGENT_ADMIN_ONLY=true`.
- memverifikasi MCP `xninetzy` sebelum menjalankan task;
- menyisipkan kontrak `AGENTS.md`, akses OS bersama, dan grounded knowledge ke prompt task.

Sandbox akhir juga bergantung pada kemampuan CLI yang dipilih. Jangan menganggap semua runtime memiliki semantic sandbox identik.

## Hubungan dengan MCP

Ada dua arah integrasi:

1. Coding client memakai Xninetzy MCP untuk Obsidian, HEBAT, task, dan tools lain.
2. WhatsApp meminta Xninetzy menjalankan coding client pada workspace.

Keduanya dapat aktif bersamaan, tetapi tidak berarti satu client otomatis mewarisi login client lain.

Saat runtime dipanggil dari WhatsApp, preflight harus menemukan konfigurasi MCP
global/user milik CLI tersebut. Xninetzy sengaja gagal tertutup apabila MCP tidak
tersedia agar coding agent tidak memberikan hasil yang kehilangan context vault,
HEBAT, task, atau knowledge pemilik.

## Workflow yang aman

Gunakan task sempit dan dapat diverifikasi:

```text
/code diagnosis kenapa test test_reminder_parser gagal; jangan ubah file
```

Setelah diagnosis:

```text
/code implementasikan perbaikan yang sudah dianalisis, jalankan test terkait, lalu rangkum file yang berubah
```

Hindari prompt seperti “perbaiki semuanya” pada repository dengan data/runtime state yang belum dibackup.

## Container limitation

Docker image AI standar tidak menyertakan:

- binary Codex/Claude/OpenCode;
- login store personal;
- konfigurasi global host.

Pilihan paling sederhana adalah menjalankan AI service lokal pada host. Alternatif container membutuhkan image custom, volume login terarah, dan review security khusus.

## Diagnosis

```bash
which codex
which claude
which opencode
```

Periksa log audit tanpa mencetak credential. Error umum berasal dari binary tidak ditemukan, login kedaluwarsa, workspace di luar allowed root, timeout, atau CLI meminta input interaktif.
