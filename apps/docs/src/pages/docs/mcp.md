---
layout: ../../layouts/DocsLayout.astro
title: Global MCP
description: Connect the Xninetzy registry to Codex, Claude Code, and OpenCode from any directory.
section: AI & developer tools
---

Xninetzy MCP uses `stdio` and exposes tools directly from the AI service
registry. Global configuration must use absolute paths; relative paths work only
when a client starts inside the repository.

MCP is the trusted local-owner entry point to Xninetzy. The server injects
identity context at startup via `xninetzy/interfaces/mcp_tool_adapter.py::mcp_principal()`.
Client-supplied `sender_id`, `sender_name`, and `chat_id` values are never
authorization evidence on their own.

## Prerequisites

```bash
cd /absolute/path/to/xninetzy
uv sync
command -v uv
pwd
```

The examples use:

```text
/home/you/.local/bin/uv
/home/you/code/xninetzy
```

Replace both paths with values from your host.

## Global Codex

Codex CLI, its IDE extension, and Codex desktop on the same host share
`~/.codex/config.toml`.

```bash
codex mcp add xninetzy -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy \
  python -m xninetzy.interfaces.mcp_server
```

For browser or research tools, configure explicit timeouts:

```toml
[mcp_servers.xninetzy]
command = "/home/you/.local/bin/uv"
args = ["run", "--directory", "/home/you/code/xninetzy", "python", "-m", "xninetzy.interfaces.mcp_server"]
startup_timeout_sec = 30
tool_timeout_sec = 120
```

Verify outside the repository:

```bash
cd /tmp
codex mcp get xninetzy
codex mcp list
```

## Global Claude Code

User scope makes the server available in every project:

```bash
claude mcp add --scope user xninetzy \
  -e PYTHONUNBUFFERED=1 -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy \
  python -m xninetzy.interfaces.mcp_server
```

```bash
cd /tmp
claude mcp get xninetzy
claude mcp list
```

The result should report `Scope: User config` and `Connected`.

## Global OpenCode

Edit `~/.config/opencode/opencode.jsonc`:

```json
{
  "$schema": "https://opencode.ai/config.json",
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

Merge only `mcp.xninetzy` when the file already has other settings.

```bash
cd /tmp
opencode mcp list
opencode debug config
```

## Use the server

From any directory:

```text
Use MCP xninetzy to list notes in the Learning folder.
```

```text
Use MCP xninetzy to read available HEBAT courses without submitting anything.
```

For a grounded answer:

```text
Use knowledge_answer from MCP xninetzy and preserve its source citations.
```

`knowledge_search` exposes selected evidence for inspection.
`knowledge_answer` performs hybrid retrieval, synthesis, and citation
validation. When evidence is insufficient, the client must disclose the gap.

## Shared Agent Skills

The registry discovers the Xninetzy `SKILL.md` catalog at runtime. Built-ins
live under `xninetzy/.agents/skills`; owner-installed skills live in the
runtime data directory. All clients use the same MCP catalog.

Recommended flow:

```text
Use skill_suggest_for_request for this request.
Load the most relevant result with skill_get.
```

Install a skill without adding application code:

```text
Validate this SKILL.md with skill_validate, then install it with skill_install
using the idempotency key skill-example-v1.
```

`skill_install` accepts only the injected local owner. A skill is workflow
guidance, never factual evidence or a safety-policy override. Catalog changes
are visible on the next request without restarting the MCP client.

Codex discovers repository skills under `.agents/skills`, Claude Code under
`.claude/skills`, and OpenCode under `.agents/skills` or
`.opencode/skills`. In this repository, `.claude/skills` points to the shared
catalog. MCP remains the source for domain tools and OS state.

Learning sessions are also shared:

```text
Use MCP xninetzy to show learning_generate_today_plan, then start a session
with learning_start_study_session and a stable idempotency key.
```

A session started from any MCP client remains the same active session in every
other coding client connected to the same `DATA_DIR`.

## Paths and environment

The server starts in the AI project, so it reads the root `.env`. Never place
API keys directly in MCP configuration.

```dotenv
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

`auto` maps standard container paths to host runtime data when MCP runs outside
Docker.

## Remove configuration

```bash
codex mcp remove xninetzy
claude mcp remove xninetzy --scope user
```

For OpenCode, delete only the `mcp.xninetzy` object.

## Troubleshooting

- Use absolute paths for `uv` and the AI directory.
- Run `uv sync` in `xninetzy`.
- Keep stdout free of application logs because it carries MCP protocol frames.
- Run `claude mcp list` or `opencode mcp list` for health checks.
- Update all global absolute paths after moving the repository.
- Restart the IDE or client after changing configuration.

> Global means available from any directory on the same host. It does not copy the repository or credentials to another machine.

## Streamable HTTP (secondary transport)

Default transport is `stdio`. Streamable HTTP is opt-in for users who want a
localhost HTTP endpoint.

```bash
XNINETZY_MCP_TRANSPORT=streamable-http \
XNINETZY_MCP_HTTP_HOST=127.0.0.1 \
XNINETZY_MCP_HTTP_PORT=8765 \
XNINETZY_MCP_HTTP_PATH=/mcp \
uv run python -m xninetzy.interfaces.mcp_server
```

Then connect to `http://127.0.0.1:8765/mcp`.

The server is configured with `stateless_http=True` and `json_response=True`
(recommended for production per the 2026-07-28 spec direction). Non-loopback
binding logs a warning to stderr at startup — Streamable HTTP bound beyond
localhost requires OAuth 2.1 + Resource Indicators + Client ID Metadata
Documents before it is safe to expose.

## Authorization model

The MCP server injects the trusted local-owner principal at startup via
`xninetzy/interfaces/mcp_tool_adapter.py::mcp_principal()`. Tools receive
`sender_id` / `sender_name` from the host call, but those values are never
authorization evidence on their own. Tools that require owner scope
(`external_mcp_*`, `obsidian_organize_apply`, `improvement_approve`,
etc.) check via `xninetzy/os/research/permissions.py::is_owner_admin`.

FINAL-class tools (per `xninetzy/os/policy/action_policy.py`) always
require HITL approval. The CLI orchestrator enforces this via
`_effective_tier = max(declared, manifest_tier)` so owner-supplied tier
downgrade is rejected.

## Tasks extension (long-running work)

For tools that take more than a few seconds, Xninetzy ships a Tasks
extension adapter (SEP-2663):

- `tasks_submit(name, payload_json)` — register a long task, returns
  `task_id`
- `tasks_get(task_id)` — current status + result
- `tasks_cancel(task_id)` — mark cancelled (active execution not auto-stopped)
- `tasks_list(limit)` — recent tasks

Active result lives in the `long_tasks` SQLite table. Genuinely long tools
(`deep_research`, `mcp_security_audit`, `system_security_analyze`, HEBAT
ingest) keep their sync fast paths today; future migration is a follow-up.

## External MCP gateway

External MCP servers register via `xninetzy/interfaces/external_mcp.py`. Each
entry carries:

- `risk_level` ∈ `unreviewed` / `low` / `medium` / `high`
- `allowed_tools` allowlist (empty = no calls permitted)
- `last_reviewed_at` timestamp
- owner-scoped registration via `is_owner_admin`

`external_mcp_call` rejects any tool not in `allowed_tools` before issuing
the upstream call. Every result is tagged `untrusted_source=True`.
