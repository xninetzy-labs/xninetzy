---
layout: ../../layouts/DocsLayout.astro
title: Troubleshooting
description: Diagnose provider, WhatsApp, media, Obsidian, HEBAT, MCP, permission, and documentation failures.
section: Operations
---

Start with health checks and the nearest system boundary. Do not begin by
deleting sessions, databases, or volumes.

## The model cannot be reached

```text
/llm list
```

Inspect enabled providers, model allowlists, base URL, and credentials, then
restart the service after changing `.env`.

```bash
cd services/ai
uv run python scripts/configure_flaz.py
```

## QR or pairing code does not appear

```bash
docker compose logs -f wa-enggine
```

Verify `WA_LOGIN_MODE`. Pairing requires `WA_PHONE_NUMBER`. Do not remove the
session volume before confirming that the session is corrupt.

## The bot ignores a group

```dotenv
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

Mention the bot, reply to its message, or use the `!` prefix.

## A document or image cannot be read

1. reply to the attachment and run `/media-info`;
2. verify the file exists in shared `WA_MEDIA_DIR`;
3. verify both services resolve the same storage;
4. inspect MIME type, extension, checksum, and size limits;
5. verify Tesseract and required language packs;
6. enable OCR fallback for scanned PDFs.

## AI cannot call WhatsApp tools

```bash
curl -s http://127.0.0.1:8081/health
```

Verify `socket_ready=true`, `WA_MCP_BASE_URL`, and that
`WA_MCP_API_KEY` equals `MCP_API_KEY`.

## Obsidian cannot write

- `OBSIDIAN_VAULT_HOST_PATH` is absolute and exists.
- The container UID and GID can access the vault.
- `OBSIDIAN_ALLOW_WRITE=true`.
- Tool input uses vault-relative paths.
- The extension is allowlisted.
- The vault is not mounted read-only.

## HEBAT login or download fails

```text
/hebat-debug
```

Inspect credentials, Chromium, browser-profile permissions, session expiry,
portal maintenance, selector changes, and downloaded file magic bytes.

## GraphRAG timeout or Neo4j offline

GraphRAG V3 keeps SQLite canonical. Neo4j and FAISS are rebuildable projections,
so retrieval can continue when Neo4j is offline. Autostart has bounded command,
readiness, and connection timeouts plus a failure cooldown.

Inspect state without forcing startup:

```text
graph_v3_stats
```

```dotenv
NEO4J_ENABLED=false
NEO4J_AUTOSTART_ENABLED=true
NEO4J_AUTOSTART_COMMAND_TIMEOUT_SECONDS=8
NEO4J_AUTOSTART_READINESS_TIMEOUT_SECONDS=10
NEO4J_CONNECT_TIMEOUT_SECONDS=3
NEO4J_FAILURE_COOLDOWN_SECONDS=60
```

Keep `NEO4J_ENABLED=false` when Docker or Neo4j is not used. Deliberately raise
the readiness timeout for a slow cold image. The smaller legacy
`NEO4J_AUTOSTART_BOOT_TIMEOUT_SECONDS` remains an upper bound. Never delete
canonical SQLite to recover a projection timeout.

## MCP is unavailable outside the repository

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

Replace relative AI paths with absolute global configuration. Update all clients
after moving the repository.

### Claude waits for approval

A project `.mcp.json` entry requires approval. For global use,
`claude mcp get xninetzy` should report `Scope: User config`.

### OpenCode is not connected

```bash
opencode debug paths
opencode debug config
```

Inspect `~/.config/opencode/opencode.jsonc`, JSON syntax, the absolute `uv`
path, timeout, and Python dependencies.

### MCP protocol error

Stdout carries protocol frames only. Send application logging to stderr.

```bash
cd services/ai
uv run pytest -q tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

## SQLite or download permission denied

Inspect `HOST_UID`, `HOST_GID`, ownership of `services/ai/data`, and vault
ownership. Do not alternate between root and a normal user.

## Port already in use

```bash
ss -ltnp | grep -E ':8000|:8081'
docker compose ps
```

Stop the unused instance. Do not run host and Docker services on the same ports.

## Documentation build fails

```bash
cd apps/docs
node --version
yarn install --frozen-lockfile
yarn check
yarn build
```

Astro 7 requires Node 22.12 or newer. Read the error before removing a cache;
never delete source files or the lockfile as a first response.

## Bug-report information

Include:

- the exact command;
- expected and actual results;
- health state;
- Python, Node, and client versions;
- sanitized logs;
- host or Docker scope, chat type, and text or media scope;
- the smallest failing test.

Never include API keys, passwords, cookies, private JIDs, or sensitive document
content.
