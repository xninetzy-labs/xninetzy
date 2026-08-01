---
layout: ../../layouts/DocsLayout.astro
title: Obsidian vault management
description: Canonical foldering, safe migration, note metadata, MOCs, and grounded knowledge.
section: Integrations
---

<div data-locale="en">

Xninetzy treats Obsidian as the human-readable persistence layer for the Learning OS and Life OS. Every interface uses the same vault policy: WhatsApp, LangGraph, MCP, Codex, Claude Code, and OpenCode never maintain separate note conventions.

## Canonical vault structure

```text
Home.md
Inbox/Captures/       Inbox/Triage/        Inbox/Unsorted/
Daily/YYYY/YYYY-MM-DD.md
Learning/Roadmaps/    Learning/Concepts/   Learning/Sessions/
Learning/Notes/       Learning/Reviews/    Learning/MOCs/
Projects/<project>/README.md
Academic/HEBAT/Courses/<course>/Materials/
Academic/HEBAT/Courses/<course>/Assignments/
Academic/Cyber-Campus/{Schedule,Grades,KRS}/
Research/{Briefs,Sources,Topics,MOCs}/
Life/{Goals,Tasks,Habits,Money,Workouts,Areas,Reviews}/
Knowledge/{Notes,Sources,MOCs}/
Attachments/
System/{MOCs,Templates,Help,Logs,Migration}/
Archive/
```

Existing paths such as `Daily/`, `Learning/`, `Tasks/`, `Goals/`, `HEBAT/`, and `Helper/` remain readable. New generated notes use the canonical paths. Migration is hybrid: preview first, then owner approval, backup, atomic move, link update, and verification.

## Folder management tools

| Tool | Behavior |
| --- | --- |
| `obsidian_vault_init` | Creates the canonical folder structure. |
| `obsidian_folder_status` | Reports missing folders and duplicate note IDs. |
| `obsidian_organize_preview` | Read-only inventory and migration plan. |
| `obsidian_organize_apply` | Creates an approval request before moving notes. |
| `obsidian_moc_refresh` | Rebuilds domain indexes and navigation links. |
| `obsidian_verify` | Runs the vault health checks. |

Example:

```text
Use MCP xninetzy to preview the Obsidian folder migration.
Do not move anything until I approve the plan.
```

## Note metadata

Generated notes use a stable frontmatter contract:

```yaml
---
schema_version: 1
type: learning_concept
title: Gradient descent
canonical_path: Learning/Concepts/gradient-descent.md
status: active
created: 2026-08-02T10:00:00+07:00
updated: 2026-08-02T10:00:00+07:00
tags: [xninetzy, learning-concept]
source_type: knowledge
source_id:
---
```

Unknown existing fields are preserved during migration. Folder names and filenames use lowercase kebab-case; note titles remain human-readable. Tags are lowercase and do not include the `#` prefix.

## Safety and privacy

- All paths are vault-relative and reject absolute paths, traversal, credentials, and blocked runtime directories.
- Overwrites and migrations create backups when `OBSIDIAN_BACKUP_BEFORE_WRITE=true`.
- Migration validates the source hash and skips notes changed after preview.
- Unknown notes stay in place and are reported instead of being moved silently.
- HEBAT summaries may be stored, but Cyber Campus grades, tokens, cookies, and KRS details are not persisted by default.
- Downloads, browser state, SQLite, and WhatsApp sessions remain outside the vault.

## Configuration

```dotenv
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/vault
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
OBSIDIAN_FOLDERING_ENABLED=true
OBSIDIAN_ORGANIZE_MODE=hybrid
OBSIDIAN_REQUIRE_ORGANIZE_APPROVAL=true
OBSIDIAN_AUTO_REFRESH_MOC=true
OBSIDIAN_PERSIST_ACADEMIC_SENSITIVE=false
OBSIDIAN_LEGACY_PATH_COMPATIBILITY=true
```

## Knowledge and learning workflow

Use the shared loop:

1. Capture a note or source in `Inbox/Captures`.
2. Triage it into Learning, Research, Knowledge, Academic, Life, or Projects.
3. Ingest evidence into the knowledge index when it must be searchable.
4. Link concepts, roadmaps, tasks, and evidence through MOCs and wikilinks.
5. Review progress through daily and weekly notes.

`knowledge_search` is evidence inspection. `knowledge_answer` produces grounded answers with citations. Raw vector chunks are never presented as final answers.

</div>

<div data-locale="id" hidden>

Xninetzy menggunakan Obsidian sebagai lapisan penyimpanan yang mudah dibaca manusia untuk Learning OS dan Life OS. Semua interface memakai aturan vault yang sama: WhatsApp, LangGraph, MCP, Codex, Claude Code, dan OpenCode tidak memiliki konvensi note terpisah.

## Struktur folder canonical

```text
Home.md
Inbox/Captures/       Inbox/Triage/        Inbox/Unsorted/
Daily/YYYY/YYYY-MM-DD.md
Learning/Roadmaps/    Learning/Concepts/   Learning/Sessions/
Learning/Notes/       Learning/Reviews/    Learning/MOCs/
Projects/<project>/README.md
Academic/HEBAT/Courses/<course>/Materials/
Academic/HEBAT/Courses/<course>/Assignments/
Academic/Cyber-Campus/{Schedule,Grades,KRS}/
Research/{Briefs,Sources,Topics,MOCs}/
Life/{Goals,Tasks,Habits,Money,Workouts,Areas,Reviews}/
Knowledge/{Notes,Sources,MOCs}/
Attachments/
System/{MOCs,Templates,Help,Logs,Migration}/
Archive/
```

Path lama tetap bisa dibaca. Note baru memakai path canonical. Migrasi menggunakan mode hybrid: preview, approval owner, backup, pemindahan atomic, pembaruan link, lalu verifikasi.

## Tool management folder

- `obsidian_vault_init` menyiapkan struktur folder.
- `obsidian_folder_status` memeriksa folder dan duplicate ID.
- `obsidian_organize_preview` membuat inventory dan rencana migrasi read-only.
- `obsidian_organize_apply` meminta approval sebelum memindahkan note.
- `obsidian_moc_refresh` memperbarui index dan navigasi.
- `obsidian_verify` menjalankan health check vault.

Nilai, token, cookie, KRS, session browser, SQLite, dan credential tidak disimpan otomatis ke vault.

</div>
