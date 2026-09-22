from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.integrations.tableau.workspace import (
    resolve_template_path,
    safe_workspace_subdir,
    templates_root,
    workspace_root,
)


def test_workspace_root_creates_subdirs(tmp_path: Path) -> None:
    root = workspace_root(override=tmp_path)
    expected = {"templates", "workbooks", "hyper", "twbx", "metadata", "staging", "temp"}
    actual = {p.name for p in root.iterdir() if p.is_dir()}
    assert expected.issubset(actual)


def test_safe_workspace_subdir_strips_traversal() -> None:
    cleaned = safe_workspace_subdir("../etc/passwd")
    assert ".." not in cleaned
    assert "/" not in cleaned


def test_safe_workspace_subdir_strips_absolute() -> None:
    cleaned = safe_workspace_subdir("/abs/path")
    assert not cleaned.startswith("/")
    assert "abs" in cleaned


def test_safe_workspace_subdir_accepts_clean() -> None:
    assert safe_workspace_subdir("workbooks") == "workbooks"


def test_safe_workspace_subdir_returns_nonempty() -> None:
    assert safe_workspace_subdir("") == "default"


def test_resolve_template_path_repo_first() -> None:
    repo_dir = templates_root()
    assert repo_dir.is_dir()
    assert (repo_dir / "Progres1ya.twb").is_file()
    resolved = resolve_template_path("Progres1ya.twb")
    assert resolved.name == "Progres1ya.twb"


def test_resolve_template_path_missing() -> None:
    with pytest.raises(FileNotFoundError):
        resolve_template_path("nonexistent_xyz.twb")
