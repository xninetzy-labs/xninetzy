---
layout: ../../layouts/DocsLayout.astro
title: Quick start
description: Install Xninetzy on Linux, macOS, or Windows and connect an MCP host.
section: Start
---

Xninetzy runs as a single Python process. There is no Docker Compose
required for the default `local` mode — the MCP server runs over stdio and
hosts (Claude / Claude Code / Codex / OpenCode) launch the binary.

For self-hosted mode with optional heavier backends (Neo4j, FalkorDB),
see [Architecture](/docs/architecture/).

## Prerequisites

- Python 3.11 or later.
- `uv` (recommended) or `pip`.
- Git.
- A Flaz API key or credentials for another supported LLM provider (see
  [Providers](/docs/providers/)).
- An absolute path to an Obsidian vault (optional).

Verify prerequisites:

```bash
python --version
command -v uv
git --version
```

## Install

```bash
git clone <repo>
cd xninetzy
uv sync
cp .env.example .env
chmod 600 .env
```

Edit `.env` and set at minimum:

```dotenv
FLAZ_API_KEY=your-key-here
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/your/vault
```

## Initialize

```bash
uv run python -m xninetzy.cli.supervisor init
```

This:

- checks Python version, `uv`, `docker` (optional), `tesseract` (optional)
- creates `~/.local/share/xninetzy`, `~/Documents/xninetzy/output`,
  `~/Documents/xninetzy-vault`
- prints next-step instructions

## Start the MCP server

```bash
uv run python -m xninetzy.cli.supervisor start
```

The server listens on stdio by default. For Streamable HTTP:

```bash
XNINETZY_MCP_TRANSPORT=streamable-http \
XNINETZY_MCP_HTTP_HOST=127.0.0.1 \
XNINETZY_MCP_HTTP_PORT=8765 \
uv run python -m xninetzy.cli.supervisor start
```

then connect to `http://127.0.0.1:8765/mcp`.

## Connect an MCP host

### Claude Code

```bash
claude mcp add --scope user xninetzy \
  -e PYTHONUNBUFFERED=1 -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy \
  python -m xninetzy.interfaces.mcp_server
```

### Codex CLI

```bash
codex mcp add xninetzy -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy \
  python -m xninetzy.interfaces.mcp_server
```

### OpenCode

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
        "/home/you/code/xninetzy",
        "python",
        "-m",
        "xninetzy.interfaces.mcp_server"
      ],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

## Verify

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Expected output:

```
  [PASS   ] tool_registry            343 tools classified
  [PASS   ] secret_redaction         3/3 sample secrets redacted
  [PASS   ] safe_fetch               3/3 SSRF guard scenarios blocked
  [PASS   ] transport_config         transport=stdio host=127.0.0.1
  [PASS   ] sdk_pin                  mcp resolved=1.28.1
overall: PASS
```

If `tool_registry` reports fewer than 343 tools, an import failed. Check
the install log for missing optional dependencies.

## Next steps

- [Configuration](/docs/configuration/) — every env var explained
- [Providers](/docs/providers/) — switch LLM providers
- [Obsidian](/docs/obsidian/) — connect your vault
- [Global MCP](/docs/mcp/) — full MCP host connection guide
- [Security](/docs/security/) — review safety boundaries
