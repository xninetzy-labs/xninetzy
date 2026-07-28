---
layout: ../../layouts/DocsLayout.astro
title: MCP global
description: Hubungkan registry Xninetzy ke Codex, Claude Code, dan OpenCode agar tersedia dari folder mana pun.
section: AI & developer tools
---

Xninetzy MCP memakai transport `stdio` dan mengekspos katalog tool langsung dari registry AI service. Konfigurasi global harus memakai **absolute path**; relative path hanya berfungsi ketika client dibuka dari repository.

MCP ini adalah pintu masuk owner lokal ke OS yang sama dengan WhatsApp dan
LangGraph. Identitas context diinjeksi oleh server; parameter `sender_id`,
`sender_name`, dan `chat_id` tidak dipercaya dari client.

## Prasyarat

```bash
cd /absolute/path/to/xninetzy/services/ai
uv sync
```

Catat dua path:

```bash
command -v uv
pwd
```

Contoh di bawah memakai:

```text
/home/you/.local/bin/uv
/home/you/code/xninetzy/services/ai
```

Ganti dengan path milikmu.

## Codex global

Codex CLI, IDE extension, dan Codex desktop pada host yang sama berbagi `~/.codex/config.toml`.

```bash
codex mcp add xninetzy -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy/services/ai \
  python -m app.xninetzy.interfaces.mcp_server
```

Tambahkan timeout pada `~/.codex/config.toml` jika tool browser/research membutuhkan waktu lebih lama:

```toml
[mcp_servers.xninetzy]
command = "/home/you/.local/bin/uv"
args = ["run", "--directory", "/home/you/code/xninetzy/services/ai", "python", "-m", "app.xninetzy.interfaces.mcp_server"]
startup_timeout_sec = 30
tool_timeout_sec = 120
```

Verifikasi:

```bash
cd /tmp
codex mcp get xninetzy
codex mcp list
```

## Claude Code global

Scope `user` membuat server tersedia pada seluruh project:

```bash
claude mcp add --scope user xninetzy \
  -e PYTHONUNBUFFERED=1 -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy/services/ai \
  python -m app.xninetzy.interfaces.mcp_server
```

Verifikasi dari luar repository:

```bash
cd /tmp
claude mcp get xninetzy
claude mcp list
```

Output seharusnya menampilkan `Scope: User config` dan `Connected`.

## OpenCode global

Edit `~/.config/opencode/opencode.jsonc`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "xninetzy": {
      "type": "local",
      "command": [
        "/home/you/.local/bin/uv",
        "run",
        "--directory",
        "/home/you/code/xninetzy/services/ai",
        "python",
        "-m",
        "app.xninetzy.interfaces.mcp_server"
      ],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

Jika file memiliki konfigurasi lain, merge key `mcp.xninetzy`; jangan menimpa seluruh file.

```bash
cd /tmp
opencode mcp list
opencode debug config
```

## Uji pemakaian

Buka salah satu client dari directory bebas lalu gunakan prompt:

```text
Gunakan MCP xninetzy untuk menampilkan daftar note pada folder Learning.
```

Atau:

```text
Gunakan MCP xninetzy untuk membaca course HEBAT yang tersedia tanpa melakukan submission.
```

Untuk jawaban dari knowledge base gunakan:

```text
Gunakan knowledge_answer dari MCP xninetzy untuk menjawab pertanyaan ini dan pertahankan sitasi sumbernya.
```

`knowledge_search` hanya menampilkan evidence terpilih untuk inspeksi.
`knowledge_answer` melakukan hybrid retrieval, sintesis, dan validasi sitasi.
Jika evidence tidak cukup, client harus menyampaikan kekurangan tersebut.

## Path dan environment

Server menjalankan AI project sehingga root `.env` tetap terbaca. Jangan menaruh API key langsung dalam file MCP.

```dotenv
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

`auto` memetakan path container standar ke data host ketika server berjalan di luar Docker.

## Menghapus konfigurasi

```bash
codex mcp remove xninetzy
claude mcp remove xninetzy --scope user
```

Untuk OpenCode, hapus hanya object `mcp.xninetzy` dari config global.

## Troubleshooting

- Gunakan path absolut untuk binary `uv` dan directory AI.
- Jalankan `uv sync` pada `services/ai`.
- Pastikan stdout server tidak berisi log biasa; stdout adalah protocol stream.
- Jalankan `claude mcp list` atau `opencode mcp list` untuk health check.
- Jika repository dipindah, perbarui ketiga absolute path global.
- Restart IDE/client setelah mengubah config.

> Global berarti tersedia dari folder mana pun pada host yang sama. Ia tidak menyalin repository atau credential ke mesin lain.
