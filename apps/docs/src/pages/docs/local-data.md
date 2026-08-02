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
clone A → services/ai/data/xninetzy.sqlite3 owned by owner A
clone B → services/ai/data/xninetzy.sqlite3 owned by owner B
```

The database is created and migrated automatically when the AI service starts.
State is never shared through Git, Codex configuration, Claude configuration, or
OpenCode configuration. An MCP client on a machine points to that machine's
configured local installation.

## Repository rules

All of `services/ai/data/**` is ignored by Git except the policy file
`services/ai/data/README.md`. This includes:

- SQLite, `-wal`, and `-shm`;
- FAISS indexes and maps that represent personal knowledge;
- HEBAT browser profiles, cookies, state, downloads, and debug HTML;
- web-analysis snapshots and reports;
- normalized Cyber Campus grade snapshots without verified tokens;
- Learning OS concept graphs, evidence, and mastery;
- recall cards, attempts, confidence, and spaced-repetition schedules;
- WhatsApp media and local backups.

Before committing:

```bash
git status --short
git ls-files services/ai/data
```

`git ls-files` should list only `services/ai/data/README.md`.

## Move an installation

Use [Backup and restore](/docs/backup-restore/) instead of committing a
database. Backups have checksums and restore confirmation. Transfer a snapshot
through encrypted media, restrict access to the owner, and remove temporary
copies.

## If data was pushed

Removing a file from the latest commit does not remove its blob from history.
Before making the repository public:

1. revoke or rotate any exposed session or credential;
2. create a private backup clone;
3. sanitize history with a tool such as `git filter-repo`;
4. force-push only after coordinating with every collaborator;
5. run a secret scan and inspect `git ls-files` again;
6. ask collaborators to create fresh clones after history changes.

History rewriting is destructive and is never performed automatically by
Xninetzy.
