---
layout: ../../layouts/DocsLayout.astro
title: Testing and quality gates
description: Run unit tests, type checks, builds, and MCP health checks.
section: Operations
---

Run tests for the changed component first, then run its full suite
before handoff. The canonical command bundle is:

```bash
uv run --no-project --directory . ruff check xninetzy tests
uv run --no-project --directory . pytest -ra
uv run --no-project --directory . python scripts/verify_cpu_only.py
cd apps/docs && yarn check && yarn build
uv run --no-project --directory . python scripts/install_skills.py --dry-run
```

## Python tests

```bash
uv sync --all-extras
uv run pytest -q
uv run ruff check xninetzy tests
```

Tests cover routing, providers, MCP adapters and servers, Obsidian,
HEBAT, knowledge, reminders, HITL, media, research, workflows, and Life
OS.

Focused example:

```bash
uv run pytest -q tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

The release gate `xninetzy.cli.supervisor release-check` runs 5 checks
(`tool_registry`, `secret_redaction`, `safe_fetch`, `transport_config`,
`sdk_pin`) and must be green before any merge.

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

Inspect navigation links, the mobile drawer, search, code overflow, and
headings on a narrow viewport.

## Skills installer dry-run

```bash
uv run --no-project --directory . python scripts/install_skills.py --dry-run
```

Confirms every skill in `.agents/skills/` parses, has valid frontmatter,
and would install cleanly to the configured harness targets.

## Global MCP

Test outside the repository so project configuration cannot hide a
global configuration problem:

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

Claude and OpenCode perform health checks and should report
`Connected`.

## Repository checks

```bash
git diff --check
git status --short
```

Review every runtime artifact. Never commit `.env`, SQLite/WAL/SHM,
runtime FAISS indexes, HEBAT downloads, browser profiles, or
`node_modules`.

## When the full checks are not green

Do not hide a failure. Separate:

1. new errors in changed files;
2. existing unrelated debt;
3. tooling or deprecation warnings;
4. tests that require credentials or external services.

Record the exact command and result in the handoff. The current
baseline is **828 pass / 29 fail / 7 collection-blocked** — see
`tests/baseline/REPORT.md` for the full list of excluded files.
