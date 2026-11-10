from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.interfaces import mcp_runtime
from xninetzy.interfaces.mcp_runtime import configure_mcp_runtime_paths


def test_service_root_uses_package_parent(monkeypatch, tmp_path: Path) -> None:
    package_parent = tmp_path / "site-packages"
    monkeypatch.setattr(
        mcp_runtime, "__file__", str(package_parent / "xninetzy/interfaces/mcp_runtime.py")
    )

    assert mcp_runtime.ai_service_root() == package_parent


@pytest.mark.parametrize("legacy_layout", [False, True])
def test_repository_env_path_supports_flat_and_legacy_layouts(
    tmp_path: Path, legacy_layout: bool
) -> None:
    repo = tmp_path / "repo"
    service_root = repo / "services/ai" if legacy_layout else repo

    assert mcp_runtime.repository_env_path(service_root) == repo / ".env"


def test_flat_layout_resolves_relative_host_paths_inside_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    overrides = configure_mcp_runtime_paths(
        environ={"MCP_HOST_DATA_DIR": "runtime", "MCP_HOST_SQLITE_PATH": "runtime/owner.db"},
        env_file_values={},
        ai_root=repo,
        force_host=True,
    )

    assert overrides["DATA_DIR"] == str(repo / "runtime")
    assert overrides["SQLITE_PATH"] == str(repo / "runtime/owner.db")


def test_default_host_mapping_uses_flat_checkout(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setattr(mcp_runtime, "__file__", str(repo / "xninetzy/interfaces/mcp_runtime.py"))
    overrides = configure_mcp_runtime_paths(
        environ={}, env_file_values={}, force_host=True
    )

    assert overrides["DATA_DIR"] == str(repo / "data")
    assert overrides["SQLITE_PATH"] == str(repo / "data/xninetzy.sqlite3")


@pytest.mark.parametrize("checkout_store_exists", [False, True])
def test_implicit_root_change_requires_explicit_store_selection(
    tmp_path: Path, checkout_store_exists: bool
) -> None:
    repo = tmp_path / "repo"
    legacy_store = tmp_path / "data/xninetzy.sqlite3"
    legacy_store.parent.mkdir()
    legacy_store.touch()
    if checkout_store_exists:
        checkout_store = repo / "data/xninetzy.sqlite3"
        checkout_store.parent.mkdir(parents=True)
        checkout_store.touch()
    environ: dict[str, str] = {}

    with pytest.raises(ValueError, match="MCP_HOST_DATA_DIR.*MCP_HOST_SQLITE_PATH"):
        configure_mcp_runtime_paths(
            environ=environ, env_file_values={}, ai_root=repo, force_host=True
        )

    assert environ == {}
    assert legacy_store.exists()


@pytest.mark.parametrize("file_setting", ["MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH", "SQLITE_PATH"])
def test_newly_discovered_env_file_cannot_silently_select_different_store(
    tmp_path: Path, file_setting: str
) -> None:
    repo = tmp_path / "repo"
    legacy_store = tmp_path / "data/xninetzy.sqlite3"
    legacy_store.parent.mkdir()
    legacy_store.touch()

    with pytest.raises(ValueError, match="MCP_HOST_DATA_DIR.*MCP_HOST_SQLITE_PATH"):
        configure_mcp_runtime_paths(
            environ={},
            env_file_values={file_setting: str(repo / "new-store")},
            ai_root=repo,
            force_host=True,
        )


@pytest.mark.parametrize("explicit_setting", ["MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH", "SQLITE_PATH"])
def test_explicit_store_selection_is_preserved_when_legacy_store_exists(
    tmp_path: Path, explicit_setting: str
) -> None:
    repo = tmp_path / "repo"
    legacy_store = tmp_path / "data/xninetzy.sqlite3"
    legacy_store.parent.mkdir()
    legacy_store.touch()
    selection = repo / "chosen"
    environ = {explicit_setting: str(selection)}

    overrides = configure_mcp_runtime_paths(
        environ=environ, env_file_values={}, ai_root=repo, force_host=True
    )

    assert environ[explicit_setting] == str(selection)
    if explicit_setting == "MCP_HOST_DATA_DIR":
        assert overrides["SQLITE_PATH"] == str(selection / "xninetzy.sqlite3")
    elif explicit_setting == "MCP_HOST_SQLITE_PATH":
        assert overrides["SQLITE_PATH"] == str(selection)
    else:
        assert "SQLITE_PATH" not in overrides


def test_host_runtime_maps_container_paths_into_service_data(tmp_path: Path) -> None:
    ai_root = tmp_path / "repo" / "services" / "ai"
    ai_root.mkdir(parents=True)
    environ: dict[str, str] = {}
    env_file = {
        "MCP_RUNTIME_MODE": "auto",
        "DATA_DIR": "/app/data",
        "SQLITE_PATH": "/app/data/xninetzy.sqlite3",
        "VECTOR_DATA_DIR": "/app/data/vector",
        "GRAPH_VECTOR_DATA_DIR": "/app/data/graph_vector",
        "WEB_ANALYSIS_DATA_DIR": "/app/data/web-analysis",
        "HEBAT_DATA_DIR": "/app/data/hebat",
        "HEBAT_DOWNLOAD_DIR": "/app/data/hebat/downloads",
    }

    overrides = configure_mcp_runtime_paths(
        environ=environ,
        env_file_values=env_file,
        ai_root=ai_root,
        force_host=True,
    )

    assert overrides["DATA_DIR"] == str(ai_root / "data")
    assert overrides["SQLITE_PATH"] == str(ai_root / "data/xninetzy.sqlite3")
    assert overrides["VECTOR_DATA_DIR"] == str(ai_root / "data/vector")
    assert overrides["GRAPH_VECTOR_DATA_DIR"] == str(ai_root / "data/graph_vector")
    assert overrides["HEBAT_DOWNLOAD_DIR"] == str(ai_root / "data/hebat/downloads")
    assert environ["SQLITE_PATH"] == overrides["SQLITE_PATH"]


def test_host_runtime_preserves_explicit_host_paths(tmp_path: Path) -> None:
    ai_root = tmp_path / "repo" / "services" / "ai"
    custom_db = tmp_path / "custom" / "xninetzy.sqlite3"
    environ = {"SQLITE_PATH": str(custom_db)}

    overrides = configure_mcp_runtime_paths(
        environ=environ,
        env_file_values={"DATA_DIR": "/app/data"},
        ai_root=ai_root,
        force_host=True,
    )

    assert "SQLITE_PATH" not in overrides
    assert environ["SQLITE_PATH"] == str(custom_db)


def test_container_mode_preserves_container_paths(tmp_path: Path) -> None:
    environ: dict[str, str] = {}
    overrides = configure_mcp_runtime_paths(
        environ=environ,
        env_file_values={
            "MCP_RUNTIME_MODE": "container",
            "SQLITE_PATH": "/app/data/xninetzy.sqlite3",
        },
        ai_root=tmp_path / "services/ai",
        force_host=True,
    )

    assert overrides == {}
    assert "SQLITE_PATH" not in environ


def test_invalid_runtime_mode_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="MCP_RUNTIME_MODE"):
        configure_mcp_runtime_paths(
            environ={},
            env_file_values={"MCP_RUNTIME_MODE": "invalid"},
            ai_root=tmp_path / "services/ai",
            force_host=True,
        )
