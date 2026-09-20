---
name: obsidian-ops
description: Use when the user asks for vault health, graph analysis, canvas inspection, template discovery, or daily-note discovery in Obsidian. Read-only operations — never modify the vault without explicit owner confirmation.
metadata:
  type: workflow
  domain: obsidian
  capabilities:
    - obsidian_vault_health
    - obsidian_graph_analysis
    - obsidian_canvas_inspect
    - obsidian_template_list
    - obsidian_daily_notes_list
  version: 1.0.0
---

# Obsidian Ops Workflow

Use this skill when the request is one of:

- "is my vault healthy?" / "audit my notes" / "find broken links"
- "what are my knowledge hubs?" / "show orphan notes"
- "what does this canvas contain?"
- "list my templates" / "what variables do my templates use?"
- "find my daily notes" / "which daily notes have open tasks?"

## Decision tree

```text
user request
   ├── "broken links / orphans / duplicates"     → obsidian_vault_health
   ├── "graph / hubs / connectivity"             → obsidian_graph_analysis
   ├── "canvas content / nodes / references"      → obsidian_canvas_inspect
   ├── "templates / variables"                   → obsidian_template_list
   └── "daily notes list / open tasks"           → obsidian_daily_notes_list
```

## Non-negotiable rules

- All five tools are **READ-ONLY**. They never modify the vault.
- Never claim an issue is fixed without the user explicitly
  authorizing a write operation.
- Never guess vault path; always read `OBSIDIAN_VAULT_HOST_PATH`.
- Never assume the vault exists. If health report shows
  `note_count == 0`, surface that the path may be empty or
  unreachable.
- Never fabricate links, references, or note names. Every report is
  derived from a real walk of the vault directory.
- Treat broken-link targets as **suggestions for repair**, never as
  reasons to delete a note.
