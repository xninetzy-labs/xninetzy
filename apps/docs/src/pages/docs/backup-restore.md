---
layout: ../../layouts/DocsLayout.astro
title: Backup and restore
description: Create, verify, retain, and safely restore Xninetzy state.
section: Operations
---

A Xninetzy backup contains a consistent SQLite snapshot and, when
available, `faiss.index` and `faiss_map.json`. Every snapshot has a
SHA-256 manifest. Credentials, `.env`, cookies, HEBAT browser profiles,
course downloads, and the Obsidian vault are excluded. Back up vaults
and secrets separately.

## Configuration

```dotenv
BACKUP_DIR=~/.local/share/xninetzy/backups
BACKUP_RETENTION=14
```

The backup directory contains private data and is ignored by Git. Keep
a second copy on encrypted storage that only the owner can read.

## Create and verify a snapshot

The backup script lives at `scripts/xninetzy_backup.py`. Run it with
`uv` so the repo's virtualenv is used:

```bash
uv run --no-project --directory . python scripts/xninetzy_backup.py create
uv run --no-project --directory . python scripts/xninetzy_backup.py list
uv run --no-project --directory . python scripts/xninetzy_backup.py verify <backup-name>
```

`create` uses the SQLite online backup API, so a running MCP server can
produce a consistent snapshot. A retention policy removes old snapshots
only after a new snapshot succeeds.

## Restore

Stop the MCP server before restoring:

```bash
# stop the supervisor first
uv run python -m xninetzy.cli.supervisor stop
uv run --no-project --directory . python scripts/xninetzy_backup.py restore <backup-name>
uv run python -m xninetzy.cli.supervisor start
```

Restore requires explicit confirmation. It verifies the manifest, backs
up the current target, writes through temporary files, validates SQLite
integrity, and atomically replaces the targets. If verification fails,
the current database is left unchanged.

After restore:

```bash
uv run --no-project --directory . python scripts/xninetzy_backup.py verify <backup-name>
curl -s http://127.0.0.1:8000/health
```

Verify important tools through MCP, e.g. `task_list`, `reminder_list`,
and a knowledge query against a known note.

## Recovery boundaries

- SQLite is canonical for structured OS state.
- FAISS is rebuildable from SQLite when its chunk map invariant fails.
- Neo4j is a projection and is not part of the canonical snapshot.
- HEBAT sessions require separate reauthentication.
- The Obsidian vault requires its own versioned or encrypted backup.
- The External MCP registry (`EXTERNAL_MCP_REGISTRY_PATH`) stores
  `allowed_tools` allowlists and `risk_level` per server; back it up
  alongside other structured OS state if desired, but treat it as
  reauthorable configuration.
