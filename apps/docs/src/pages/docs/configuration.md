---
layout: ../../layouts/DocsLayout.astro
title: Konfigurasi environment
description: Peta konfigurasi service, provider, persistence, dan guard yang aman untuk instalasi baru.
section: Mulai
---

Root `.env.example` adalah kontrak konfigurasi seluruh monorepo. Salin menjadi `.env`; jangan mengubah template dengan nilai rahasia.

## Konfigurasi inti

```dotenv
APP_ENV=development
APP_TIMEZONE=Asia/Jakarta
LOG_LEVEL=INFO
HOST_UID=1000
HOST_GID=1000
```

Gunakan UID/GID pemilik repository dan vault. Ini mencegah file Docker dimiliki root.

## AI dan provider

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

`*_MODELS` adalah allowlist model yang dipisahkan koma. Lihat [Provider LLM](/docs/providers/) untuk konfigurasi multi-provider.

## WhatsApp

```dotenv
AI_API_URL=http://127.0.0.1:8000
WA_LOGIN_MODE=qr
WA_PHONE_NUMBER=
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

Untuk local development, path session/media harus absolute dan menunjuk lokasi yang sama bagi kedua service:

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
```

`OBSIDIAN_VAULT_HOST_PATH` dipakai Docker host. `OBSIDIAN_VAULT_PATH` adalah mount path di container.

## HEBAT / Moodle

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

Credential hanya boleh berada di `.env` lokal. Session browser dan file download diabaikan Git.

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

`MCP_API_KEY` dan `WA_MCP_API_KEY` harus sama. `AI_API_KEY` wajib dikirim oleh WA
engine dan CLI ke chat, reminder, dan debug API. Buat key acak, misalnya dengan
`openssl rand -hex 32`; jangan menggunakan password akun atau API key provider.

`ADMIN_JID` adalah identitas owner utama. `OWNER_ALLOWED_JIDS` hanya untuk alias
owner yang memang diperlukan, misalnya JID `@lid`; pisahkan dengan koma.

## Replay safety dan backup

```dotenv
WA_PROCESSING_DIR=/app/data/wa-processing
WA_MESSAGE_LEASE_MS=120000
WA_MESSAGE_RETRY_DELAY_MS=30000
WA_MESSAGE_RETENTION=10000
BACKUP_DIR=/app/data/backups
BACKUP_RETENTION=14
```

WA engine menyimpan claim dan reply outbox agar pengiriman ulang event tidak
menjalankan LLM/tool yang sama. Direktori ini harus persisten dan hanya dapat
dibaca owner. Lihat [Backup dan restore](/docs/backup-restore/) untuk recovery.

## MCP runtime path

Saat server MCP berjalan di host, path container perlu dipetakan ke data host:

```dotenv
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

Mode `auto` meng-resolve layout repository standar. Isi override hanya jika data berada di tempat lain.

## Coding runtime

```dotenv
CODING_AGENT_ENABLED=false
CODING_AGENT_DEFAULT=codex
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_WORKSPACE=/absolute/path/to/workspace
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/workspace
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_SANDBOX=workspace-write
```

Aktifkan hanya jika service berjalan pada host yang memiliki binary dan session login CLI.

## Validasi

```bash
docker compose config -q
cd services/ai && uv run python -c "from app.xninetzy.core.config import get_settings; print(get_settings().app_env)"
```

Jangan mencetak object settings lengkap karena dapat memuat secret.
