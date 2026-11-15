---
layout: ../../layouts/DocsLayout.astro
title: Backup and restore
description: Create, verify, retain, and safely restore Xninetzy state.
section: Operations
---

A Xninetzy backup contains a SQLite snapshot and, when both are present,
`faiss.index` and `faiss_map.json`. The version1 manifest binds their exact
names, SHA-256 hashes and byte sizes. Verification also checks SQLite
integrity and foreign keys. Invalid manifests, unlisted vector files and
symlinks are refused.

Only these files are selected. Separate `.env`, cookies, browser profiles,
course downloads and the Obsidian vault are excluded. SQLite itself can
contain private records or credentials: `contains_secrets` is unknown
(`null`), never a guarantee that a snapshot is secret-free. Protect the
snapshot as private data and back up vaults/secrets separately. Hashes
detect accidental changes; they do not authenticate an untrusted author.

## Configuration

```dotenv
BACKUP_DIR=~/.local/share/xninetzy/backups
BACKUP_RETENTION=14
```

The backup directory contains private data and is ignored by Git. Keep
a second copy on encrypted storage that only the owner can read.

## Create and verify a snapshot

The backup script lives at `scripts/xninetzy_backup.py`. From the repository,
use the project interpreter and explicitly review the selected SQLite,
vector and backup paths in the process settings. Do not let an unrelated
shell default select a new database. Commands below operate on those paths;
they are owner operations, not an automatic production drill.

```bash
.venv/bin/python scripts/xninetzy_backup.py create
.venv/bin/python scripts/xninetzy_backup.py list
.venv/bin/python scripts/xninetzy_backup.py verify <backup-name>
```

`create` uses SQLite's online backup API, including committed WAL data.
The backup-copy loop has a cooperative30-second budget. A new snapshot
is published only after SQLite validation; retention preserves the just-created
snapshot even if another snapshot has the same second timestamp.

SQLite online consistency does not make the separately copied FAISS pair
transactional with SQLite. Stop all writers for a cross-file snapshot;
otherwise the pair requires separate reconciliation. An incomplete pair is
held. Core SQLite backup needs no embedding/graph library.

## Restore

Restore is an offline owner operation. Stop every MCP session/worker using
the selected database and its projections through its host before proceeding.
An idle process may hold the old file open even when no lock is visible;
the script cannot prove all such processes have stopped. Do not rely on a
removed REST server or one supervisor command to stop every MCP host.

```bash
.venv/bin/python scripts/xninetzy_backup.py restore <backup-name> --confirm
```

`--confirm` acknowledges a trusted local operator's action; it is not an
independently authenticated approval channel and is not exposed as an MCP
permission bypass. No owner restore is authorized by a passing test.

The service refuses existing `-wal`, `-shm` or `-journal` sidecars and busy
databases. Do not delete these files to bypass a hold: recover/checkpoint
through SQLite under separately reviewed owner control. Symlink paths and
overlap with the backup source are also held. Cooperating restores use a
nonblocking POSIX file lock that must not be unlinked while in use.

Verified files are copied into private staging and checked again before any
target replacement. Current state is preserved as a verified pre-restore
snapshot without retention pruning during the restore. Each replacement is
atomic, with canonical SQLite replaced last; database plus vector files are
**not one atomic transaction**. On `restore_interrupted`, keep services offline
and retain the named safety snapshot for reviewed recovery. A failed stage
verification does not change the current database. A corrupt current database
may prevent its safety snapshot and holds automatic replacement.

If a SQLite-only snapshot would leave existing target vectors stale, restore
is held for projection reconciliation instead of deleting user index files.

After restore:

```bash
.venv/bin/python scripts/xninetzy_backup.py verify <backup-name>
```

Reconnect only after the offline restore has completed and any external
effects since the snapshot have been reconciled. Check `task_list`,
`reminder_list` and known authorized records through MCP. A point-in-time
restore also rewinds approval/idempotency/workflow state: do not repeat external
submissions simply because their later receipt/key is absent from the snapshot.
There is no external exactly-once guarantee across restore.

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
