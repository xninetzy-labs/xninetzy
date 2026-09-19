---
layout: ../../layouts/DocsLayout.astro
title: HTTP API
description: FastAPI surface for health, /api/chat, /api/chat/stream, reminders, scheduler, and debug.
section: Operations
---

MCP is the primary public interface. The FastAPI HTTP surface in
`xninetzy/interfaces/api/` exists for hosts that cannot speak stdio,
for owner-facing ops (health, reminders, scheduler tick, debug), and
for the optional Streamable HTTP MCP transport. The FastAPI listener
defaults to `http://127.0.0.1:8000`.

There is no WhatsApp engine, no port-8081 service, no separate MCP
tool server. Channel-tagged requests (`metadata.channel="whatsapp"`)
still route through `authorize_owner` so the legacy owner allowlist
applies, but no Baileys runtime exists in v2.2.0 — clients should
prefer the MCP server for new work.

## Health

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{"status":"ok","service":"xninetzy-ai","ai_runtime":{...}}
```

## HTTP MCP bridge — `/api/chat` and `/api/chat/stream`

`POST /api/chat` is an HTTP MCP bridge for hosts that cannot run the
MCP stdio transport. It dispatches a `ChatRequest` to a single canonical
MCP tool. There is no server-side LangGraph agent loop; multi-turn
reasoning belongs to the host.

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <AI_API_KEY>' \
  -d '{
    "chat_id": "owner",
    "sender_id": "owner",
    "sender_name": "Owner",
    "message": "explain classification and clustering",
    "chat_type": "private",
    "metadata": {}
  }'
```

Identity fields affect memory, preferences, owner guards, and chat
history. In single-owner mode, `sender_id` must match `ADMIN_JID` or
`OWNER_ALLOWED_JIDS`. The bearer key authenticates the service caller;
the sender ID determines owner scope. Never forward owner identity
from untrusted user input.

`POST /api/chat/stream` is the streaming sibling used by clients that
want incremental responses. The route uses the same authorization and
the same MCP dispatch path.

## Reminder HTTP surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/reminders` | List reminders |
| `POST` | `/api/reminders` | Create a reminder |
| `POST` | `/api/reminders/{id}/cancel` | Cancel a reminder |
| `POST` | `/api/reminders/{id}/close` | Close a reminder |
| `POST` | `/api/reminders/scheduler/tick` | Manually trigger one scheduler tick |

Send `Authorization: Bearer <AI_API_KEY>` with every reminder request.
These endpoints wrap the same `reminder_*` MCP tools; prefer the MCP
tools when the host supports MCP.

## Debug API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/debug/tools` | List the tool registry |
| `POST` | `/api/debug/invoke-tool/{tool}` | Invoke a development tool |

Disable debug endpoints on a real installation:

```dotenv
AGENT_DEBUG_ENDPOINTS=false
```

Debug routes are intended for the owner on the local machine. They
are not part of the MCP contract.

## Streamable HTTP MCP

For hosts that need MCP over HTTP rather than stdio, Xninetzy exposes
the same tool set over Streamable HTTP via `xninetzy.interfaces.mcp_server`.
The HTTP-MCP listener defaults to `http://127.0.0.1:8765/mcp` and runs
through the same tool registry as stdio. See [Global MCP](/docs/mcp/)
for configuration.

## Authentication boundary

`AI_API_KEY` protects `/api/chat`, `/api/chat/stream`, reminder routes,
and debug routes. When `AI_API_AUTH_REQUIRED=true` but the server key
is empty, protected endpoints return `503`; a missing or invalid caller
key returns `401`.

Streamable HTTP relies on the OS process boundary when bound to
loopback, or on OAuth 2.1 + Resource Indicators (RFC 8707) + Client ID
Metadata Documents when bound beyond loopback.

Keep these controls in place:

- bind to `127.0.0.1` (loopback) for single-owner local use;
- never expose FastAPI port `8000` or Streamable HTTP port `8765`
  directly to the internet;
- disable debug endpoints in any deployment that exposes the API;
- if a reverse proxy terminates TLS, terminate bearer auth there and
  enforce mutual TLS or a private-network ACL;
- there is no separate `MCP_API_KEY` — `AI_API_KEY` is the single auth
  surface.

## Error handling

Use HTTP status codes to distinguish failures:

- `4xx`: payload, authentication, allowlist, or permission failure;
- `5xx`: dependency, provider, database, or unexpected exception;
- health OK but a tool call fails: inspect `xninetzy/observability/`
  trace logs (`request_id`, `trace_id`, `span_id`).

Do not log request headers or complete media payloads in production
because they may contain credentials and personal data.
