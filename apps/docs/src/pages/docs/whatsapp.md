---
layout: ../../layouts/DocsLayout.astro
title: WhatsApp integration
description: Login, chat triggers, slash commands, documents, images, OCR, and internal WhatsApp tools.
section: Integrations
---

The WhatsApp engine uses Baileys for a linked-device session. Messages that pass
trigger policy become structured payloads for the AI service.

## Login

QR mode:

```dotenv
WA_LOGIN_MODE=qr
```

Pairing-code mode:

```dotenv
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Monitor the process:

```bash
docker compose logs -f wa-enggine
```

Docker stores the session in the `wa-session` volume. Host mode uses
`WA_AUTH_DIR`.

## Administrator startup menu

On the first `open` connection of each process launch, the engine sends five
cards to `ADMIN_JID`. Each card has at most three Baileys buttons.

| Card | Buttons |
|---|---|
| Daily | `/today`, `/inbox`, `/review` |
| Life OS | `/tasks`, `/goals`, `/workout` |
| Learning OS | `/hebat`, `/roadmaps`, `/study-today` |
| Knowledge | `/memory`, `/skills`, `/helper knowledge` |
| AI control | `/approvals`, `/llm`, `/agent` |

```dotenv
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
WA_STARTUP_MENU_ENABLED=true
WA_STARTUP_MENU_DELAY_MS=1500
```

“Once per launch” state lives in the WhatsApp process. Reconnects do not send a
second menu; restarting the container begins a new launch. If interactive
buttons fail, the engine sends one text fallback containing all commands.
`ADMIN_JID` can be a number or complete JID and is normalized before delivery.

## Private and group triggers

Private chats are processed directly. A group message is processed when the bot
is mentioned, the message uses the configured prefix, it replies to a bot
message, or `WA_GROUP_ALLOW_ALL=true`.

Safe defaults:

```dotenv
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

## Important commands

| Command | Purpose |
|---|---|
| `/helper [topic]` | Capability guide |
| `/today` | OS attention queue |
| `/capture`, `/inbox`, `/triage` | Cross-interface capture and triage |
| `/tasks`, `/goals` | Life OS |
| `/research`, `/deep-research` | Research |
| `/roadmaps`, `/study-today` | Learning OS |
| `/media-info`, `/analyze-media` | Attachment and reply inspection |
| `/approvals`, `/approve`, `/reject` | Human approval |
| `/llm list`, `/llm use` | Provider and model |
| `/agent list`, `/agent use`, `/code` | Coding runtime |

## Documents and images

Send or reply to a PDF, DOCX, TXT, CSV, JSON, spreadsheet, presentation, or
image:

```text
summarize this document
create action items from the file I replied to
read the text in this image and save it to Obsidian
ingest this PDF and answer from its evidence
```

Media processing is:

1. the WhatsApp engine downloads the attachment to shared durable storage;
2. the payload carries metadata and a resolved path;
3. the AI validates checksum, MIME type, extension, and size;
4. native text is extracted first;
5. images and scanned PDFs use Tesseract OCR as a fallback;
6. extracted content can reach an agent, knowledge ingestion, or Obsidian tools.

If a replied attachment is unavailable, run `/media-info` and verify both
services resolve the same `WA_MEDIA_DIR`.

## HTTP MCP-style tools

List WhatsApp tools:

```bash
curl -H 'Authorization: Bearer <MCP_API_KEY>' \
  http://127.0.0.1:8081/mcp/tools
```

Invoke a tool:

```bash
curl -X POST http://127.0.0.1:8081/mcp/call \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <MCP_API_KEY>' \
  -d '{"tool":"send_text_message","input":{"jid":"628xxxxxxxxxx@s.whatsapp.net","text":"Hello"}}'
```

Set `MCP_API_KEY` in the WhatsApp engine and the same value as
`WA_MCP_API_KEY` in the AI service.

> Baileys is not the official WhatsApp Business API. Protocol or policy changes can affect connectivity.
