from __future__ import annotations

import pytest

from xninetzy.context.intake.layout import (
    LAYOUT_FILE_CAPABILITIES,
    LAYOUT_FILE_MANIFEST_DOCKER,
    LAYOUT_FILE_MANIFEST_NPM,
    LAYOUT_FILE_MANIFEST_PYTHON,
    LAYOUT_FILE_README,
    collect_layout,
)


def _write(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collect_layout_reads_readme_and_pyproject(tmp_path):
    _write(tmp_path / "README.md", "# hello")
    _write(tmp_path / "pyproject.toml", "[project]\nname='x'")
    layout = collect_layout(tmp_path)
    assert layout.has(LAYOUT_FILE_README)
    assert layout.has(LAYOUT_FILE_MANIFEST_PYTHON)
    assert not layout.has(LAYOUT_FILE_MANIFEST_DOCKER)


def test_collect_layout_finds_capability_manifest(tmp_path):
    _write(tmp_path / "mcp_capabilities.json", '{"tools": ["foo"]}')
    layout = collect_layout(tmp_path)
    assert layout.has(LAYOUT_FILE_CAPABILITIES)


def test_collect_layout_detects_entry_scripts(tmp_path):
    _write(tmp_path / "server.py", "")
    _write(tmp_path / "index.js", "")
    layout = collect_layout(tmp_path)
    paths = [p.name for p in layout.entry_script_paths]
    assert "server.py" in paths
    assert "index.js" in paths


def test_collect_layout_counts_files(tmp_path):
    _write(tmp_path / "a.py", "x")
    _write(tmp_path / "b.py", "yy")
    _write(tmp_path / "nested/c.txt", "zzz")
    layout = collect_layout(tmp_path)
    assert layout.file_count == 3
    assert layout.total_bytes > 0


def test_collect_layout_raises_when_missing(tmp_path):
    with pytest.raises(ValueError):
        collect_layout(tmp_path / "definitely-not-here")


def test_collect_layout_finds_docker(tmp_path):
    _write(tmp_path / "Dockerfile", "FROM python:3.11")
    layout = collect_layout(tmp_path)
    assert layout.has(LAYOUT_FILE_MANIFEST_DOCKER)


def test_collect_layout_finds_npm_manifest(tmp_path):
    _write(tmp_path / "package.json", '{"name": "x"}')
    layout = collect_layout(tmp_path)
    assert layout.has(LAYOUT_FILE_MANIFEST_NPM)
