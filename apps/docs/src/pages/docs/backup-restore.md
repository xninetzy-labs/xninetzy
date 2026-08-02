---
layout: ../../layouts/DocsLayout.astro
title: Backup and restore
description: Create, verify, retain, and safely restore Xninetzy state.
section: Operations
---

A Xninetzy backup contains a consistent SQLite snapshot and, when available,
`faiss.index` and `faiss_map.json`. Every snapshot has a SHA-256 manifest.
Credentials, `.env`, cookies, WhatsApp sessions, browser profiles, course
downloads, and the Obsidian vault are excluded. Back up vaults and secrets
separately.

## Configuration

```dotenv
BACKUP_DIR=/app/data/backups
BACKUP_RETENTION=14
```

The backup directory contains private data and is ignored by Git. Keep a second
copy on encrypted storage that only the owner can read.

## Create and verify a snapshot

For Docker, run inside the container so `/app/data` resolves to the mounted
volume:

```bash
docker compose exec ai uv run python scripts/xninetzy_backup.py create
docker compose exec ai uv run python scripts/xninetzy_backup.py list
docker compose exec ai uv run python scripts/xninetzy_backup.py verify <backup-name>
```

For host mode, run from `services/ai` after pointing `SQLITE_PATH`,
`VECTOR_DATA_DIR`, and `BACKUP_DIR` to host paths.

`create` uses the SQLite online backup API, so a running service can produce a
consistent snapshot. A retention policy removes old snapshots only after a new
snapshot succeeds.

## Restore

Stop writers before restoring:

```bash
docker compose stop ai
docker compose run --rm ai uv run python scripts/xninetzy_backup.py restore <backup-name>
docker compose up -d ai
```

Restore requires explicit confirmation. It verifies the manifest, backs up the
current target, writes through temporary files, validates SQLite integrity, and
atomically replaces the targets. If verification fails, the current database
is left unchanged.

After restore:

```bash
docker compose exec ai uv run python scripts/xninetzy_backup.py verify <backup-name>
curl -s http://127.0.0.1:8000/health
```

Also verify important tools through MCP or WhatsApp.

## Recovery boundaries

- SQLite is canonical for structured OS state.
- FAISS is rebuildable from SQLite when its chunk map invariant fails.
- Neo4j is a projection and is not part of the canonical snapshot.
- WhatsApp and HEBAT sessions require separate reauthentication.
- The Obsidian vault requires its own versioned or encrypted backup.
