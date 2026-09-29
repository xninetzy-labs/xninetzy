from __future__ import annotations

import pytest

from xninetzy.core.config import get_settings
from xninetzy.core.paths import (
    ArtifactPathError,
    is_within_artifact_roots,
    resolve_artifact_output,
)


@pytest.fixture()
def artifact_root(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    for key in (
        "OUTPUT_DIR",
        "GENERATED_DOCUMENTS_DIR",
        "RESEARCH_OUTPUT_DIR",
        "UNTRACKED_OUTPUT_DIR",
        "VIDEO_OUTPUT_DIR",
        "DATA_DIR",
    ):
        monkeypatch.setenv(key, str(root))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "true")
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_write_inside_root_is_allowed(artifact_root):
    target = artifact_root / "sub" / "out.xlsx"
    resolved = resolve_artifact_output(target, create_parents=True)
    assert str(resolved).startswith(str(artifact_root.resolve()))
    assert resolved.parent.is_dir()


def test_write_outside_roots_is_blocked(artifact_root, tmp_path):
    victim = tmp_path / "outside" / "evil.txt"
    with pytest.raises(ArtifactPathError):
        resolve_artifact_output(victim)
    assert not victim.exists()


def test_traversal_escape_is_blocked(artifact_root):
    assert not is_within_artifact_roots(artifact_root / ".." / "escape.txt")


def test_allowlist_disabled_permits_any_path(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "false")
    get_settings.cache_clear()
    try:
        target = tmp_path / "anywhere" / "x.txt"
        resolved = resolve_artifact_output(target)
        assert resolved == target.resolve()
    finally:
        get_settings.cache_clear()


def test_data_generate_xlsx_rejects_escape(artifact_root, tmp_path):
    from xninetzy.tools.internal.data_analysis import data_generate_xlsx

    victim = tmp_path / "outside" / "leak.xlsx"
    out = data_generate_xlsx.invoke(
        {"output_path": str(victim), "name": "t", "rows": [{"a": 1}]}
    )
    assert "error" in out
    assert not victim.exists()


def test_data_generate_xlsx_writes_inside_root(artifact_root):
    from xninetzy.tools.internal.data_analysis import data_generate_xlsx

    target = artifact_root / "ok.xlsx"
    out = data_generate_xlsx.invoke(
        {"output_path": str(target), "name": "t", "rows": [{"a": 1, "b": 2}]}
    )
    assert "error" not in out
    assert target.exists()
