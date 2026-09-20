---
layout: ../../layouts/DocsLayout.astro
title: Quick start
description: Install Xninetzy with one curl command or git clone, then connect an MCP host.
section: Start
badge: How-to
difficulty: beginner
readingTime: 5 min
---

Xninetzy runs as a single Python process. The default `local` mode is
just Python — no Docker required, no LLM credentials required. The MCP
server runs over stdio by default and is reachable over Streamable HTTP
on loopback.

## One-line install

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

Override the source repo (for mirrors or forks):

```bash
XNINETZY_REPO_URL=https://raw.githubusercontent.com/your-fork/xninetzy/main \
  curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

The script:

- detects OS via `uname -s` and refuses to run on unsupported systems
- ensures `git` + `openssl` are present; auto-installs `uv` (Homebrew on
  macOS, official installer on Linux) if missing
- clones the repo to `~/xninetzy`
- installs OS-level dependencies via the system package manager:
  - **Debian/Ubuntu**: `tesseract-ocr`, `tesseract-ocr-eng`, `sqlite3`,
    `libatlas3-base`, `liblapack3`, `libgomp1`, `libxml2`, `libxslt1.1`
  - **Fedora/RHEL**: `tesseract`, `sqlite`, `atlas`, `lapack`, `openssl-devel`
  - **Arch**: `tesseract`, `sqlite`, `atlas`, `lapack`, `openssl`
  - **macOS (brew)**: `tesseract`, `sqlite`
- runs `uv sync --all-extras` to pull the full Python dependency set:
  `mcp`, `fastapi`, `uvicorn`, `pydantic`, `langchain-core`, `playwright`,
  `httpx`, `beautifulsoup4`, `lxml`, `pypdf`, `numpy`, `faiss-cpu`,
  `sentence-transformers`, `torch` (CPU-only), `neo4j`, `networkx`,
  `pytesseract`, `pdfplumber`, `cryptography`, `openpyxl`, `python-pptx`,
  `python-docx`, `pillow`, `opencv-python-headless`, `ddgs`
- installs the Playwright Chromium binary (`python -m playwright install
  chromium --with-deps`) for the HEBAT browser
- sets `NEO4J_ENABLED=true` and installs Neo4j if
  `XNINETZY_INSTALL_NEO4J=true`
- copies `.env.example` → `.env` with a random `AI_API_KEY`
- creates the Obsidian vault directory
- runs the release gate

### Windows (PowerShell 5.1+)

```powershell
iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
```

The script:

- forces TLS 1.2 (`[Net.ServicePointManager]::SecurityProtocol`)
- installs `uv` to `%USERPROFILE%\.local\bin` if missing
- clones to `$HOME\xninetzy` (`%USERPROFILE%\xninetzy`)
- sets hidden attribute on `.env`
- runs `uv sync --all-extras` to pull the full Python dependency set
  (same list as the bash script — `mcp`, `fastapi`, `faiss-cpu`, `torch`
  CPU, `sentence-transformers`, `neo4j`, `playwright`, `langchain-core`,
  `pytesseract`, `pdfplumber`, `cryptography`, `ddgs`, etc.)
- installs the Playwright Chromium binary (`python -m playwright install
  chromium`) for the HEBAT browser
- sets `NEO4J_ENABLED=true` and installs Neo4j via choco if
  `$env:XNINETZY_INSTALL_NEO4J = 'true'`
- runs the release gate

Note: Windows scripts skip the apt/dnf package step. SQLite ships in
Python on Windows. Tesseract is required only if you opt into OCR
(set `XNINETZY_CAPTCHA_OCR_ENABLED=true`); install it from
<https://github.com/UB-Mannheim/tesseract/wiki> if needed.

Use a non-default branch:

```bash
XNINETZY_BRANCH=v2.2.0 curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

```powershell
$env:XNINETZY_BRANCH = 'v2.2.0'
iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
```

Use the Docker compose path instead:

```bash
XNINETZY_INSTALL_MODE=docker curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

```powershell
$env:XNINETZY_INSTALL_MODE = 'docker'
iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
```

## Manual install

If you'd rather drive each step yourself:

```bash
git clone https://github.com/xninetzy-labs/xninetzy
cd xninetzy
uv sync --all-extras
cp .env.example .env
chmod 600 .env
```

Edit `.env` and set at minimum:

```dotenv
AI_API_KEY=<openssl rand -hex 32>
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/your/vault
```

Xninetzy is MCP-only. The host (Claude, Claude Code, Codex, OpenCode,
Cursor) supplies the chat model. No LLM credentials belong in this file
unless you also run the optional `/api/chat` HTTP bridge with a private
provider.

## Prerequisites

- Python 3.11 or later.
- `uv` (recommended) or `pip`.
- Git.
- An absolute path to an Obsidian vault (optional).

Verify:

```bash
python --version
command -v uv
git --version
```

## Initialize

```bash
uv run python -m xninetzy.cli.supervisor init
```

This checks Python version, `uv`, `docker` (optional), `tesseract`
(optional), and creates `~/.local/share/xninetzy`,
`~/Documents/xninetzy/output`, `~/Documents/xninetzy-vault`.

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

See [Global MCP](/docs/mcp/) for full host connection reference.

## Verify

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Expected output:

```text
  [PASS   ] tool_registry            385 tools classified
  [PASS   ] secret_redaction         3/3 sample secrets redacted
  [PASS   ] safe_fetch               3/3 SSRF guard scenarios blocked
  [PASS   ] transport_config         transport=stdio host=127.0.0.1
  [PASS   ] sdk_pin                  mcp resolved=1.28.1
  [PASS   ] canonical_final_tools    3 FINAL tools match canonical set

overall: PASS
```

The `release-check` subcommand delegates to `scripts/mcp_audit.py --json`
and emits one `[PASS] / [FAIL]` line per check. The audit script is the
canonical contract; this wrapper exists for ergonomic invocation.

If `tool_registry` reports fewer than 385 tools, an import failed.
Check the install log for missing optional dependencies.

## SDK-style install (future)

`pip install xninetzy-mcp` and `uvx xninetzy` are not yet published.
Today the canonical install paths are the curl one-liner, the manual
`git clone` + `uv sync`, and the Docker compose path. Publishing to
PyPI would require flipping `pyproject.toml`'s `tool.uv.package = true`
and adding a `[build-system]` table — tracked as a follow-up.

## Next steps

- [MCP system reference](/docs/mcp-system/) — canonical truth on transports, registry, gateway
- [Configuration](/docs/configuration/) — every env var explained
- [Obsidian](/docs/obsidian/) — connect your vault
- [Global MCP](/docs/mcp/) — full MCP host connection guide
- [Security](/docs/security/) — review safety boundaries
