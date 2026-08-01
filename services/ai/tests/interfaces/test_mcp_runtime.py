from __future__ import annotations

from pathlib import Path

import pytest

from app.xninetzy.interfaces.mcp_runtime import configure_mcp_runtime_paths


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
