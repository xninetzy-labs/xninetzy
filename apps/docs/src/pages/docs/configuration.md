---
layout: ../../layouts/DocsLayout.astro
title: Environment configuration
description: Service, provider, persistence, and safety settings for a secure installation.
section: Start
---

The root `.env.example` is the configuration contract for the entire
monorepo. Copy it to `.env`; never place real secrets in the template.

Every clone uses a different local SQLite database. Runtime databases are not
stored in the repository. Startup creates or migrates the database at
`SQLITE_PATH`; see [Local data per installation](/docs/local-data/).

## Core settings

```dotenv
APP_ENV=development
APP_TIMEZONE=Asia/Jakarta
LOG_LEVEL=INFO
HOST_UID=1000
HOST_GID=1000
```

Use the UID and GID of the repository and vault owner so Docker-created files
are not owned by root.

## AI and providers

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

Each `*_MODELS` value is a comma-separated model allowlist. See
[LLM providers](/docs/providers/) for multi-provider configuration.

## WhatsApp

```dotenv
AI_API_URL=http://127.0.0.1:8000
WA_LOGIN_MODE=qr
WA_PHONE_NUMBER=
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

For local development, session and media paths must be absolute and resolve to
the same locations for both services:

```dotenv
WA_AUTH_DIR=/absolute/path/to/xninetzy/services/wa-enggine/sessions
WA_MEDIA_DIR=/absolute/path/to/xninetzy/services/ai/data/wa-media
```

## Obsidian

```dotenv
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/vault
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
OBSIDIAN_FOLDERING_ENABLED=true
OBSIDIAN_CANONICAL_SCHEMA_VERSION=1
OBSIDIAN_ORGANIZE_MODE=hybrid
OBSIDIAN_REQUIRE_ORGANIZE_APPROVAL=true
OBSIDIAN_AUTO_REFRESH_MOC=true
OBSIDIAN_PERSIST_ACADEMIC_SENSITIVE=false
OBSIDIAN_LEGACY_PATH_COMPATIBILITY=true
```

`OBSIDIAN_VAULT_HOST_PATH` is the host path mounted by Docker.
`OBSIDIAN_VAULT_PATH` is the corresponding container path.

## HEBAT and Moodle

```dotenv
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
HEBAT_BROWSER_HEADLESS=true
HEBAT_AUTO_LOGIN=false
HEBAT_REQUIRE_CONFIRMATION=true
HEBAT_ALLOW_AUTO_SUBMIT=false
```

Credentials belong only in the local `.env`. Browser sessions and downloaded
files are ignored by Git.

## Internal service authentication

```dotenv
MCP_API_KEY=generate-a-long-random-secret
WA_MCP_API_KEY=generate-the-same-secret
AI_API_KEY=another-long-random-secret
AI_API_AUTH_REQUIRED=true
AGENT_DEBUG_ENDPOINTS=false
SINGLE_OWNER_MODE=true
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
OWNER_ALLOWED_JIDS=
```

`MCP_API_KEY` and `WA_MCP_API_KEY` must match. The WhatsApp engine and CLI
must send `AI_API_KEY` to chat, reminder, and debug APIs. Generate independent
keys with a command such as `openssl rand -hex 32`; never reuse an account
password or provider API key.

For a local installation, run this command from `services/ai`:

```bash
uv run python scripts/configure_internal_auth.py
```

The script adds missing configuration, generates cryptographically secure
internal keys, never prints secrets, and preserves populated values.

`ADMIN_JID` is the primary WhatsApp owner identity.
`OWNER_ALLOWED_JIDS` is for explicitly reviewed aliases such as an `@lid`
identity. Separate multiple aliases with commas.

## WhatsApp startup menu

```dotenv
WA_STARTUP_MENU_ENABLED=true
WA_STARTUP_MENU_DELAY_MS=1500
```

The target is always `ADMIN_JID`; the LLM cannot select it. The delay gives
the socket time to stabilize after an `open` connection. Setting the feature
to `false` does not affect approvals or other notifications.

The WhatsApp engine attempts to map a Baileys `@lid` identity to its phone JID.
If WhatsApp provides no mapping, add the reviewed owner alias explicitly to
`OWNER_ALLOWED_JIDS`.

## Cyber Campus and grade tokens

```dotenv
CYBER_CAMPUS_ENABLED=false
CYBER_CAMPUS_BASE_URL=https://mahasiswa.unair.ac.id
CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat
CYBER_CAMPUS_BROWSER_HEADLESS=true
CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS=180
CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS=3
CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS=180
CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS=3
CYBER_CAMPUS_ENTRY_YEAR=0
```

Cyber Campus reads `HEBAT_USERNAME` and `HEBAT_PASSWORD` in memory only
during login. Login CAPTCHA images are sent to the WhatsApp administrator and
must be answered manually. The owner can reply to the image, send one answer
while a challenge is active, or use `/captcha <id> <answer>`.

Grade tokens are accepted only from the WhatsApp administrator through a
short-lived challenge and are never persisted. `CYBER_CAMPUS_ENTRY_YEAR`
enables aliases such as `/nilai semester 1`. A value of `0` attempts to
derive the entry year from a UNAIR student identifier. The target semester is
resolved deterministically, but the portal dropdown is changed only after a
verified token arrives for the same challenge.

## Replay safety and backups

```dotenv
WA_PROCESSING_DIR=/app/data/wa-processing
WA_MESSAGE_LEASE_MS=120000
WA_MESSAGE_RETRY_DELAY_MS=30000
WA_MESSAGE_RETENTION=10000
BACKUP_DIR=/app/data/backups
BACKUP_RETENTION=14
```

The WhatsApp engine persists claims and a reply outbox so redelivery cannot run
the same LLM or tool action twice. This directory must be persistent and
owner-readable only. See [Backup and restore](/docs/backup-restore/).

## Scheduled Personal OS

```dotenv
OS_SCHEDULER_ENABLED=true
OS_SCHEDULER_STARTUP_DELAY_SECONDS=30
OS_NOTIFY_CHAT_ID=628xxxxxxxxxx@s.whatsapp.net
MORNING_BRIEFING_HOUR=7
EVENING_CHECKIN_HOUR=20
WEEKLY_REVIEW_WEEKDAY=6
WEEKLY_REVIEW_HOUR=20
HEBAT_PERIODIC_SYNC_ENABLED=false
```

See [Automation and scheduled jobs](/docs/automation/) for lease behavior,
at-most-once delivery boundaries, ambiguous state, and periodic HEBAT sync.

## MCP runtime paths

When the MCP server runs on the host, container paths must resolve to host data:

```dotenv
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

