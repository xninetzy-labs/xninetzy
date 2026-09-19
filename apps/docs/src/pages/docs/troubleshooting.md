---
layout: ../../layouts/DocsLayout.astro
title: Troubleshooting
description: Diagnose MCP, provider, Obsidian, HEBAT, permission, and documentation failures.
section: Operations
---

Start with health checks and the nearest system boundary. Do not begin by
deleting sessions, databases, or volumes.

## The model cannot be reached

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Inspect enabled providers, model allowlists, base URL, and credentials, then
restart after changing `.env`:

```bash
uv run --no-project --directory . \
  python -c "from xninetzy.core.config import get_settings; print(get_settings().AI_PROVIDER)"
```

## MCP server does not start

- Confirm `XNINETZY_MCP_TRANSPORT` is `stdio` or `streamable-http`. Other
  values raise `ValueError` at boot.
- Confirm `XNINETZY_MCP_HTTP_HOST` parses as an IP. A hostname raises
  `ValueError`.
- For Streamable HTTP: confirm the host is loopback (`127.0.0.1` / `::1`).
  Non-loopback triggers a stderr WARNING and OAuth is required before
  real use.
- Run the release gate: `uv run python -m xninetzy.cli.supervisor release-check`.
  It checks `tool_registry`, `secret_redaction`, `safe_fetch`,
  `transport_config`, `sdk_pin` and reports which check failed.

## CAPTCHA / OCR keeps failing

`xninetzy/os/security/captcha/lockout.py` disables OCR after
`XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD` failures within
`XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS`. After the lockout, OCR is
suspended for `XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS`.

Diagnose:

```bash
uv run --no-project --directory . \
  python -c "from xninetzy.core.config import get_settings; s=get_settings(); print(
    s.XNINETZY_CAPTCHA_OCR_ENABLED,
    s.XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD,
    s.XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS,
    s.XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS,
    s.XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE,
  )"
```

If `should_allow_ocr()` returns `False`, owner must solve manually or
wait out the cooldown. Owner fallback via WA delivery is controlled by
`XNINETZY_CAPTCHA_WA_PREFERRED` and `XNINETZY_CAPTCHA_DIR`.

## A document or image cannot be read

1. confirm the file lives under `OUTPUT_DIR`, `RESEARCH_OUTPUT_DIR`,
   `GENERATED_DOCUMENTS_DIR`, or `UNTRACKED_OUTPUT_DIR` — `ARTIFACT_ALLOWLIST`
   rejects writes outside those roots;
2. inspect MIME type, extension, checksum, and size limits;
3. verify Tesseract and required language packs are installed;
4. enable OCR fallback for scanned PDFs (`XNINETZY_CAPTCHA_OCR_ENABLED`).

## Obsidian cannot write

- `OBSIDIAN_VAULT_HOST_PATH` is absolute and exists.
- `OBSIDIAN_ALLOW_WRITE=true` (default).
- `OBSIDIAN_ALLOW_DELETE=false` (default) — deletions require explicit
  approval.
- Tool input uses vault-relative paths.
- The vault is not mounted read-only.

## HEBAT login or download fails

Inspect credentials, Chromium, browser-profile permissions, session
expiry, portal maintenance, selector changes, and downloaded file magic
bytes:

```bash
hebat_login_status
hebat_login_status_verbose
hebat_sync_courses
```

Configuration knobs in `xninetzy/core/config.py`:

| Var | Default | Notes |
|---|---|---|
| `HEBAT_BROWSER_HEADLESS` | `true` | flip to `false` to watch login |
| `HEBAT_AUTO_LOGIN` | `false` | requires explicit opt-in |
| `HEBAT_REQUIRE_CONFIRMATION` | `true` | gate submissions |
| `HEBAT_RATE_LIMIT_SECONDS` | `2.0` | throttle |
| `HEBAT_DEBUG_SAVE_HTML` | `false` | persist debug HTML when selectors drift |

## GraphRAG timeout or Neo4j offline

SQLite is canonical. Neo4j and FAISS are rebuildable projections, so
retrieval can continue when Neo4j is offline. Autostart has bounded
command, readiness, and connection timeouts plus a failure cooldown.

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

Keep `NEO4J_ENABLED=false` when Docker or Neo4j is not used. Deliberately
raise the readiness timeout for a slow cold image. Never delete canonical
SQLite to recover a projection timeout.

## MCP is unavailable outside the repository

```bash
claude mcp list
codex mcp list
opencode mcp list
```

Replace relative paths with absolute global configuration. Update all
clients after moving the repository. See [Global MCP](/docs/mcp/).

### Claude waits for approval

A project `.mcp.json` entry requires approval. For global use, prefer
the user-scope registry.

### OpenCode is not connected

```bash
opencode debug paths
opencode debug config
```

Inspect `~/.config/opencode/opencode.jsonc`, JSON syntax, the absolute
`uv` path, timeout, and Python dependencies.

### MCP protocol error

Stdout carries protocol frames only. Send application logging to stderr.
Run the focused tests:

```bash
uv run --no-project --directory . pytest -q \
  tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

## SQLite or download permission denied

Inspect ownership of `DATA_DIR`, `OBSIDIAN_VAULT_HOST_PATH`, and
`HEBAT_DATA_DIR`. Do not alternate between root and a normal user.

## Port already in use

```bash
ss -ltnp | grep -E ':8000|:8765'
```

Stop the unused instance. Default ports: FastAPI `8000`, Streamable HTTP
`8765`. Both default to loopback.

## Documentation build fails

```bash
cd apps/docs
node --version
yarn install --frozen-lockfile
yarn check
yarn build
```

Astro 7 requires Node 22.12 or newer. Read the error before removing a
cache; never delete source files or the lockfile as a first response.

## Bug-report information

Include:

- the exact command;
- expected and actual results;
- release-check output;
- Python, Node, and client versions;
- sanitized logs (no `AI_API_KEY`, no `HEBAT_PASSWORD`, no private JIDs);
- the smallest failing test.

Never include API keys, passwords, cookies, grade tokens, or sensitive
document content.
