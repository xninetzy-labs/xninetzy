---
layout: ../../layouts/DocsLayout.astro
title: Local data per installation
description: Per-owner SQLite, runtime-data isolation, migrations, backups, and open-source repository hygiene.
section: Operations
---

Every Xninetzy installation owns a separate SQLite database. The repository
contains no sample owner database, WAL or SHM files, FAISS state, Moodle
sessions, downloads, or analysis snapshots.

```text
clone A → ~/.local/share/xninetzy/xninetzy.sqlite3   owner A
clone B → ~/.local/share/xninetzy/xninetzy.sqlite3   owner B
```

The database is created and migrated automatically when the MCP server
boots via `xninetzy/db/migrations.py::run_migrations()` +
`xninetzy/db/sqlite.py::init_db()`. State is never shared through Git or
any MCP client configuration. An MCP client on a machine points to that
machine's configured local installation.

## Repository rules

`DATA_DIR` (default `~/.local/share/xninetzy`) is ignored by Git except
for its README. This includes:

- SQLite, `-wal`, and `-shm`;
- FAISS indexes and maps that represent personal knowledge;
- HEBAT browser profiles, cookies, state, downloads, and debug HTML;
- web-analysis snapshots and reports;
- normalized Cyber Campus grade snapshots without verified tokens;
- Learning OS concept graphs, evidence, and mastery;
- recall cards, attempts, confidence, and spaced-repetition schedules;
- long-task records (`long_tasks` table for the Tasks extension);
- external MCP registry state (default path
  `/app/data/external-mcp.json`).

Before committing:

```bash
git status --short
git ls-files .local/share/xninetzy 2>/dev/null
```

Only the README should be tracked. The default `DATA_DIR` lives outside
the repository, so a clean clone never carries any owner data.

## Path conventions (env-driven)

| Env var | Default |
|---|---|
| `DATA_DIR` | `~/.local/share/xninetzy` |
| `OUTPUT_DIR` | `~/Documents/xninetzy/output` |
| `GENERATED_DOCUMENTS_DIR` | `~/Documents/xninetzy/generated/documents` |
| `RESEARCH_OUTPUT_DIR` | `~/Documents/xninetzy/generated/research` |
| `UNTRACKED_OUTPUT_DIR` | `~/Documents/xninetzy/generated/untracked` |
| `HEBAT_DATA_DIR` | `~/.local/share/xninetzy/hebat` |
| `HEBAT_DOWNLOAD_DIR` | `~/Documents` |
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` |
| `EXTERNAL_MCP_REGISTRY_PATH` | `/app/data/external-mcp.json` |

`ARTIFACT_ALLOWLIST=true` (default) rejects writes outside the four
`*_DIR` roots above.

## Move an installation

Use [Backup and restore](/docs/backup-restore/) instead of committing a
database. Backups have checksums and restore confirmation. Transfer a
snapshot through encrypted media, restrict access to the owner, and
remove temporary copies.

## If data was pushed

Removing a file from the latest commit does not remove its blob from
history. Before making the repository public:

1. revoke or rotate any exposed session or credential (`AI_API_KEY`,
   `HEBAT_PASSWORD`, OAuth client secrets);
2. create a private backup clone;
3. sanitize history with a tool such as `git filter-repo`;
4. force-push only after coordinating with every collaborator;
5. run a secret scan (`xninetzy/os/security/guards.py::redact_secrets`
   patterns) and inspect `git ls-files` again;
6. ask collaborators to create fresh clones after history changes.

History rewriting is destructive and is never performed automatically by
Xninetzy.
