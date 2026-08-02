---
layout: ../../layouts/DocsLayout.astro
title: HTTP API
description: AI service and WhatsApp engine endpoints, chat payloads, reminders, health checks, debugging, and authentication boundaries.
section: Operations
---

The AI service listens on `http://127.0.0.1:8000` by default. The WhatsApp
engine listens on `http://127.0.0.1:8081`.

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
    "message": "explain classification and clustering",
    "chat_type": "private",
    "metadata": {}
  }'
```

Identity fields affect memory, preferences, administrator guards, and chat
history. In single-owner mode, `sender_id` must match `ADMIN_JID` or
`OWNER_ALLOWED_JIDS`. The bearer key authenticates the service caller, while
the sender ID determines owner scope. Never forward administrator identity from
untrusted user input.

## Reminder API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/reminders` | List reminders |
| `POST` | `/api/reminders` | Create a reminder |
| `POST` | `/api/reminders/{id}/cancel` | Cancel a reminder |
| `POST` | `/api/reminders/{id}/close` | Close a reminder |

Send `Authorization: Bearer <AI_API_KEY>` with every reminder request.

## Debug API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/debug/tools` | List the tool registry |
| `POST` | `/api/debug/invoke-tool/{tool}` | Invoke a development tool |

Disable debug endpoints on a real installation:

```dotenv
AGENT_DEBUG_ENDPOINTS=false
```

## WhatsApp health and tools

```bash
curl -s http://127.0.0.1:8081/health
```

Check `socket_ready` before sending a WhatsApp action.

List tools:

```bash
curl -H 'Authorization: Bearer <MCP_API_KEY>' \
  http://127.0.0.1:8081/mcp/tools
```

Invoke a tool:

```bash
curl -X POST http://127.0.0.1:8081/mcp/call \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <MCP_API_KEY>' \
  -d '{
    "tool": "send_text_message",
    "input": {
      "jid": "628xxxxxxxxxx@s.whatsapp.net",
      "text": "Hello from Xninetzy"
    }
  }'
```

## Authentication boundary

`AI_API_KEY` protects `/api/chat`, reminder routes, and debug routes. When
`AI_API_AUTH_REQUIRED=true` but the server key is empty, protected endpoints
return `503`; a missing or invalid caller key returns `401`.

Keep these controls in place:

- bind to `127.0.0.1` or a private network;
- never forward port `8000` directly to the internet;
- disable debug endpoints;
- use firewall or reverse-proxy authentication for cross-host access;
- use different shared secrets for the AI API and WhatsApp tool server.

## Error handling

Use HTTP status codes to distinguish failures:

- `4xx`: payload, authentication, allowlist, or permission failure;
- `5xx`: dependency, provider, database, or unexpected exception;
- health is OK but chat fails: inspect provider and tool logs;
- AI is OK but WhatsApp fails: inspect socket state and the shared key.

Do not log request headers or complete media payloads in production because they
may contain credentials and personal data.