`auto` resolves the standard repository layout. Set overrides only when runtime
data lives elsewhere.

## Coding runtime

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=opencode
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_EXECUTION_MODE=host_bridge
CODING_AGENT_HOST_BRIDGE_URL=http://host.docker.internal:8765
CODING_AGENT_HOST_BRIDGE_TOKEN=
CODING_AGENT_HOST_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_HOST_ALLOWED_ROOT=/absolute/path/to/xninetzy
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_SANDBOX=workspace-write
```

`/code` never executes Codex, Claude Code, or OpenCode inside the AI
container. The AI service sends an authenticated task to the host bridge, which
runs the host CLI in an allowed workspace and returns bounded output to
WhatsApp. The host and container must share the bridge token, but the bridge
never forwards it to the coding subprocess.

Install and enable the Linux user service:

```bash
bash scripts/install_host_agent_bridge.sh
loginctl enable-linger "$USER"
systemctl --user status xninetzy-host-agent-bridge
curl -s http://127.0.0.1:8765/health
```

Run the bridge temporarily with:

```bash
bash scripts/run_host_agent_bridge.sh
```

The bridge performs MCP preflight on the host. If the selected CLI cannot reach
the `xninetzy` MCP server, the task fails closed. Select a runtime with
`/agent use codex`, `/agent use claude-code`, or
`/agent use opencode`, then invoke `/code ...`.

## GraphRAG and the Neo4j projection

```dotenv
GRAPHRAG_V3_ENABLED=false
NEO4J_ENABLED=false
NEO4J_AUTOSTART_ENABLED=true
NEO4J_AUTOSTART_COMMAND_TIMEOUT_SECONDS=8
NEO4J_AUTOSTART_READINESS_TIMEOUT_SECONDS=10
NEO4J_CONNECT_TIMEOUT_SECONDS=3
NEO4J_FAILURE_COOLDOWN_SECONDS=60
```

SQLite is canonical. Neo4j and FAISS are rebuildable projections and may be
offline. After an autostart failure, requests do not repeat Docker startup
during the cooldown and retrieval falls back to SQLite or FAISS. Enable
`NEO4J_ENABLED` only when the graph Compose profile is available.

The vault folder policy is shared by every interface. Preview Obsidian
organization before applying a legacy migration.

## Validation

```bash
docker compose config -q
cd services/ai && uv run python -c "from app.xninetzy.core.config import get_settings; print(get_settings().app_env)"
```

Never print the complete settings object because it may contain secrets.
