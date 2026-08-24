---
name: xninetzy-obsidian-orchestra
description: >
  Orchestrate, reorganize, and maintain the canonical Obsidian vault structure for Xninetzy.
  Use when: creating folders, migrating notes, fixing naming conventions, generating MOCs,
  running vault health checks, restructuring the vault, archiving old semester content,
  writing or upgrading project/course notes with diagrams (Mermaid visualization standard),
  or any request about Obsidian folder organization and file placement.
  Do NOT use for: reading note content (use obsidian-knowledge), graph queries (use graph-rag),
  or daily note creation (use life-management).
---

# Xninetzy Obsidian Orchestra

Manage the Obsidian vault's folder structure, naming conventions, and navigation
as a single, coherent system. Every note must live in the right place with the
right name so that retrieval, MOC generation, and cross-session memory all work.

## Principle

The vault is a **living knowledge base**, not a file dump. Every folder has a
clear purpose. Every naming convention exists so that humans and agents can find
things without guessing. When in doubt, check this skill before creating or
moving anything.

## Naming Rules (STRICT)

### Folder Names — MUST be human-readable

| Type | Format | Good | Bad |
|------|--------|------|-----|
| Course | `{Code} - {Full Name}` | `SII213 - Inovasi SI dan Teknologi` | `SII213`, `10929`, `2025genap-sii213-*` |
| Semester | `{Year} {Period}` | `2026 Ganjil`, `2025 Genap` | `2026Ganjil`, `2025Genap`, `2025g` |
| Topic | `{Topic Name}` | `Machine Learning`, `SDLC`, `TOGAF` | `machine-learning`, `sic201` |
| Project | `{Project Name}` | `BEM UNAIR 2026`, `Xninetzy` | `bemunair2026`, `xninetzy-proj` |

### Folder Names — NEVER use

- Numeric IDs: `10929`, `10924`, `10976`
- Auto-generated slugs: `2025genap-sic201-pembelajaran-mesin-s1-sistem-informasi-2021-i2`
- Abbreviations that aren't course codes: `pm`, `jk`, `se`
- Temporal markers: `week-1`, `bab-1` (use numbering in files instead)

### File Names

| Type | Format | Example |
|------|--------|---------|
| Daily note | `YYYY-MM-DD.md` | `2026-08-21.md` |
| Lecture note | `NN - Topic Name.md` | `01 - Konsep Dasar SDLC.md` |
| Assignment | `Tugas N - Title.md` | `Tugas 2 - Rencana Desain.md` |
| MOC | `00 - Index.md` | `00 - Index.md` |
| Concept | `Concept Name.md` | `SDLC.md`, `Enterprise Architecture.md` |
| Other | `Title Name.md` | `Sleep Tracker.md`, `KRS Plan.md` |

### File Names — NEVER use

- Auto-slug filenames: `innovation-management-and-new-product-developmentfile.md`
- IDs in filenames: `course-10929-material.md`
- Underscores: `my_note.md` (use spaces or kebab-case)
- All lowercase without structure: `notes.md`

## Canonical Folder Structure

```
/
+-- Academic/
|   +-- Current/                          <- ACTIVE semester only
|   |   +-- {Code} - {Full Name}/         <- e.g. SII213 - Inovasi SI dan Teknologi
|   |       +-- Materials/                <- lecture slides, readings
|   |       +-- Assignments/              <- tugas, resume, laporan
|   |       +-- Notes/                    <- personal lecture notes
|   |       +-- README.md                 <- course overview + links
|   +-- Archive/                          <- past semesters
|   |   +-- {Year} {Period}/             <- e.g. 2025 Genap
|   |       +-- {Code} - {Full Name}/    <- same sub-structure
|   +-- BBK/                              <- BBK guide & artifacts
|   +-- KRS/                              <- KRS plans & war logs
|   +-- Schedule/                         <- jadwal kuliah
|   +-- UACC/                             <- UACC SSO portal analysis
|   |   +-- UACC Portal Overview.md       <- portal structure + graph
|   |   +-- Pages/                        <- per-page analysis notes
|   |   +-- Workflow.md                   <- login + analysis workflow
|   +-- HEBAT/                            <- HEBAT Moodle portal
|   +-- Cyber Campus/                     <- Cyber Campus (mahasiswa.unair.ac.id)
|   +-- QA/                               <- QA portal (qa.unair.ac.id)
|
+-- Knowledge/                            <- permanent, reusable knowledge
|   +-- Notes/                            <- Zettelkasten-style atomic notes
|   +-- Concepts/                         <- concept definitions
|   +-- Literature/                       <- paper summaries, book notes
|   +-- Sources/                          <- source metadata for citation
|
+-- Learning/                             <- active learning materials
|   +-- {Topic Name}/                     <- e.g. Machine Learning, SDLC
|   +-- Roadmaps/                         <- learning roadmaps
|   +-- Sessions/                         <- study session logs
|
+-- Life/                                 <- personal life management
|   +-- Goals/                            <- life goals & reviews
|   +-- Habits/                           <- habit tracking
|   +-- Health/                           <- workout, sleep, health
|   +-- Finance/                          <- money logs
|
+-- Research/                             <- research outputs
|   +-- Manifests/                        <- research manifests
|   +-- Reports/                          <- research reports & briefs
|
+-- Projects/                             <- project documentation
|   +-- {Project Name}/                   <- e.g. BEM UNAIR 2026
|
+-- Inbox/                                <- unprocessed captures
+-- Archive/                              <- completed/moved items
+-- Templates/                            <- note templates
+-- Daily/                                <- daily notes (YYYY-MM-DD.md only)
+-- System/                               <- logs, checkpoints, config
```

