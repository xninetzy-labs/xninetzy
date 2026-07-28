---
layout: ../../layouts/DocsLayout.astro
title: Testing dan quality gates
description: Jalankan unit test, typecheck, build, compose validation, dan MCP health check secara terarah.
section: Operasional
---

Jalankan test dari komponen yang berubah terlebih dahulu, lalu full suite sebelum handoff.

## AI service

```bash
cd services/ai
uv sync
uv run pytest -q
uv run ruff check app tests
```

Test mencakup routing, provider, MCP adapter/server, Obsidian, HEBAT, knowledge, reminder, HITL, media, research, workflow, dan Life OS.

Targeted example:

```bash
uv run pytest -q tests/interfaces/test_mcp_server.py \
  tests/interfaces/test_mcp_tool_adapter.py
```

## WA engine

```bash
cd services/wa-enggine
yarn install --frozen-lockfile
yarn test
yarn build
```

Build TypeScript wajib lulus karena test runtime saja tidak selalu menangkap type mismatch.

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

Preview hasil statis:

```bash
yarn preview --host 127.0.0.1
```

Periksa link navigasi, mobile drawer, pencarian, code overflow, dan heading pada viewport kecil.

## Docker configuration

```bash
docker compose config -q
```

Smoke stack:

```bash
docker compose up --build -d ai wa-enggine
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8081/health
```

## MCP global

Uji dari luar repository agar config project tidak menutupi masalah:

```bash
cd /tmp
codex mcp get xninetzy
claude mcp list
opencode mcp list
```

Claude dan OpenCode melakukan health check dan seharusnya menampilkan `Connected`.

## Repository checks

```bash
git diff --check
git status --short
```

Review setiap runtime artifact. Jangan commit `.env`, SQLite/WAL/SHM, FAISS runtime index, HEBAT downloads, session WhatsApp, browser profile, atau `node_modules`.

## Saat full lint belum hijau

Jangan menyamarkan failure. Pisahkan:

1. error baru pada file yang diubah;
2. debt yang sudah ada dan tidak berkaitan;
3. warning tooling/deprecation;
4. test yang memerlukan credential atau service eksternal.

Catat command serta hasil eksaknya dalam handoff.
