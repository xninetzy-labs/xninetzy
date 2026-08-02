---
layout: ../../layouts/DocsLayout.astro
title: Quick start
description: Install Xninetzy on Linux, macOS, or Windows and reach the first WhatsApp conversation.
section: Start
---

The Docker path runs the AI service and WhatsApp engine on one Compose bridge
network. Ports are published only to host loopback, so the same configuration
works on Linux, macOS, Windows, and WSL2.

## Prerequisites

- Linux: Docker Engine and the Docker Compose plugin.
- macOS: Docker Desktop.
- Windows 10 or 11: Docker Desktop with the WSL2 backend, or PowerShell 7.
- Git. The Unix installer also requires OpenSSL.
- A Flaz API key or credentials for another supported LLM provider.
- An absolute path to an Obsidian vault.
- A WhatsApp account that can link a new device.

For host development, also install Python 3.11+, `uv`, Node.js 22.12+, Yarn
1.22, Playwright Chromium, and Tesseract for OCR.

## One-command installation

Linux, macOS, or WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/misbahul45/xninetzy/main/scripts/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/misbahul45/xninetzy/main/scripts/install.ps1 | iex
```

The installer clones the repository or uses the active checkout, creates
`.env`, asks for the vault path, WhatsApp administrator number, and Flaz API
key, generates independent internal keys, validates Compose, builds the images,
and starts the services. Secret input is not echoed or printed. Follow the
WhatsApp engine logs to scan the QR code.

Audit any remote install script before using a pipe-to-shell command. The manual
path below produces the same result.

## Platform support

| Platform | Runtime | Automatic startup |
|---|---|---|
| Linux | Docker Engine and Compose | Enable Docker through systemd |
| macOS | Docker Desktop | Enable “Start Docker Desktop when you sign in” |
| Windows | Docker Desktop and WSL2 | Enable “Start Docker Desktop when you sign in” |
| WSL2 | Docker Desktop integration | Follows Windows Docker Desktop startup |

Use an absolute native-platform vault path. Do not use a network path that has
not been shared with Docker Desktop.

## 1. Prepare the environment manually

From the repository root:

```bash
cp .env.example .env
chmod 600 .env
```

Never place a real password, token, cookie, or API key in `.env.example`.

## 2. Add the Flaz API key safely

```bash
cd services/ai
uv run python scripts/configure_flaz.py
cd ../..
```

The script uses `getpass`, writes `.env` atomically, preserves mode `600`,
and never echoes the key.

Default provider settings:

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
```

Generate internal service authentication without printing secrets:

```bash
cd services/ai
uv run python scripts/configure_internal_auth.py
cd ../..
```

## 3. Connect host data

Find the host user identity:

```bash
id -u
id -g
```

Set these values in `.env`:

```dotenv
HOST_UID=1000
HOST_GID=1000
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/obsidian-vault
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
ADMIN_NAMES=your_name
APP_TIMEZONE=Asia/Jakarta
WA_STARTUP_MENU_ENABLED=true
WA_STARTUP_MENU_DELAY_MS=1500
```

`OBSIDIAN_VAULT_HOST_PATH` must be absolute. Compose rejects an empty value.

## 4. Choose WhatsApp login

QR mode:

```dotenv
WA_LOGIN_MODE=qr
```

Pairing-code mode:

```dotenv
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Use the country code without `+`, spaces, or punctuation.

## 5. Start services

```bash
docker compose config -q
docker compose up --build -d ai wa-enggine
docker compose ps
docker compose logs -f wa-enggine
```

Complete QR or pairing through **WhatsApp → Linked devices**.

After the first `open` connection, the administrator receives five menu cards
with 15 command buttons. The menu is sent once per process launch, not after
every reconnect. A text fallback is sent when interactive buttons are not
supported.

## Automatic startup after boot or login

On Linux with systemd:

```bash
sudo systemctl enable --now docker
systemctl is-enabled docker
systemctl is-active docker
```

Compose uses `restart: unless-stopped` for the AI and WhatsApp services. Once
created, the containers return with Docker after reboot. Avoid
`docker compose down` when containers must remain registered for automatic
startup.

On macOS and Windows, enable Docker Desktop startup under Settings → General.
On WSL2, verify distribution integration. Docker Desktop restores the
containers with the same restart policy.

## 6. Verify health

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8081/health
```

The AI service should return:

```json
{"status":"ok","service":"xninetzy-ai"}
```

WhatsApp health reports socket and connection state.

## 7. Try WhatsApp

```text
/helper
create a 14-day machine-learning roadmap
remind me tomorrow at 08:00 to review my assignment
save this conversation summary to Obsidian
```

## Host development

AI service:

```bash
cd services/ai
uv sync
uv run playwright install chromium
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

WhatsApp engine in a second terminal:

```bash
cd services/wa-enggine
yarn install --frozen-lockfile
yarn dev
```

Never run Docker and host instances on the same ports or WhatsApp account at the
same time.
