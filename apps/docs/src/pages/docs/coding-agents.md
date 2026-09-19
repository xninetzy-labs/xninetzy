---
layout: ../../layouts/DocsLayout.astro
title: Coding agents
description: Configure Codex, Claude Code, or OpenCode with workspace, timeout, MCP, and audit boundaries.
section: AI & developer tools
---

Coding runtimes execute a local CLI against a repository. They are
separate from chat LLM providers and have higher risk because they can
read or modify files. There is no WhatsApp-mediated path in v2.2.0;
coding agents reach Xninetzy through the same MCP server as every other
client.

## Requirements

- Codex, Claude Code, or OpenCode is installed on the laptop host.
- The owner has completed interactive CLI login.
- The Xninetzy MCP server is reachable from the host (stdio or Streamable
  HTTP, see [Global MCP](/docs/mcp/)).
- Workspace and allowed-root values are absolute paths.
- A global `xninetzy` MCP configuration is available to each CLI.

## Configuration

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=opencode
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_MAX_OUTPUT_CHARS=30000
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_REQUIRE_XNINETZY_MCP=true
CODING_AGENT_MCP_SERVER_NAME=xninetzy
CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS=15
```

Never use `/`, a home directory, or another broad directory as the
allowed root. Owner identity is resolved through
`xninetzy/os/research/permissions.py::is_owner_admin`.

## Usage

From any MCP-aware coding client, the runtime preference is stored per
owner in SQLite and only allowlisted runtimes can be selected. CLI-level
selection:

```bash
# Codex CLI
codex --mcp xninetzy "<task>"

# Claude Code
claude --mcp xninetzy "<task>"

# OpenCode
opencode --mcp xninetzy "<task>"
```

## Execution guards

The runtime wrapper:

- never builds commands through shell interpolation;
- confines the working directory to the allowed root;
- passes a minimal environment allowlist;
- bounds duration and output size;
- writes an audit record;
- rejects non-administrators when `CODING_AGENT_ADMIN_ONLY=true`;
- verifies the `xninetzy` MCP server before execution;
- injects the `AGENTS.md` contract, shared OS access, and grounded-knowledge
  rules.

The effective sandbox also depends on the selected CLI. Do not assume
every runtime has identical sandbox semantics.

## Relationship with MCP

Coding clients use the Xninetzy MCP server for Obsidian, HEBAT, tasks,
knowledge, and other capabilities. When the host invokes a coding
client, preflight must find the CLI's global or user-scoped MCP
configuration. Xninetzy fails closed when MCP is unavailable so the
coding agent cannot return an answer that lacks owner vault, HEBAT,
task, or knowledge context.

## Safe workflow

Start with a narrow, verifiable request:

```text
Diagnose why test_reminder_parser fails; do not modify files.
```

After reviewing the diagnosis:

```text
Implement the reviewed fix, run the related tests, and summarize changed files.
```

Avoid broad prompts such as "fix everything" when repository runtime
state has not been backed up.

## Diagnosis

```bash
which codex
which claude
which opencode
```

Inspect audit logs without printing credentials. Common failures are
missing binaries, expired login, a workspace outside the allowed root,
timeout, or a CLI waiting for interactive input.