## Course Reference

### 2026 Ganjil (Active)
| Code | Full Name |
|------|-----------|
| SIA301 | Perencanaan Arsitektur Perusahaan |
| SIA302 | PPA Praktikum |
| SID303 | Analisis dan Visualisasi Data |
| SID304 | AVD Praktikum |
| SII208 | Desain Interaksi |
| SII209 | Desain Interaksi Praktikum |
| SII213 | Inovasi Sistem Informasi dan Teknologi |
| SII318 | Pembangunan Perangkat Lunak |
| SII319 | PPL Praktikum |
| MNW409 | Kewirausahaan dan Bisnis SI |
| BAE112 | Bahasa Inggris II |

### 2025 Genap (Archive)
| Code | Full Name |
|------|-----------|
| MNM203 | Kepemimpinan dan Manajemen Organisasi |
| SIC201 | Pembelajaran Mesin |
| SIC202 | Pembelajaran Mesin Praktikum |
| SII301 | Analisis dan Perancangan Sistem Informasi |
| SII316 | APSI Praktikum |
| SIJ202 | Jaringan Komputer |
| SIJ206 | Jaringan Komputer Praktikum |
| SIS202 | Sistem Enterprise |
| SIS304 | Pemrograman Mobile |
| SIS305 | Pemrograman Mobile Praktikum |

## Orchestration Workflows

### 1. Vault Health Check
Run when: periodic review, before big changes, user asks "cek vault".
```
Steps:
1. xninetzy_obsidian_folder_status -> total notes, missing structure, duplicates
2. xninetzy_obsidian_list (each top-level folder) -> check for misplaced files
3. xninetzy_obsidian_todos -> find orphaned todos
4. xninetzy_obsidian_search_health -> FTS index health
5. Report: file count per folder, naming violations, misplaced notes, health status
```

### 2. Create Course Structure
Run when: new course appears in HEBAT, user asks "siapkan folder course X".
```
Steps:
1. xninetzy_hebat_list_courses(query=courseCode) -> get course info
2. Determine folder name: "{Code} - {Full Name}"
3. Create: Academic/Current/{Code} - {Full Name}/Materials/
4. Create: Academic/Current/{Code} - {Full Name}/Assignments/
5. Create: Academic/Current/{Code} - {Full Name}/Notes/
6. Create README.md with course overview, links, schedule
7. Add frontmatter: course_code, course_name, semester, status
```

### 3. Migrate Notes
Run when: notes are in wrong folders, reorganization needed.
```
Steps:
1. xninetzy_obsidian_organize_preview -> show what will move where
2. Present migration plan to user for approval
3. For each note to move:
   a. xninetzy_obsidian_read (source)
   b. xninetzy_obsidian_create (destination, same content)
   c. Update frontmatter: path, moved_from, moved_at
4. Verify: re-check folder_status, update MOCs
```

### 4. Archive Semester
Run when: semester ends, user asks "arsipkan semester X".
```
Steps:
1. List all courses in Academic/Current/
2. Create Academic/Archive/{Year} {Period}/
3. Move each course folder to Archive
4. Update frontmatter: status=archived, archived_at
5. Regenerate Academic MOC
```

### 5. Generate/Refresh MOCs
Run when: after migration, periodic refresh, user asks "refresh MOC".
```
Steps:
1. xninetzy_obsidian_moc_refresh -> regenerate root MOCs
2. For each major folder, generate/update {Folder}-MOC.md
3. Ensure all notes are linked from at least one MOC
4. Report: orphaned notes (not in any MOC)
```

