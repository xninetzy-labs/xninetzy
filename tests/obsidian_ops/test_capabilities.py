from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from xninetzy.context.obsidian_ops import (
    find_daily_notes,
    inspect_canvas,
    list_templates,
    run_graph_analysis,
    run_vault_health,
)


@pytest.fixture
def vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path))
    from xninetzy.core import config as cfg

    cfg.get_settings.cache_clear()
    return tmp_path


def _write(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_vault_health_detects_broken_links(vault: Path) -> None:
    _write(vault, "a.md", "# A\nlinks to [[B]] and [[Ghost]].\n")
    _write(vault, "b.md", "# B\n")
    report = run_vault_health()
    assert report.note_count == 2
    assert "Ghost" in report.broken_link_targets


def test_vault_health_detects_orphans(vault: Path) -> None:
    _write(vault, "a.md", "# A")
    _write(vault, "b.md", "# B")
    report = run_vault_health()
    assert len(report.orphan_notes) == 2


def test_vault_health_detects_duplicate_titles(vault: Path) -> None:
    _write(vault, "a.md", "---\ntitle: same\n---\nA")
    _write(vault, "b.md", "---\ntitle: same\n---\nB")
    report = run_vault_health()
    titles = [t for t, _ in report.duplicate_titles]
    assert "same" in titles


def test_vault_health_detects_missing_frontmatter(vault: Path) -> None:
    _write(vault, "no_fm.md", "# No frontmatter")
    _write(vault, "with_fm.md", "---\ntitle: ok\n---\nok")
    report = run_vault_health()
    rel = lambda p: str(Path("no_fm.md"))
    assert any(rel(p) == "no_fm.md" for p in report.notes_without_frontmatter)


def test_graph_analysis_counts_edges_and_density(vault: Path) -> None:
    _write(vault, "a.md", "links [[b]]")
    _write(vault, "b.md", "links [[a]]")
    g = run_graph_analysis()
    assert g.note_count == 2
    assert g.edge_count == 2


def test_graph_analysis_detects_hub(vault: Path) -> None:
    _write(vault, "hub.md", "x")
    for i in range(3):
        _write(vault, f"leaf{i}.md", f"links [[hub]]")
    g = run_graph_analysis()
    hub_names = [name for name, _ in g.hubs]
    assert "hub" in hub_names


def test_canvas_inspect_parses_valid_json(vault: Path) -> None:
    payload = {
        "nodes": [
            {"id": "1", "type": "text", "text": "see [[a]]"},
            {"id": "2", "type": "file", "file": "a.md"},
            {"id": "3", "type": "web", "url": "https://example.com"},
        ],
        "edges": [{"idNode": "1", "idNode2": "2"}],
    }
    _write(vault, "c.canvas", json.dumps(payload))
    report = inspect_canvas("c.canvas", vault_root=vault)
    assert report.valid
    assert report.node_count == 3
    assert report.edge_count == 1
    assert "a" in report.references_to_notes


def test_canvas_inspect_reports_malformed(vault: Path) -> None:
    _write(vault, "bad.canvas", "{not json")
    report = inspect_canvas("bad.canvas", vault_root=vault)
    assert report.valid is False
    assert "invalid JSON" in (report.error or "")


def test_canvas_inspect_reports_missing(vault: Path) -> None:
    report = inspect_canvas("missing.canvas", vault_root=vault)
    assert report.valid is False
    assert "not found" in (report.error or "")


def test_template_discover_detects_date_and_time(vault: Path) -> None:
    (vault / "templates").mkdir()
    _write(
        vault,
        "templates/daily.md",
        "---\ntitle: {{date}}\n---\n# {{title}} at {{time}}",
    )
    t = list_templates()[0]
    assert t.uses_date_variables is True
    assert t.uses_time_variables is True
    assert "date" in t.variables


def test_daily_notes_list_matches_iso_date(vault: Path) -> None:
    _write(vault, "2024-03-15.md", "# day\n- [ ] task")
    _write(vault, "2024-03-16-daily.md", "no task")
    notes = find_daily_notes()
    dates = [n.date for n in notes]
    assert "2024-03-15" in dates
    assert "2024-03-16" in dates
    assert notes[0].date == "2024-03-16"
    assert next(n for n in notes if n.date == "2024-03-15").has_open_tasks is True


def test_empty_vault_returns_zero(vault: Path) -> None:
    report = run_vault_health()
    assert report.note_count == 0
    assert report.issues == ()
