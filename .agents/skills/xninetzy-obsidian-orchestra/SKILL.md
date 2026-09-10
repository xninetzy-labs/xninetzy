---
name: xninetzy-obsidian-orchestra
description: Structural and navigational operating system for the canonical Xninetzy Obsidian vault. Use for folder/file conventions, course and project structures, migrations, semester archiving, MOCs, frontmatter normalization, Mermaid visualization, vault health, naming integrity, portal-to-Obsidian ingestion, backlink consistency, and safe structural changes.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "inspect -> classify -> plan -> preview -> approve -> mutate -> verify -> index -> checkpoint"
---

# Xninetzy Obsidian Orchestra

This skill is the **structural and navigational operating system for the Xninetzy Obsidian vault**. Its responsibility is to keep the vault organized, human-readable, canonical, retrievable, internally consistent, and safe to restructure.

The vault should function as a **living knowledge system**, not a collection of files.

The canonical lifecycle is:

**Inspect → Classify → Plan → Preview → Approve → Mutate → Verify → Index → Checkpoint**

## Scope boundary

Use this skill for:

* folder creation and restructuring,
* file placement and naming,
* note migration and semester archiving,
* MOC generation and refresh,
* frontmatter normalization,
* backlink and index maintenance,
* vault health checks,
* orphan and duplicate detection,
* naming-violation repair,
* project and course note structure,
* portal-analysis ingestion into Obsidian,
* Mermaid diagram insertion when the note structure requires it.

Do not use this skill as the primary owner for:

* deep note-content retrieval,
* semantic knowledge querying,
* graph reasoning,
* daily task management,
* durable cross-session memory,
* academic portal operations.

Route those concerns to the appropriate specialized skill.

## When to use

* the user asks to create, move, rename, or archive a note, folder, MOC, or section;
* the user asks to inspect vault health, naming violations, or orphan notes;
* the user asks to migrate notes, refresh an MOC, or normalize frontmatter;
* the user asks to ingest portal analysis into the vault.

## When NOT to use

* reading, searching, or synthesizing note content — use `obsidian-knowledge`;
* answering from vault evidence — use `obsidian-knowledge` or `xninetzy-knowledge-answer`;
* writing a long document — use `xninetzy-artifact-orchestrator`.

## Core principle

Every note should have the right location, the right name, the right frontmatter, the right navigation path, and the right structural relationships. Do not create a new convention merely because the existing vault is inconvenient. When a structural decision is ambiguous, **inspect the current canonical structure first.**

## Source of truth

For vault organization, the current vault structure is authoritative:

```text
current vault state
↓
existing conventions
↓
this skill's general rules
↓
fallback assumptions
```

Do not silently impose a new folder architecture if the current vault already contains an established and coherent pattern. When migrating across structures, preserve the canonical organization rather than creating parallel systems.

## Core workflow

1. **Inspect.** Inspect the current vault structure, conventions, and any existing canonical folders before planning a change.
2. **Classify.** Identify whether the change is small (one folder, one rename, one README) or broad (migration, archive, restructuring). Small changes may follow the available authorization policy. Broad changes require preview and approval.
3. **Plan.** Define the target state, affected files, naming changes, link implications, and possible conflicts.
4. **Preview.** Show the proposed path, the reason, the risk, and the conflict resolution strategy for non-trivial changes.
5. **Approve.** Require explicit approval for mass migration, bulk renaming, large archive operations, destructive cleanup, duplicate merging, or restructuring multiple top-level areas.
6. **Mutate.** Execute the narrowest required action. Preserve content, frontmatter, and metadata. Update links and refresh MOCs.
7. **Verify.** Confirm destination paths, source removal/rename where applicable, folder status, broken references, MOC refresh, frontmatter integrity, and unresolved items.
8. **Index.** Refresh MOCs, search indexes, and backlink consistency.
9. **Checkpoint.** Persist a continuity checkpoint when the structural change is material.

## Human-readable naming

Names should be understandable without opening the file.

### Course folders

Format: `{Code} - {Full Name}`. Examples: `SII213 - Inovasi Sistem Informasi dan Teknologi`, `SII208 - Desain Interaksi`. Avoid numeric IDs, internal codes, or auto-generated slugs.

### Semester folders

Format: `{Year} {Period}`. Examples: `2026 Ganjil`, `2025 Genap`. Avoid `2026Ganjil`, `2025genap`, or `2025g`.

### Topic folders

Use natural topic names: `Machine Learning`, `Enterprise Architecture`, `SDLC`, `Data Visualization`. Avoid meaningless slugs or internal codes.

### Project folders

Format: `{Project Name}`. Examples: `BEM UNAIR 2026`, `Xninetzy`, `EcoTrack`.

## Folder naming prohibitions

Never use numeric IDs, database IDs, LMS internal IDs, auto-generated slugs, meaningless abbreviations, week markers as permanent folder hierarchy, or excessively nested folder paths. Use numbering inside filenames when sequential order is meaningful.

## File naming

