---
layout: ../../layouts/DocsLayout.astro
title: Testing and quality gates
description: Run unit tests, type checks, builds, Compose validation, and MCP health checks.
section: Operations
---

Run tests for the changed component first, then run its full suite before
handoff.

## AI service

```bash
cd services/ai
uv sync
uv run pytest -q
uv run ruff check app tests
```

Tests cover routing, providers, MCP adapters and servers, Obsidian, HEBAT,
knowledge, reminders, HITL, media, research, workflows, and Life OS.

Focused example:

```bash
uv run pytest -q tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

## WhatsApp engine

```bash
cd services/wa-enggine
yarn install --frozen-lockfile
yarn test
yarn build
```

The TypeScript build must pass because runtime tests do not catch every type
mismatch.

## Terminal CLI

```bash
cd apps/cli
yarn install --frozen-lockfile
yarn typecheck
yarn build
```

## Documentation app

```bash
cd apps/docs
yarn install --frozen-lockfile
yarn check
yarn build
```

Preview the static output:

```bash
yarn preview --host 127.0.0.1
```

Inspect navigation links, the mobile drawer, search, code overflow, and headings
on a narrow viewport.

## Docker configuration

```bash
docker compose config -q
```

Smoke-test the stack:

```bash
docker compose up --build -d ai wa-enggine
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8081/health
```

## Global MCP

Test outside the repository so project configuration cannot hide a global
configuration problem:

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

Claude and OpenCode perform health checks and should report `Connected`.

## Repository checks

```bash
git diff --check
git status --short
```

Review every runtime artifact. Never commit `.env`, SQLite/WAL/SHM, runtime
FAISS indexes, HEBAT downloads, WhatsApp sessions, browser profiles, or
`node_modules`.

## When the full checks are not green

Do not hide a failure. Separate:

1. new errors in changed files;
2. existing unrelated debt;
3. tooling or deprecation warnings;
4. tests that require credentials or external services.

Record the exact command and result in the handoff.
