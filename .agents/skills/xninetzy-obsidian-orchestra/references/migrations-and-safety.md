# Xninetzy Obsidian Orchestra — Migrations, Naming, and Safety

This reference expands migration workflow, preview, safety, naming repair, conflict resolution, frontmatter normalization, idempotency, duplicate detection, broken-link safety, aliases, anti-patterns, and verification after mutation. Read it when designing or executing a structural change.

## Migration workflow

Structural changes should be safe and inspectable:

```text
Inspect
→ Organize Preview
→ Approval
→ Read
→ Create destination
→ Preserve content
→ Remove/rename source
→ Repair links
→ Refresh MOC
→ Verify
```

Do not move a large set of notes blindly.

## Migration preview

Before a non-trivial migration, show:

| Current Path | Proposed Path | Reason                      | Risk            |
| ------------ | ------------- | --------------------------- | --------------- |
| old path     | new path      | naming/structure correction | low/medium/high |

Preview should clearly identify files affected, destination, naming changes, link implications, and possible conflicts.

## Migration safety

Before moving a note:

1. verify source exists,
2. verify destination does not conflict,
3. preserve content,
4. preserve frontmatter,
5. record original path when useful,
6. update backlinks/references,
7. verify destination,
8. only then remove/rename the source when safe.

Do not delete the source first.

## Naming repair

When naming violations exist:

1. scan,
2. classify violation,
3. calculate canonical name,
4. preview changes,
5. execute approved changes,
6. update references,
7. refresh MOCs,
8. verify.

Do not rename based only on aesthetic preference. A rename must improve canonical retrieval or consistency.

## Conflict resolution during migration

When destination already exists:

```text
source exists
+
destination exists
↓
compare identities
↓
same note?
different notes?
unknown?
```

Possible resolutions:

* merge after inspection,
* rename destination,
* preserve both,
* stop and ask.

Never overwrite a potentially different note automatically.

## Frontmatter rules

* `type` — must describe the note's structural role.
* `course` — required for academic notes.
* `course_name` — required for academic notes when available.
* `semester` — use `YYYY Period`.
* `created` — reflect actual creation date when known.
* `updated` — reflect actual update date.
* `status` — `active | archived | draft`.

Do not silently convert unknown state to active.

## Frontmatter normalization

When repairing frontmatter:

1. preserve meaningful existing metadata,
2. add missing canonical fields,
3. normalize inconsistent values,
4. avoid deleting unknown user metadata without reason,
5. update only fields relevant to structural standards.

Never replace an entire frontmatter block blindly.

## Idempotency

Repeated requests should not create duplicate structures. Before creating:

```text
Does the folder already exist?
Does the README already exist?
Does the MOC already exist?
Is this note already in the destination?
```

Reuse existing structures whenever they match the canonical model.

## Duplicate detection

Possible duplicate signals:

* same canonical title,
* same course + topic,
* same source identity,
* same artifact identity,
* identical or near-identical content.

Do not automatically merge duplicates from weak similarity alone. Flag uncertain duplicate candidates for review.

## Broken-link safety

Before deleting or moving notes, inspect backlinks where supported. If a note has important inbound links:

* update references,
* preserve aliases,
* verify backlinks after migration.

Do not destroy navigation silently.

## Aliases

When a rename changes a note's canonical title but old naming remains useful for retrieval, preserve aliases when appropriate:

```yaml
aliases:
  - Old Course Title
  - Abbreviated Topic
```

Do not accumulate excessive aliases that create ambiguity.

## Nesting limit

Avoid folder structures deeper than four meaningful levels. Deep nesting harms navigation, discoverability, migration safety, and agent retrieval. When deeper nesting appears necessary, first consider a MOC, tags, metadata, links, or a flatter folder structure.

## Anti-patterns

Never:

* use numeric IDs as human-facing names,
* use auto-generated slugs,
* mix archived and active semesters,
* place non-daily files in `Daily/`,
* create managed notes without frontmatter,
* create unnecessarily deep folders,
* skip MOC maintenance after significant structure changes,
* fabricate Mermaid dates,
* use ASCII architecture where Mermaid is appropriate,
* overwrite potentially distinct notes during migration,
* claim health without performing the relevant checks.

## Small vs broad changes

### Small change

Examples: create one missing folder, rename one obviously invalid filename, create one course README. Can follow the available authorization policy.

### Broad change

Examples: migrate 100 notes, redesign the entire vault, merge duplicate knowledge trees, archive a semester, bulk rename folders. Require preview and appropriate approval before mutation.

## Verification after mutation

After any structural change:

1. confirm destination paths,
2. confirm source removal/rename where applicable,
3. inspect relevant folder status,
4. check for broken references,
5. refresh required MOCs,
6. verify frontmatter,
7. report unresolved items.

Do not declare a migration complete because the file-operation command returned successfully.

## Current course reference

The current vault may contain a course registry such as:

```text
SIA301  - Perencanaan Arsitektur Perusahaan
SIA302  - PPA Praktikum
SID303  - Analisis dan Visualisasi Data
SID304  - AVD Praktikum
SII208  - Desain Interaksi
SII209  - Desain Interaksi Praktikum
SII213  - Inovasi Sistem Informasi dan Teknologi
SII318  - Pembangunan Perangkat Lunak
SII319  - PPL Praktikum
MNW409  - Kewirausahaan dan Bisnis SI
BAE112  - Bahasa Inggris II
```

Historical course mappings may also exist. Treat this as a **reference snapshot**, not a timeless source of truth. For current course identity, prefer verified current academic data.