* **Daily notes** — `YYYY-MM-DD.md`.
* **Lecture notes** — `NN - Topic Name.md`.
* **Assignments** — `Tugas N - Title.md`.
* **MOCs** — `00 - Index.md`.
* **Concepts** — `Concept Name.md`.
* **General notes** — `Title Name.md`.

Avoid IDs as filenames. Prefer meaningful human-readable names. Use spaces for normal vault titles unless the existing project convention explicitly uses kebab-case.

## Canonical vault structure

Default structure:

```text
/
├── Academic/
│   ├── Current/
│   │   └── {Code} - {Full Name}/
│   │       ├── Materials/
│   │       ├── Assignments/
│   │       ├── Notes/
│   │       └── README.md
│   │
│   ├── Archive/
│   │   └── {Year} {Period}/
│   │       └── {Code} - {Full Name}/
│   │
│   ├── BBK/
│   ├── KRS/
│   ├── Schedule/
│   ├── UACC/
│   │   ├── Pages/
│   │   ├── UACC Portal Overview.md
│   │   └── Workflow.md
│   ├── HEBAT/
│   ├── Cyber Campus/
│   └── QA/
│
├── Knowledge/
│   ├── Notes/
│   ├── Concepts/
│   ├── Literature/
│   └── Sources/
│
├── Learning/
│   ├── {Topic Name}/
│   ├── Roadmaps/
│   └── Sessions/
│
├── Life/
│   ├── Goals/
│   ├── Habits/
│   ├── Health/
│   └── Finance/
│
├── Research/
│   ├── Manifests/
│   └── Reports/
│
├── Projects/
│   └── {Project Name}/
│
├── Inbox/
├── Archive/
├── Templates/
├── Daily/
└── System/
```

This is the **default architecture**, not an instruction to rebuild an existing vault blindly.

## Current vs archive boundary

`Academic/Current/` contains only active-semester courses. `Academic/Archive/` contains previous semesters. Never mix active and archived semesters. When a semester ends, move complete course structures into `Archive/{Year} {Period}/`. Preserve course identity and internal structure.

## Course structure

A course folder should normally contain `Materials/`, `Assignments/`, `Notes/`, and `README.md`. The README holds navigation: course code, full name, semester, status, official links, schedule, key materials, and assignment index.

## Frontmatter standard

Every managed note should have minimal frontmatter:

```yaml
---
type: note|concept|material|assignment|daily|moc
course: COURSE_CODE
course_name: FULL_NAME
semester: "YYYY Period"
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active|archived|draft
---
```

Only include course fields when the note is academic. Do not invent metadata values.

## MOC architecture

MOCs are navigation systems, not content dumps. Use `00 - Index.md`. A course MOC may link Overview, Materials, Assignments, Lecture Notes, Concepts, Projects, and Related Courses. Keep MOCs compact.

## MOC refresh triggers

Refresh MOCs after course creation, significant migration, five or more new notes, semester archival, major renaming, structural reorganization, or user request. Do not regenerate every MOC after every tiny note edit.

## Vault health check

Run health checks for folder structure, naming violations, misplaced files, duplicate notes, orphaned TODOs, broken references, missing frontmatter, FTS/index health, excessive nesting, and stale MOCs.

## Reference map

* `references/migrations-and-safety.md` — migration workflow, preview, safety, naming repair, conflict resolution, frontmatter normalization, idempotency, duplicate detection, broken-link safety, aliases, anti-patterns, and verification after mutation.
* `references/mocs-and-diagrams.md` — MOC architecture, refresh triggers, integrity, nesting limit, inbox, daily, archive, portal-to-Obsidian ingestion, portal naming, portal overview notes, per-page notes, Mermaid standard, diagram mapping, Mermaid syntax, diagram selection rule, and current course reference.
* `references/semesters-and-validation.md` — current vs archive boundary, semester transition, structural vs content operations, safe mutation model, small vs broad changes, semester archives, completion contract, standard health output, and operating rules.

## Routing

* Reading and answering from vault evidence → `obsidian-knowledge`.
* Semantic knowledge querying → `xninetzy-knowledge-answer`.
* HEBAT context → `hebat-academic`.
* Cyber Campus and KRS → `xninetzy-cyber-campus`.
* Cross-session continuity → `xninetzy-memory`.
* Graph relationships → `graph-rag`.

## Operating rules

The system must:

* inspect before restructuring,
* use human-readable canonical names,
* separate active and archived academic content,
* preserve existing valid conventions,
* preview broad mutations,
* preserve content and metadata during migration,
* repair links after structural changes,
* maintain MOCs as navigation systems,
* use Mermaid for meaningful structural/process visualization,
* never fabricate dates in diagrams,
* avoid deep folder nesting,
* keep `Daily/` restricted to daily notes,
* verify actual vault state after mutations,
* avoid duplicate creation through idempotent checks,
* separate structural orchestration from note-content reasoning,
* report incomplete operations honestly.

The central objective is:

> **Maintain one coherent, human-readable, machine-retrievable Obsidian vault in which structure is intentional, naming is canonical, navigation remains usable, and every structural change can be inspected and verified.**