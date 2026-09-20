---
layout: ../../layouts/DocsLayout.astro
title: Obsidian vault operations
description: Read-only vault health, graph analysis, canvas inspection, template discovery, and daily-note discovery.
section: Operations
badge: Reference
difficulty: intermediate
readingTime: 8 min
---

The **Obsidian Ops** layer sits next to the existing
`obsidian_*` tools (CRUD, search, todos, backlinks). It adds
**vault-level read-only capabilities** — health, graph, canvas,
templates, daily notes — without coupling to any single Obsidian
plugin or external MCP.

```text
VAULT (filesystem)
  ↓
xninetzy/context/obsidian_ops/
  ├── vault_health      (broken links, orphans, duplicates, missing frontmatter)
  ├── graph_analysis    (edges, density, hubs, connected components)
  ├── canvas_inspect    (JSON Canvas parsing, node/edge counts, refs)
  ├── template_discover (variables, date/time, frontmatter presence)
  └── daily_notes       (date-filename match, open-task detection)
```

All five modules are **read-only**. They never modify the vault.

## 1. Vault health

`obsidian_vault_health()` returns:

- `note_count`
- `broken_link_targets` (links to non-existent notes)
- `orphan_notes` (no incoming links)
- `duplicate_titles` (frontmatter `title` shared by ≥ 2 notes)
- `notes_without_frontmatter`
- `issues` (severity-tagged: high / medium / low)

Frontmatter parser handles YAML subset (`key: value`, list items).

## 2. Graph analysis

`obsidian_graph_analysis()` returns:

- `note_count`, `edge_count`
- `density` (edges / max possible)
- `orphans` (no in or out links)
- `hubs` (top-10 nodes by combined in+out degree)
- `weakly_connected_components` (number of disconnected subgraphs)

Edges derive from `[[wikilinks]]` in note bodies. Aliases and
section/block links are recognized but not fully resolved yet.

## 3. Canvas inspection

`obsidian_canvas_inspect(canvas_path)` parses JSON Canvas format
and returns:

- `node_count`, `edge_count`
- `nodes_by_type` (`text`, `file`, `web`, `group`, `link`)
- `references_to_notes` (extracted from `[[wikilinks]]` in text nodes
  and `file` references)
- `external_urls` (from web nodes)
- `valid` (true if JSON parsed cleanly)
- `error` (if file missing or malformed)

The inspector preserves the JSON Canvas structure (no rewriting).

## 4. Template discovery

`obsidian_template_list()` walks the `templates/` folder (and any
nested templates folder) and reports per-template:

- `name`, `path`, `size_bytes`
- `uses_date_variables` (matches `{{date …}}`)
- `uses_time_variables` (matches `{{time …}}`)
- `variables` (extracted `{{placeholder}}` names)
- `has_frontmatter`
- `preview` (first 400 chars)

Native Obsidian templates behavior is preserved: the system
**detects** but does not **re-define** the core template engine.

## 5. Daily note discovery

`obsidian_daily_notes_list()` returns every note whose stem starts
with a date in one of these forms:

- `2024-01-15`
- `2024-01-15-daily`
- `15-01-2024`

For each:

- `date` (canonical ISO from regex group 1)
- `path`, `size_bytes`, `modified`
- `has_open_tasks` (matches `- [ ]` anywhere in body)

## 6. MCP tools

| Tool | Read-only | Use |
|---|---|---|
| `obsidian_vault_health` | yes | broken links, orphans, duplicates |
| `obsidian_graph_analysis` | yes | edges, density, hubs |
| `obsidian_canvas_inspect` | yes | `.canvas` parsing |
| `obsidian_template_list` | yes | template discovery |
| `obsidian_daily_notes_list` | yes | date-based note list |

Total registered tools: **406** (audit-script-verified).

## 7. Skill

`.agents/skills/obsidian-ops/SKILL.md` enforces:

- always read-only
- never claim a fix without owner confirmation
- never fabricate link/canvas/template data
- surface `note_count == 0` as a path problem, not as "no notes"

## 8. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` | Absolute vault root |

All five tools read this path via `xninetzy.core.config.get_settings()`.

## 9. Failure containment

| Failure | Behavior |
|---|---|
| Vault path missing or empty | `note_count=0`, no issues, no orphans |
| Malformed JSON Canvas | `valid=false`, `error="invalid JSON: …"` |
| Frontmatter without `:` | silently skipped; parser falls back to `{}` |
| Template folder missing | returns `{"templates": []}` |
| Daily note with non-standard name | not included in daily list (caller decides) |

## 10. Tests

`tests/obsidian_ops/` covers:

- vault health (broken links, orphans, duplicates, missing frontmatter)
- graph analysis (density, hubs, components)
- canvas inspection (valid JSON, malformed JSON, missing file)
- template discovery (date/time variables, frontmatter)
- daily note detection (multiple date formats)
