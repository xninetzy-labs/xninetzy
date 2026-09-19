---
layout: ../../layouts/DocsLayout.astro
title: Chat model selection
description: The host supplies the chat model. Xninetzy is MCP-only; only the optional HTTP bridge consumes a fallback provider.
section: AI & developer tools
---

Xninetzy is MCP-only. The chat model lives in the host that connects
to the MCP server — Claude, Claude Code, Cursor, Codex, OpenCode, or
any other MCP-compatible client. Configure your provider there.

| Path | Provider | Configuration |
|---|---|---|
| Claude / Claude Code / Cursor | Anthropic API key | set in the host application |
| Codex CLI | OpenAI API key | set in the host application |
| OpenCode | OpenAI-compatible, Anthropic, OpenRouter, Ollama | set in the host config |
| Custom host | any OpenAI-compatible endpoint | host-level config |

The Xninetzy MCP server itself never reads an LLM API key. There is no
`LLM_DEFAULT_PROVIDER`, no `FLAZ_API_KEY`, and no
`xninetzy.llm_provider` MCP tool. The registry has no `ai_provider_*`
tools exposed to MCP callers — that module exists internally for the
HTTP bridge only (see below).

## HTTP bridge fallback (optional)

The secondary FastAPI HTTP surface (`/api/chat`, see
[HTTP API](/docs/api/)) does dispatch through a chat failover path
that can fall back to a configured provider. The provider is selected
per-owner in SQLite and is consumed by `xninetzy/core/chat_failover.py`
and `xninetzy/core/llm.py`.

If you use the HTTP bridge with a custom fallback provider, set
`LLM_ENABLED_PROVIDERS` and the corresponding `*_API_KEY` in `.env`.
The default is empty — the host drives the model and the bridge only
echoes MCP tool results.

```dotenv
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-flash
```

This block is intentionally absent from `.env.example` in v2.2.0.
Add it only when you opt into the HTTP bridge with a custom fallback.

## Removed from Xninetzy surface

| Removed in v2.2.0 | Reason |
|---|---|
| `LLM_DEFAULT_PROVIDER` default block in `.env.example` | hosts supply the model |
| `/llm list`, `/llm use` chat commands | slash-command surface removed |
| `ai_provider_*` MCP tools in the public registry | internal to HTTP bridge only |
| `LLM_ENABLED_PROVIDERS` selection at host time | host handles its own model selection |

## See also

- [HTTP API](/docs/api/) — secondary FastAPI surface and `/api/chat`
- [MCP system reference](/docs/mcp-system/) — canonical tool registry
- [Configuration](/docs/configuration/) — every env var explained
