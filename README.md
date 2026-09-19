# Xninetzy

> Local-first, MCP-only Personal Intelligence and Learning system. One
> FastMCP server, stdio primary, Streamable HTTP loopback by default.
> 343 tools under one canonical registry.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio%20%2B%20Streamable%20HTTP-6C47FF)
![SDK](https://img.shields.io/badge/mcp-1.28.1%20(v1.x)-1C3C3C)
![Tools](https://img.shields.io/badge/tools-343-009688)
![CPU](https://img.shields.io/badge/CPU--only-2496ED)
![License](https://img.shields.io/badge/license-Xninetzy--SAL%20v2.2.0-6C47FF)

Xninetzy exposes a single MCP server to your host (Claude, Claude Code,
Cursor, Codex, OpenCode). Obsidian, HEBAT, Cyber Campus, Lightning,
Knowledge, Career, reminders, skills, and automation share one canonical
registry. There is no server-side agent loop, no REST surface, no CLI
client, no WhatsApp engine.

The host owns reasoning, planning, and tool selection. Xninetzy owns
capability, replay safety, idempotency, owner identity, and approval
gates.

```text
host (Claude / Claude Code / Cursor / Codex / OpenCode)
  │  stdio   or   Streamable HTTP (loopback by default)
  ▼
xninetzy.interfaces.mcp_server   ─── FastMCP("xninetzy", ...)
  │
  ├── xninetzy.tools.registry.get_all_tools()   (343 tools)
  │     └── xninetzy.tools.manifest.manifest_for(name)
  │           ├── feature_pack: core | academic-unair | research | coding
  │           ├── risk:         read | draft | write | final
  │           └── requires_approval / requires_idempotency / requires_evidence
  │
  ├── xninetzy.interfaces.tasks_extension          (SEP-2663, 4 tools)
  ├── xninetzy.interfaces.external_mcp             (gateway, 5 tools)
  ├── xninetzy.observability.trace                 (SEP-414, W3C traceparent)
  └── xninetzy.os.security.captcha.lockout         (CAPTCHA auto-OCR guard)
```

## Contents

- [Capabilities](#capabilities)
- [Quick install](#quick-install)
- [Transports](#transports)
- [Connect an MCP host](#connect-an-mcp-host)
- [Repository layout](#repository-layout)
- [Run for development](#run-for-development)
- [HTTP bridge](#http-bridge-secondary)
- [Data and persistence](#data-and-persistence)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Documentation map](#documentation-map)

## Capabilities

| Area | Capabilities |
|---|---|
| MCP server | FastMCP("xninetzy", stateless_http, json_response) over stdio + Streamable HTTP on loopback |
| Tool registry | 343 tools classified by risk (read/draft/write/final), feature pack (core/academic-unair/research/coding), idempotency, stability |
| Obsidian | list, search, read, create, append, frontmatter, tags, headings, backlinks, todos, MOC, daily note, vault init / organize / verify |
| HEBAT / Moodle | login (Playwright Chromium), course sync, activity sync, material download, PDF read, assignment digest, submission with HITL approval |
| Cyber Campus | profile, academic status, schedule, grades, KRS capabilities, KRS War arm/disarm/execute (FINAL), grade-token submission |
| Knowledge | text/file ingest, hybrid FAISS retrieval, evidence selection, grounded Q&A with citations, Graph RAG projection (Neo4j opt-in) |
| Career | RemoteOK + ArbeitNow adapters, 17 MCP tools, 19 skill bodies, no wall-garden scraping |
| Lightning | CPU-only contextual bandit: episode / action / outcome / reward / strategy ranking / proposal + approval / regression check (15 tools) |
| Skills | 68 skill bodies under `.agents/skills/`, owner-scoped install via MCP, progressive disclosure, healthcheck |
| Reminders + Life OS | task, capture, triage, attention queue, reminders, habits, goals, automation leases |
| Security | HITL approvals, scope tokens, SSRF guards, secret redaction, NS trace context, CAPTCHA lockout |
| External MCP gateway | untrusted-by-default registry, `risk_level` + `allowed_tools` allowlist, owner-scoped registration |

## Quick install

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

### Windows (PowerShell 5.1+)

```powershell
iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
```

Override the source repo (mirror / fork):

```bash
XNINETZY_REPO_URL=https://raw.githubusercontent.com/your-fork/xninetzy/main \
  curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

Both scripts:

- refuse to run on unsupported OS
- ensure `git` + `openssl`; auto-install `uv` (Homebrew on macOS,
  official installer on Linux, `%USERPROFILE%\.local\bin` on Windows)
- clone the repo at the requested branch
- install OS dependencies (`tesseract`, `sqlite3`, `libatlas`/`lapack`
  via `apt`/`dnf`/`pacman`/`brew`)
- run `uv sync --all-extras` (full Python dep set: `mcp`, `fastapi`,
  `uvicorn`, `pydantic`, `langchain-core`, `playwright`, `httpx`,
  `beautifulsoup4`, `lxml`, `pypdf`, `numpy`, `faiss-cpu`,
  `sentence-transformers`, `torch` CPU, `neo4j`, `networkx`,
  `pytesseract`, `pdfplumber`, `cryptography`, `ddgs`,
  `opencv-python-headless`)
- install Playwright Chromium (`python -m playwright install chromium`)
- opt-in Neo4j via `XNINETZY_INSTALL_NEO4J=true`
- write a random `AI_API_KEY`, set `OBSIDIAN_VAULT_HOST_PATH`
- run `xninetzy.cli.supervisor release-check`

### Manual install

```bash
git clone https://github.com/xninetzy-labs/xninetzy
cd xninetzy
uv sync --all-extras
bash scripts/setup-mcp.sh
```

### Two remotes

| Remote | URL | Role |
|---|---|---|
| `origin` | `git@github.com:xninetzy-labs/xninetzy.git` | canonical, where releases land |
| `public` | `https://github.com/misbahul45/xninetzy.git` | public mirror, updated via `scripts/sync-public.sh` |

After tagging a release on `origin`, mirror to `public`:

```bash
bash scripts/sync-public.sh
```
cp .env.example .env
chmod 600 .env
```

Xninetzy is MCP-only. The host (Claude, Claude Code, Cursor, Codex,
OpenCode) supplies the chat model. No LLM credentials belong in this
file unless you also opt into the optional `/api/chat` HTTP bridge with
a private fallback provider.

### Initialize

```bash
uv run python -m xninetzy.cli.supervisor init
```

This checks Python, `uv`, `docker` (optional), `tesseract` (optional),
and creates `~/.local/share/xninetzy`, `~/Documents/xninetzy/output`,
`~/Documents/xninetzy-vault`.

## Transports

| Transport | Status | Default | How |
|---|---|---|---|
| stdio | primary | yes | `uv run python -m xninetzy.cli.supervisor start` |
| Streamable HTTP | secondary, loopback | opt-in | `XNINETZY_MCP_TRANSPORT=streamable-http` |
| Legacy HTTP+SSE | n/a | n/a | not used |
| REST / GraphQL | n/a | n/a | MCP-only |

Streamable HTTP defaults:

- `XNINETZY_MCP_HTTP_HOST=127.0.0.1`
- `XNINETZY_MCP_HTTP_PORT=8765`
- `XNINETZY_MCP_HTTP_PATH=/mcp`
- `stateless_http=True`, `json_response=True`

Non-loopback binding triggers a stderr WARNING advising OAuth 2.1 +
Resource Indicators (RFC 8707) + Client ID Metadata Documents before
real use.

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

Verify from outside the repo:

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

See [MCP system reference](apps/docs/src/pages/docs/mcp-system.md) for
the canonical tool registry and authorization model.

## Repository layout

```text
.
├── .env.example                         # template (no secrets)
├── AGENTS.md                            # project governance
├── CLAUDE.md                            # Claude Code entry point
├── README.md                            # this file
├── pyproject.toml                       # mcp>=1.28.1,<2 ; package=false
├── docs/                                # cross-service design + plans
├── scripts/
│   ├── install-mcp.sh                   # Linux/macOS one-line installer
│   ├── install-mcp.ps1                  # Windows PowerShell installer
│   ├── mcp_audit.py                     # live registry audit
│   ├── verify_cpu_only.py               # CPU-only runtime guard
│   ├── install_skills.py                # skill catalog sync
│   ├── xninetzy_backup.py               # backup / restore
│   └── configure_internal_auth.py       # AI_API_KEY bootstrap
├── apps/
│   └── docs/                            # Astro Starlight documentation
├── xninetzy/                            # canonical MCP package
│   ├── cli/supervisor.py                # init / start / release-check
│   ├── interfaces/
│   │   ├── mcp_server.py                # FastMCP("xninetzy", ...)
│   │   ├── mcp_runtime.py
│   │   ├── mcp_tool_adapter.py
│   │   ├── external_mcp.py              # gateway + allowlist
│   │   ├── tasks_extension.py           # SEP-2663
│   │   └── api/                         # FastAPI HTTP bridge (secondary)
│   ├── tools/
│   │   ├── registry.py                  # get_all_tools() — 343 tools
│   │   ├── manifest.py                  # risk + feature_pack + idempotency
│   │   └── release_check.py             # 6 release-gate checks
│   ├── os/
│   │   ├── academic/hebat/              # HEBAT/Moodle (Playwright)
│   │   ├── academic/mahasiswa_portal/   # Cyber Campus + KRS War
│   │   ├── academic/qa_portal/          # QA Kuesioner (FINAL)
│   │   ├── inbox/                       # capture / triage / today
│   │   ├── knowledge/                   # FAISS + retrieval
│   │   ├── lightning/                   # 15 bandit tools
│   │   ├── notes/                       # Obsidian vault
│   │   ├── policy/                      # action policy + risk class
│   │   ├── reminders/
│   │   ├── research/sources/            # 30 source adapters
│   │   ├── security/captcha/lockout.py
│   │   └── ...
│   ├── observability/trace.py           # SEP-414 W3C trace context
│   ├── skills/                          # runtime skill tools
│   └── ...
├── .agents/skills/                      # 68 skill bodies
└── tests/                               # 828 pass / 29 fail / 7 blocked
```

## Run for development

The MCP server is the only long-running process. Everything else is
either a one-shot script, an MCP call, or the host doing reasoning.

```bash
uv sync --all-extras
uv run python -m xninetzy.cli.supervisor start      # stdio
# or
XNINETZY_MCP_TRANSPORT=streamable-http \
  uv run python -m xninetzy.interfaces.mcp_server    # http://127.0.0.1:8765/mcp
```

Run the release gate:

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Expected output:

```text
  [PASS   ] tool_registry            343 tools classified
  [PASS   ] secret_redaction         3/3 sample secrets redacted
  [PASS   ] safe_fetch               3/3 SSRF guard scenarios blocked
  [PASS   ] transport_config         transport=stdio host=127.0.0.1
  [PASS   ] sdk_pin                  mcp resolved=1.28.1
  [PASS   ] canonical_final_tools    3 FINAL tools match canonical set
overall: PASS
```

## HTTP bridge (secondary)

MCP is the primary public interface. The FastAPI HTTP surface in
`xninetzy/interfaces/api/` exists for hosts that cannot speak stdio,
for ops (`/health`, `/api/reminders`, debug routes), and for the
optional `/api/chat` HTTP MCP bridge.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | public health check |
| `POST` | `/api/chat` | HTTP MCP bridge (single-tool dispatch) |
| `POST` | `/api/chat/stream` | streaming sibling of `/api/chat` |
| `GET` | `/api/reminders` | list reminders |
| `POST` | `/api/reminders` | create reminder |
| `POST` | `/api/reminders/{id}/cancel` | cancel |
| `POST` | `/api/reminders/{id}/close` | close |
| `POST` | `/api/reminders/scheduler/tick` | manual scheduler tick |
| `GET` | `/api/debug/tools` | list registry (debug only) |
| `POST` | `/api/debug/invoke-tool/{tool}` | invoke tool (debug only) |

Auth via `Authorization: Bearer <AI_API_KEY>`. Bind to `127.0.0.1`.

## Data and persistence

| Data | Host path |
|---|---|
| SQLite, FAISS, HEBAT, web analysis | `~/.local/share/xninetzy` |
| Obsidian vault | `OBSIDIAN_VAULT_HOST_PATH` (default `~/Documents/xninetzy-vault`) |
| AI-generated artifacts | `~/Documents/xninetzy/output` |
| HEBAT downloads | `~/Documents` |
| External MCP registry | `EXTERNAL_MCP_REGISTRY_PATH` |

`ARTIFACT_ALLOWLIST=true` (default) rejects writes outside the four
`*_DIR` roots. See [Local data per installation](apps/docs/src/pages/docs/local-data.md).

### Backup and restore

```bash
uv run --no-project python scripts/xninetzy_backup.py create
uv run --no-project python scripts/xninetzy_backup.py list
uv run --no-project python scripts/xninetzy_backup.py verify <backup-name>
```

Backups include SQLite + FAISS with SHA-256 manifest; never include
secrets, sessions, downloads, or the vault. See
[Backup and restore](apps/docs/src/pages/docs/backup-restore.md).

## Testing

```bash
uv sync --all-extras
uv run pytest -ra
uv run ruff check xninetzy tests
uv run --no-project python scripts/verify_cpu_only.py
cd apps/docs && yarn check && yarn build
uv run --no-project python scripts/install_skills.py --dry-run
```

Current baseline: **828 pass / 29 fail / 7 collection-blocked** (see
`tests/baseline/REPORT.md`).

## Troubleshooting

- Run `uv run python -m xninetzy.cli.supervisor release-check` first;
  it covers `tool_registry`, `secret_redaction`, `safe_fetch`,
  `transport_config`, `sdk_pin`, and `canonical_final_tools`.
- For MCP host issues, verify from `/tmp`:
  `codex mcp get xninetzy`, `claude mcp list`, `opencode mcp list`.
- For CAPTCHA failures, check
  `XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD` /
  `XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS` — auto-OCR disables
  itself after threshold failures within the window.
- For Obsidian, confirm `OBSIDIAN_VAULT_HOST_PATH` is absolute,
  `OBSIDIAN_ALLOW_WRITE=true`, and the note path is vault-relative.
- For HEBAT, use `hebat_login_status_verbose` and
  `hebat_debug_login` MCP tools.

### Skill repair

If `tests/governance/test_skill_frontmatter.py::test_skill_catalog_yaml_parses`
xfails (currently all 69 built-in skill SKILL.md files have broken YAML
frontmatter), see [`docs/runbooks/skill-repair.md`](docs/runbooks/skill-repair.md).
The repair tool is `scripts/repair_skill_yaml.py`; run it **outside**
Claude Code (the in-session auto-linter hook re-damages YAML on every
write to `.agents/skills/*/SKILL.md`). Track via
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) ISS-20260919-01.

See [Troubleshooting](apps/docs/src/pages/docs/troubleshooting.md) for
the full list.

## Security

Threat model is aligned to NSA Cybersecurity Sheet
**U/OO/6030316-26** (Model Context Protocol: Security Design
Considerations for AI-Driven Automation) and the 2026-07-28 MCP
specification.

- stdio = OS process boundary is the trust boundary (no network auth).
- Streamable HTTP bound to loopback by default. Non-loopback requires
  OAuth 2.1 + Resource Indicators (RFC 8707) + Client ID Metadata
  Documents before real use.
- FINAL-class tools always require HITL approval server-side. The CLI
  orchestrator enforces `_effective_tier = max(declared, manifest_tier)`
  so an owner-supplied tier downgrade is rejected.
- External MCP servers are untrusted by default. Each server requires
  `risk_level` + `allowed_tools` allowlist + `last_reviewed_at`.
- `safe_fetch` rejects non-http(s) schemes, private/loopback hosts, and
  oversized responses. `redact_secrets` strips OpenAI, Anthropic, GitHub,
  Google, AWS, and PEM key patterns from any logged text.

Full mapping in `/SECURITY.md`.

## Documentation map

| Document | Topic |
|---|---|
| [MCP system reference](apps/docs/src/pages/docs/mcp-system.md) | transports, registry, FINAL tools, gateway, tasks, trace, paths |
| [Quick start](apps/docs/src/pages/docs/getting-started.md) | install + connect an MCP host |
| [Architecture](apps/docs/src/pages/docs/architecture.md) | services, request flow, transports, persistence |
| [Configuration](apps/docs/src/pages/docs/configuration.md) | every env var explained |
| [Security](apps/docs/src/pages/docs/security.md) | hardening checklist, network boundary, identity |
| [Global MCP](apps/docs/src/pages/docs/mcp.md) | Codex / Claude Code / OpenCode wiring |
| [Obsidian](apps/docs/src/pages/docs/obsidian.md) | vault management |
| [HEBAT / Moodle](apps/docs/src/pages/docs/hebat.md) | academic workflow |
| [Cyber Campus](apps/docs/src/pages/docs/cyber-campus.md) | portal tools, grade tokens, KRS War |
| [OS kernel](apps/docs/src/pages/docs/os-kernel.md) | capture, triage, attention queue |
| [Learning roadmaps](apps/docs/src/pages/docs/learning-roadmaps.md) | adaptive planning, recall, mastery |
| [Lightning](apps/docs/src/pages/docs/lightning.md) | rewards, strategy ranking, regression |
| [Skills](apps/docs/src/pages/docs/skills.md) | 68 skill bodies + open-source catalog |
| [Action policy](apps/docs/src/pages/docs/action-policy.md) | auto/approval/manual/final gates |
| [HTTP API](apps/docs/src/pages/docs/api.md) | FastAPI surface |
| [Local data](apps/docs/src/pages/docs/local-data.md) | per-installation persistence |
| [Backup & restore](apps/docs/src/pages/docs/backup-restore.md) | snapshots, verification, retention |
| [Testing](apps/docs/src/pages/docs/testing.md) | test suites and quality gates |
| [Automation](apps/docs/src/pages/docs/automation.md) | briefings, reviews, leases, freshness |
| [Troubleshooting](apps/docs/src/pages/docs/troubleshooting.md) | diagnose common problems |
| [Chat model selection](apps/docs/src/pages/docs/providers.md) | host supplies the model |

## License

Xninetzy is distributed under the
[Xninetzy Source-Available License v2.2.0](./LICENSE)
(`SPDX-License-Identifier: LicenseRef-Xninetzy-Source-Available-2.2.0`).

- **Personal Use** — read, build, run, fork, and contribute back at no
  charge.
- **Commercial Use** — requires a separate written agreement with the
  Licensee. Open an issue titled `commercial-license` on the upstream
  repository to start the conversation.
- **Trademarks** — "Xninetzy" and "Xninetzy Labs" are not licensed under
  this grant; use them only for factual references and the NOTICE file.
- **Third-party components** — retain their original licenses; see
  Section 11 of the LICENSE file for the non-exhaustive list.

This is a source-available license, not an OSI-approved open-source
license. Not a substitute for the Apache License, MIT, or any other
OSI-approved license.
