---
layout: ../../layouts/DocsLayout.astro
title: HTTP API
description: Endpoint AI service dan WA engine, payload chat, reminder, health, debug, serta authentication boundary.
section: Operasional
---

AI service default berada di `http://127.0.0.1:8000`. WA engine default berada di `http://127.0.0.1:8081`.

## AI health

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{"status":"ok","service":"xninetzy-ai"}
```

## Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <AI_API_KEY>' \
  -d '{
    "chat_id": "628xxxxxxxxxx@s.whatsapp.net",
    "sender_id": "628xxxxxxxxxx@s.whatsapp.net",
    "sender_name": "Owner",
    "message": "jelaskan classification dan clustering",
    "chat_type": "private",
    "metadata": {}
  }'
```

Field identitas memengaruhi memory, preference, admin guard, dan chat history.
Dalam single-owner mode, `sender_id` harus cocok dengan `ADMIN_JID` atau
`OWNER_ALLOWED_JIDS`. Bearer key mengautentikasi service caller; sender ID
menentukan owner scope. Jangan meneruskan identitas admin dari input user.

## Reminder API

| Method | Endpoint | Fungsi |
|---|---|---|
| `GET` | `/api/reminders` | list reminder |
| `POST` | `/api/reminders` | membuat reminder |
| `POST` | `/api/reminders/{id}/cancel` | membatalkan |
| `POST` | `/api/reminders/{id}/close` | menutup |

Kirim `Authorization: Bearer <AI_API_KEY>` pada semua request reminder.

## Debug API

| Method | Endpoint | Fungsi |
|---|---|---|
| `GET` | `/api/debug/tools` | daftar tool registry |
| `POST` | `/api/debug/invoke-tool/{tool}` | invoke tool development |

Nonaktifkan pada instalasi nyata:

```dotenv
AGENT_DEBUG_ENDPOINTS=false
```

## WA health

```bash
curl -s http://127.0.0.1:8081/health
```

Periksa `socket_ready` sebelum mengirim aksi WhatsApp.

## WA tools

List tools:

```bash
curl -H 'Authorization: Bearer <MCP_API_KEY>' \
  http://127.0.0.1:8081/mcp/tools
```

Invoke:

```bash
curl -X POST http://127.0.0.1:8081/mcp/call \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <MCP_API_KEY>' \
  -d '{
    "tool": "send_text_message",
    "input": {
      "jid": "628xxxxxxxxxx@s.whatsapp.net",
      "text": "Halo dari Xninetzy"
    }
  }'
```

## Authentication boundary

`AI_API_KEY` melindungi `/api/chat`, reminder, dan debug routes. Jika
`AI_API_AUTH_REQUIRED=true` tetapi key server kosong, endpoint terlindungi
merespons `503`; key hilang atau salah menghasilkan `401`.

Tetap lakukan hal berikut:

- bind ke `127.0.0.1` atau private network;
- jangan port-forward `8000` ke internet;
- matikan debug endpoints;
- gunakan firewall/reverse proxy authentication jika akses lintas host diperlukan;
- gunakan shared secret berbeda untuk AI API dan WA tool server.

## Error handling

Gunakan status HTTP untuk membedakan:

- `4xx`: payload, auth, allowlist, atau permission;
- `5xx`: dependency, provider, database, atau unexpected exception;
- health OK tetapi chat gagal: periksa provider/tool log;
- AI OK tetapi WA gagal: periksa socket dan shared key.

Jangan log request headers atau full payload media pada production karena dapat memuat credential dan data personal.
