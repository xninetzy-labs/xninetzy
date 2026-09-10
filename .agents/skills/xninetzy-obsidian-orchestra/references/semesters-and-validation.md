# Xninetzy Obsidian Orchestra — Semesters and Validation

This reference expands current vs archive boundary, semester transition, structural vs content operations, safe mutation model, semester archives, completion contract, standard health output, and operating rules. Read it when handling semester transitions or producing the closing health report.

## Current vs archive boundary

`Academic/Current/` contains only active-semester courses. `Academic/Archive/` contains previous semesters. Never mix active and archived semesters. When a semester ends:

```text
Current
 ↓
Archive/{Year} {Period}
```

Preserve course identity and internal structure.

## Semester transition

At semester transition:

1. determine the active semester,
2. identify courses still belonging to the current term,
3. verify no active course remains incorrectly archived,
4. create the destination archive,
5. move complete course structures,
6. update frontmatter,
7. refresh Academic MOC,
8. verify Current contains only active courses.

Do not archive a course merely because its last note is old.

## Structural vs content operations

This skill owns: **where a note lives and how the vault is structured.** It does not automatically own: **what the note says.**

When content must be read deeply, route to the note-content/knowledge capability. When content must be generated or rewritten, use the appropriate writing/artifact workflow.

## Safe mutation model

Structural mutations should follow:

```text
inspect
↓
preview
↓
approval when material
↓
execute
↓
verify
```

Approval is especially appropriate for:

* mass migration,
* bulk renaming,
* large archive operations,
* destructive cleanup,
* duplicate merging,
* restructuring multiple top-level areas.

## Health report

Return:

```text
Folder Health
Naming Violations
Misplaced Notes
Duplicate Candidates
Orphaned Notes
Missing Frontmatter
MOC Issues
Index Health
Overall Status
Recommended Next Action
```

Do not claim "healthy" if critical checks were skipped.

## Vault health check

Run health checks for:

* folder structure,
* naming violations,
* misplaced files,
* duplicate notes,
* orphaned TODOs,
* broken references,
* missing frontmatter,
* FTS/index health,
* excessive nesting,
* stale MOCs.

Suggested workflow:

```text
folder status
→ top-level inspection
→ TODO/orphan check
→ search/index health
→ naming scan
→ structural report
```

## Completion contract

After any orchestration action, report the relevant subset of:

**Folders created/renamed/moved** — use full human-readable paths.

**Files created/moved/renamed** — include exact paths.

**MOCs updated** — identify affected indexes.

**Naming violations fixed** — state what changed.

**Frontmatter changes** — when structural metadata was modified.

**Health status** — what was actually checked.

**Unresolved items** — notes that could not be moved, renamed, indexed, or verified, with reasons.

**Approval status** — whether the action was merely proposed, approved, or completed.

**Next action** — one bounded structural step if anything remains.

## Standard health output

```text
Vault Scope
Structural Status
Naming Status
Frontmatter Status
MOC Status
Orphan / Misplaced Notes
Broken References
Index Health
Unresolved Issues
Next Action
```

## Checkpoint integration

For material structural changes, persist a checkpoint with the goal, scope, completed stages, exact paths, important decisions, version, health state, unresolved items, and next action. Use the Memory Chat system when persistence is required.

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

The canonical lifecycle is:

**Inspect → Classify → Plan → Preview → Approve → Mutate → Verify → Index → Checkpoint**