### 6. Fix Naming Violations
Run when: health check finds violations, user asks "perbaiki naming".
```
Steps:
1. Scan all folders/files for naming convention violations
2. Common issues:
   - Course folders with IDs or slugs -> rename to "{Code} - {Full Name}"
   - Files with auto-slug names -> rename to descriptive name
   - Files with spaces in wrong places -> rename properly
3. Present fix plan to user
4. Execute renames (read -> create -> delete old)
5. Update all backlinks and MOCs
```

### 7. Portal Analysis → Obsidian
Run when: web_analysis + discovery completed for a portal, user asks "simpan ke Obsidian" or "orchestrate portal X".
```
Steps:
1. Read analysis data: analysis.json + analisis_web.md from cache
2. Create folder: Academic/{PortalName}/
3. Create main note: Academic/{PortalName}/{PortalName} Portal Overview.md
   - Frontmatter: tags, aliases, created, source
   - Overview table (URL, login page, CAPTCHA type, session, last analysis)
   - Pages detected with selectors + fields
   - Mermaid diagram of portal structure
   - Protection flags (no auto-CAPTCHA, encrypted session)
   - Workflow steps
   - Links to other portals
   - Changelog
4. Create per-page notes if 3+ pages: Academic/{PortalName}/Pages/{page_path}.md
5. Link to graph: verify graph_v3_search returns portal node
6. Update Academic MOC if exists
```

Portal naming convention:
| Portal | Folder | Notes |
|--------|--------|-------|
| UACC | `Academic/UACC/` | SSO portal, math CAPTCHA |
| HEBAT | `Academic/HEBAT/` | Moodle LMS |
| Cyber Campus | `Academic/Cyber Campus/` | mahasiswa.unair.ac.id |
| QA | `Academic/QA/` | Questionnaire portal |

## Frontmatter Standards

Every note should have minimal frontmatter:
```yaml
---
type: note|concept|material|assignment|daily|moc
course: COURSE_CODE        # if academic
course_name: FULL_NAME     # if academic
semester: "YYYY Period"    # if academic (e.g. "2026 Ganjil")
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active|archived|draft
---
```

## Visualization Standard (Mermaid)

Explanatory notes that describe a process, architecture, hierarchy,
lifecycle, or timeline MUST include at least one Mermaid diagram. ASCII art
is not a substitute. Pick the first matching type:

| Content shape | Diagram type |
|------|--------------|
| System components & connections | `flowchart TB` / `flowchart LR` with `subgraph` per layer |
| Sequential stages / lifecycle | `flowchart LR`; highlight human gates with `classDef` |
| Phased plan WITHOUT official dates | `timeline` (never fabricate gantt dates) |
| Scheduled plan WITH official dates | `gantt` |
| Interactions between actors | `sequenceDiagram` |
| Domain entities & relations | `erDiagram` |

Syntax rules (Obsidian renders ```mermaid fenced blocks natively):

1. Quote every label containing spaces or special characters: `A["Label"]`.
2. Line breaks inside labels use `<br/>`; never put raw `|` inside label text.
3. Group more than ~8 nodes into subgraphs; keep one diagram under ~15 nodes.
4. Place the block directly under the heading it illustrates, preceded by one
   caption sentence.
5. Prefer several small diagrams over one giant diagram.
6. MOC/index notes stay lean — no diagrams unless they aid navigation.

## Anti-Patterns (DO NOT)

- Do NOT use numeric IDs in folder/file names (`10929`, `10924`)
- Do NOT use auto-generated slugs (`2025genap-sic201-pembelajaran-mesin-*`)
- Do NOT use non-representative abbreviations (`pm`, `jk`, `se`)
- Do NOT mix current and archived semesters in Academic/Current/
- Do NOT put non-daily files in Daily/
- Do NOT create notes without frontmatter
- Do NOT create nested folders deeper than 4 levels
- Do NOT skip MOC generation after creating 5+ notes in a folder
- Do NOT draw architecture/process/lifecycle/timeline as ASCII art when a
  Mermaid diagram applies
- Do NOT fabricate dates in gantt charts when no official schedule exists
  (use `timeline` instead)

## Completion Contract

After any orchestration action, report:
- Folders created/renamed/moved (with full human-readable names)
- Files created/moved/renamed
- MOCs updated
- Naming violations fixed
- Health status after change
- Any notes that could not be moved (with reason)
