from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.context.obsidian_ops import (
    find_daily_notes,
    inspect_canvas,
    list_templates,
    run_graph_analysis,
    run_vault_health,
)


@tool
def obsidian_vault_health() -> dict:
    """Run a vault health audit. Reports note count, broken-link targets,
    orphan notes, duplicate titles, and notes missing frontmatter. Read-only."""
    return run_vault_health().to_dict()


@tool
def obsidian_graph_analysis() -> dict:
    """Run a graph analysis on the vault. Returns note count, edge count,
    density, orphans, top-degree hubs, and connected-component count.
    Read-only."""
    return run_graph_analysis().to_dict()


@tool
def obsidian_canvas_inspect(canvas_path: str) -> dict:
    """Inspect an Obsidian Canvas (.canvas, JSON Canvas format). Returns
    node count, edge count, nodes by type, referenced notes, and external
    URLs. Read-only."""
    return inspect_canvas(canvas_path).to_dict()


@tool
def obsidian_template_list() -> dict:
    """Discover templates under the vault's templates directory. Reports
    file name, path, size, detected date/time variables, and YAML
    frontmatter presence. Read-only."""
    return {
        "templates": [t.to_dict() for t in list_templates()],
    }


@tool
def obsidian_daily_notes_list() -> dict:
    """List daily notes (notes whose filename starts with a date). Reports
    path, date, size, modified timestamp, and whether the note contains
    open tasks. Read-only."""
    return {
        "daily_notes": [d.to_dict() for d in find_daily_notes()],
    }
