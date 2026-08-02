---
layout: ../../layouts/DocsLayout.astro
title: Coding agents from WhatsApp
description: Configure Codex, Claude Code, or OpenCode with workspace, timeout, MCP, and audit boundaries.
section: AI & developer tools
---

Coding runtimes execute a local CLI against a repository. They are separate from
chat LLM providers and have higher risk because they can read or modify files.

## Requirements

- Codex, Claude Code, or OpenCode is installed on the laptop host.
- The owner has completed interactive CLI login.
- The Xninetzy host bridge runs as a user service.
- Workspace and allowed-root values are absolute paths.
- The WhatsApp administrator has an explicit JID.
- A global `xninetzy` MCP configuration is available to each CLI.

## Configuration

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=opencode
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_EXECUTION_MODE=host_bridge
CODING_AGENT_HOST_BRIDGE_URL=http://host.docker.internal:8765
CODING_AGENT_HOST_BRIDGE_TOKEN=<random-secret>
CODING_AGENT_HOST_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_HOST_ALLOWED_ROOT=/absolute/path/to/xninetzy
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_MAX_OUTPUT_CHARS=30000
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_REQUIRE_XNINETZY_MCP=true
CODING_AGENT_MCP_SERVER_NAME=xninetzy
CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS=15
```

Never use `/`, a home directory, or another broad directory as the allowed
root.

## Usage

```text
/agent list
/agent use codex
/code run the reminder tests and explain any failures
```

Select another runtime with `/agent use claude-code` or
`/agent use opencode`. The runtime preference is stored per owner, and only
allowlisted runtimes can be selected.

## Execution guards

The runtime wrapper:

- never builds commands through shell interpolation;
- confines the working directory to the allowed root;
- passes a minimal environment allowlist;
- bounds duration and output size;
- writes an audit record;
- rejects non-administrators when `CODING_AGENT_ADMIN_ONLY=true`;
- verifies the `xninetzy` MCP server before execution;
- injects the `AGENTS.md` contract, shared OS access, and grounded-knowledge rules.

The effective sandbox also depends on the selected CLI. Do not assume every
runtime has identical sandbox semantics.

## Relationship with MCP

Integration works in both directions:

1. A coding client uses Xninetzy MCP for Obsidian, HEBAT, tasks, and other tools.
2. WhatsApp asks Xninetzy to run a coding client inside an allowed workspace.

When invoked from WhatsApp, preflight must find the CLI's global or user-scoped
MCP configuration. Xninetzy fails closed when MCP is unavailable so the coding
agent cannot return an answer that lacks owner vault, HEBAT, task, or knowledge
context.

## Safe workflow

Start with a narrow, verifiable request:

```text
/code diagnose why test_reminder_parser fails; do not modify files
```

After reviewing the diagnosis:

```text
/code implement the reviewed fix, run the related tests, and summarize changed files
```

Avoid broad prompts such as “fix everything” when repository runtime state has
not been backed up.

## Host bridge and containers

The AI container does not include coding binaries, host login stores, or global
host configuration. In `host_bridge` mode, the AI service sends an
authenticated task to `127.0.0.1:8765` through `host.docker.internal`. The
bridge performs MCP preflight, confines the workspace, runs the host CLI, and
returns bounded output to WhatsApp.

Install the bridge on Linux:

```bash
bash scripts/install_host_agent_bridge.sh
loginctl enable-linger "$USER"
systemctl --user status xninetzy-host-agent-bridge
```

Never expose the bridge port to a public network or place its token in prompts
or MCP client configuration.

## Diagnosis

```bash
which codex
which claude
which opencode
```

Inspect audit logs without printing credentials. Common failures are missing
binaries, expired login, a workspace outside the allowed root, timeout, or a CLI
waiting for interactive input.
