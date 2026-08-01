from __future__ import annotations

import json

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.notes.obsidian_config import vault_path
from app.xninetzy.tools.internal.obsidian import (
    obsidian_add_tags,
    obsidian_backlinks,
    obsidian_create,
    obsidian_create_folder,
    obsidian_headings,
    obsidian_list,
    obsidian_read,
    obsidian_set_frontmatter,
    obsidian_todos,
    obsidian_update_section,
)


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    host_vault = tmp_path / "vault"
    host_vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing-container-mount"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(host_vault))
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    monkeypatch.setenv("OBSIDIAN_BACKUP_BEFORE_WRITE", "false")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    get_settings.cache_clear()
    init_db()
    yield host_vault
    get_settings.cache_clear()


def test_vault_path_uses_host_path_outside_container(isolated_vault):
    assert vault_path() == isolated_vault.resolve()


def test_agent_tools_can_manage_safe_vault_operations(isolated_vault):
    assert "Folder siap" in obsidian_create_folder.invoke({"path": "Projects"})
    assert "Catatan dibuat" in obsidian_create.invoke(
        {
            "path": "Projects/Project.md",
            "content": "# Project\n\n## Status\nDraft\n\n## Tasks\n- [ ] Ship feature\n",
        }
    )
    assert "diperbarui" in obsidian_update_section.invoke(
        {"path": "Projects/Project.md", "heading": "Status", "content": "Active"}
    )
    assert "Tags diperbarui" in obsidian_add_tags.invoke(
        {"path": "Projects/Project.md", "tags": ["ai", "learning"]}
    )
    assert "Frontmatter diperbarui" in obsidian_set_frontmatter.invoke(
        {"path": "Projects/Project.md", "data": {"owner": "Misbahul"}}
    )
    assert "Catatan dibuat" in obsidian_create.invoke(
        {"path": "Projects/Reference.md", "content": "Related to [[Project]]."}
    )

    listed = json.loads(obsidian_list.invoke({"folder": "Projects"}))
    assert {item["path"] for item in listed} == {
        "Projects/Project.md",
        "Projects/Reference.md",
    }
    headings = json.loads(obsidian_headings.invoke({"path": "Projects/Project.md"}))
    assert any(item["title"] == "Status" for item in headings)
    todos = json.loads(obsidian_todos.invoke({"folder": "Projects"}))
    assert any("Ship feature" in item["text"] for item in todos)
    backlinks = json.loads(
        obsidian_backlinks.invoke({"note_path": "Projects/Project.md"})
    )
    assert any(item["path"] == "Projects/Reference.md" for item in backlinks)

    saved = (isolated_vault / "Projects" / "Project.md").read_text(encoding="utf-8")
    assert "owner: Misbahul" in saved
    assert "tags: [ai, learning]" in saved
    assert "Active" in saved


def test_obsidian_read_accepts_extensionless_and_dotted_paths(isolated_vault):
    daily = isolated_vault / "Daily"
    daily.mkdir()
    (daily / "2026-07-28.md").write_text("# Log\nHari ini belajar N-BEATS.\n", encoding="utf-8")
    projects = isolated_vault / "Projects"
    projects.mkdir()
    (projects / "Project.md").write_text("# Project\nStatus aktif.\n", encoding="utf-8")

    dotted = obsidian_read.invoke({"path": "Daily/2026-07-28"})
    assert "belajar N-BEATS" in dotted

    bare = obsidian_read.invoke({"path": "Projects/Project"})
    assert "Status aktif" in bare

    explicit = obsidian_read.invoke({"path": "Projects/Project.md"})
    assert "Status aktif" in explicit


def test_obsidian_read_missing_note_stays_honest_miss(isolated_vault):
    (isolated_vault / "Daily").mkdir()
    result = obsidian_read.invoke({"path": "Daily/Nonexistent"})
    assert "tidak ditemukan" in result
