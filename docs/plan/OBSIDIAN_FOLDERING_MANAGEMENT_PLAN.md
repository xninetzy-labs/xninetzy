# Obsidian Foldering Management

Xninetzy uses one canonical semantic vault layout for WhatsApp, LangGraph, MCP, Codex, Claude Code, and OpenCode. New notes are routed by the shared folder policy; legacy notes remain readable and can be migrated through a dry-run and owner approval.

## Canonical layout

```text
Home.md
Inbox/{Captures,Triage,Unsorted}/
Daily/YYYY/YYYY-MM-DD.md
Learning/{Roadmaps,Concepts,Sessions,Notes,Reviews,MOCs}/
Projects/<project>/README.md
Academic/{HEBAT,Cyber-Campus,QA}/
Research/{Briefs,Sources,Topics,MOCs}/
Life/{Goals,Tasks,Habits,Money,Workouts,Areas,Reviews}/
Knowledge/{Notes,Sources,MOCs}/
Attachments/
System/{MOCs,Templates,Help,Logs,Migration}/
Archive/
```

## Runtime contract

- `folder_policy.py` owns canonical paths, slugging, legacy classification, and metadata defaults.
- `organization_service.py` owns inventory, preview, approval execution, backups, link updates, MOC refresh, and verification.
- `obsidian_organization.py` exposes management tools through the central registry and therefore all interfaces.
- Academic sensitive data is not persisted by default. Runtime downloads and browser/session state stay outside the vault.

## Safe migration

1. Run `obsidian_organize_preview`.
2. Review source, target, source hash, conflicts, and unresolved notes.
3. Request `obsidian_organize_apply`; the owner approves through the existing HITL channel.
4. Apply validates hashes, creates backups, moves notes, updates path-based wikilinks, and reports skipped conflicts.
5. Run `obsidian_verify` and `obsidian_moc_refresh`.

The migration is idempotent. Unknown notes are not moved silently. Existing legacy paths remain readable while `OBSIDIAN_LEGACY_PATH_COMPATIBILITY=true`.

## Metadata

Generated and migrated notes carry `schema_version`, `type`, `title`, `canonical_path`, `created`, `updated`, `status`, `tags`, and optional domain identifiers. Existing unknown frontmatter fields are preserved.

## Documentation localization

Astro documentation defaults to English and provides an English/Indonesia selector in the global header. Pages can provide localized blocks with `data-locale="en"` and `data-locale="id"`; the selector persists the owner preference in browser storage.

## Shared skill installation

Install skills into the shared Xninetzy catalog rather than a client-specific registry:

```text
Use MCP xninetzy to list available skills.
Install the skill named security-threat-model into the shared catalog.
Validate the installed skill and show its resources.
```

The same `skill_list`, `skill_get`, `skill_validate`, `skill_install`, `skill_resource_list`, and `skill_resource_read` tools are available to LangGraph, WhatsApp, Codex, Claude Code, and OpenCode. Built-in skills live under `services/ai/.agents/skills`; installation is owner-scoped, idempotent, and validated before use.
