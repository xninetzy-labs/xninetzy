---
layout: ../../layouts/DocsLayout.astro
title: Environment configuration
description: Service, provider, persistence, and safety settings for a secure installation.
section: Start
---

The root `.env.example` is the configuration contract for the entire
project. Copy it to `.env`; never place real secrets in the template.

Every installation uses its own local SQLite database. Runtime databases
are not stored in the repository. Startup creates or migrates the
database at `SQLITE_PATH`; see [Local data per installation](/docs/local-data/).

## Core settings

```dotenv
APP_ENV=development
APP_TIMEZONE=Asia/Jakarta
LOG_LEVEL=INFO
```

## FastAPI HTTP surface (secondary)

MCP is the primary public interface. The FastAPI HTTP surface
(`/health`, `/api/reminders/*`, debug routes) is optional and intended
for the same owner process that hosts the MCP server.

```dotenv
AI_API_URL=http://127.0.0.1:8000
AI_API_KEY=generate-a-long-random-secret
AI_API_AUTH_REQUIRED=true
AGENT_DEBUG_ENDPOINTS=false
```

`AI_API_KEY` must be sent as a bearer token on every API request when
`AI_API_AUTH_REQUIRED=true`. The health endpoint stays public.

## MCP server

```dotenv
XNINETZY_MCP_TRANSPORT=stdio
XNINETZY_MCP_HTTP_HOST=127.0.0.1
XNINETZY_MCP_HTTP_PORT=8765
XNINETZY_MCP_HTTP_PATH=/mcp
XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS=20
XNINETZY_MCP_CALL_TIMEOUT_SECONDS=180
```

`XNINETZY_MCP_TRANSPORT=streamable-http` enables the HTTP surface. The
server is configured `stateless_http=True` + `json_response=True`
(recommended for production per the 2026-07-28 spec direction). Non-loopback
binding logs a warning to stderr; OAuth 2.1 + Resource Indicators +
Client ID Metadata Documents are required before exposing it.

## LLM providers

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

Each `*_MODELS` value is a comma-separated model allowlist. See
[Providers](/docs/providers/) for multi-provider configuration.

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

`OBSIDIAN_VAULT_HOST_PATH` is the host path (used outside Docker).
`OBSIDIAN_VAULT_PATH` is the corresponding container path (used inside
Docker). Both paths must point to the same vault.

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

Credentials belong only in the local `.env`. Browser sessions and
downloaded files are ignored by Git.

## Single-owner mode

```dotenv
SINGLE_OWNER_MODE=true
ADMIN_JID=
OWNER_ALLOWED_JIDS=
```

`ADMIN_JID` is the owner's normalized phone JID. Tools that check
`is_owner_admin` (in `xninetzy/os/research/permissions.py`) accept the
admin principal by default. The MCP server injects the admin principal at
startup, so client-supplied `sender_id` values are not authorization
evidence on their own.

## CAPTCHA auto-OCR (opt-in)

```dotenv
XNINETZY_CAPTCHA_OCR_ENABLED=false
XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE=0.6
XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD=3
XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS=600
XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS=3600
```

Default is `false`. When `true`, the lockout guard
(`xninetzy/os/security/captcha/lockout.py`) auto-disables OCR after the
configured threshold of failures within the window. Owner manual
delivery remains the fallback.

## External MCP integration

```dotenv
EXTERNAL_MCP_ENABLED=false
EXTERNAL_MCP_ALLOW_CALLS=false
EXTERNAL_MCP_REGISTRY_PATH=/absolute/path/to/external_mcp.json
EXTERNAL_MCP_MAX_SERVERS=8
```

Default is `false`. When enabled, each server requires `risk_level` and an
explicit `allowed_tools` allowlist before any tool call is permitted. See
[Global MCP](/docs/mcp/) for the gateway model.

## Coding runtimes

```dotenv
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/single-workspace
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_REQUIRE_XNINETZY_MCP=true
```

Never mount a home directory, SSH keys, cloud credentials, or the Docker
socket into the service without a specific need and threat review.

## Secrets rotation

Generate keys with `openssl rand -hex 32`; never reuse an account password
or provider API key. When a key is rotated, restart the MCP server process
to pick up the new value.
