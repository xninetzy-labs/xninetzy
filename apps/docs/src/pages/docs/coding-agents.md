---
layout: ../../layouts/DocsLayout.astro
title: Coding agents dari WhatsApp
description: Konfigurasikan Codex, Claude Code, atau OpenCode sebagai runtime coding dengan workspace, timeout, dan audit boundary.
section: AI & developer tools
---

Coding runtime menjalankan CLI lokal terhadap repository. Fitur ini terpisah dari provider LLM chat dan memiliki risiko lebih tinggi karena dapat membaca atau mengubah file.

## Persyaratan

- Binary Codex, Claude Code, atau OpenCode terpasang pada host laptop.
- CLI sudah login secara interaktif oleh pemilik.
- Host bridge Xninetzy aktif sebagai user service.
- Workspace dan allowed root menggunakan absolute path.
- Admin WhatsApp memakai JID eksplisit.
- Konfigurasi MCP global `xninetzy` tersedia untuk setiap CLI.

## Konfigurasi

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=opencode
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_EXECUTION_MODE=host_bridge
CODING_AGENT_HOST_BRIDGE_URL=http://host.docker.internal:8765
CODING_AGENT_HOST_BRIDGE_TOKEN=<random-secret>
CODING_AGENT_HOST_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_HOST_ALLOWED_ROOT=/absolute/path/to/xninetzy
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

## Host bridge dan container

AI service Docker tidak menyertakan binary coding, login store, atau konfigurasi
global host. Dalam mode `host_bridge`, AI mengirim task terautentikasi ke
`127.0.0.1:8765` melalui `host.docker.internal`; bridge menjalankan CLI di host,
melakukan MCP preflight, membatasi workspace, dan mengembalikan output ke
WhatsApp. Install otomatis:

```bash
bash scripts/install_host_agent_bridge.sh
loginctl enable-linger "$USER"
systemctl --user status xninetzy-host-agent-bridge
```

Jangan mengekspos port bridge ke jaringan publik dan jangan menaruh token bridge
di prompt atau konfigurasi MCP client.

## Diagnosis

```bash
which codex
which claude
which opencode
```

Periksa log audit tanpa mencetak credential. Error umum berasal dari binary tidak ditemukan, login kedaluwarsa, workspace di luar allowed root, timeout, atau CLI meminta input interaktif.
