"""Resolve container-oriented Xninetzy paths when MCP runs on the host."""

from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path

from dotenv import dotenv_values

_CONTAINER_PATHS = {
    "DATA_DIR": "data",
    "SQLITE_PATH": "data/xninetzy.sqlite3",
    "VECTOR_DATA_DIR": "data/vector",
    "WEB_ANALYSIS_DATA_DIR": "data/web-analysis",
    "HEBAT_DATA_DIR": "data/hebat",
    "HEBAT_DOWNLOAD_DIR": "data/hebat/downloads",
    "XNINETZY_SKILLS_DIR": "data/opencode-config/opencode/skills",
}
_VALID_MODES = {"auto", "host", "container"}


def ai_service_root() -> Path:
    """Return the absolute ``services/ai`` directory."""
    return Path(__file__).resolve().parents[3]


def repository_env_path(ai_root: Path | None = None) -> Path:
    """Return the root .env path for a normal monorepo checkout."""
    root = (ai_root or ai_service_root()).resolve()
    return root.parents[1] / ".env"


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {
        str(key): str(value)
        for key, value in dotenv_values(path).items()
        if value is not None
    }


def _effective_value(
    name: str,
    environ: Mapping[str, str],
    env_file_values: Mapping[str, str],
) -> str:
    return (environ.get(name) or env_file_values.get(name) or "").strip()


def _is_container_path(value: str, app_root: Path) -> bool:
    if not value:
        return True
    path = Path(value).expanduser()
    if not path.is_absolute():
        return False
    try:
        path.relative_to(app_root)
    except ValueError:
        return False
    return True


def _resolve_host_path(value: str, ai_root: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ai_root.parents[1] / path
    return path.resolve()


def configure_mcp_runtime_paths(
    *,
    environ: MutableMapping[str, str] | None = None,
    env_file_values: Mapping[str, str] | None = None,
    ai_root: Path | None = None,
    app_root: Path = Path("/app"),
    force_host: bool | None = None,
) -> dict[str, str]:
    """Apply host-safe path overrides before Pydantic Settings is imported.

    Xninetzy's root ``.env`` is shared by Docker and host clients. Docker uses
    ``/app/data`` while project-scoped MCP servers run on the host. In ``auto``
    mode, container paths are mapped into ``services/ai/data`` only when
    ``/app`` is unavailable or not writable. Explicit non-container paths are
    always preserved.

    Returns only the overrides that were applied, which keeps the resolver easy
    to inspect and unit test.
    """

    target_env = environ if environ is not None else os.environ
    service_root = (ai_root or ai_service_root()).resolve()
    file_values = (
        dict(env_file_values)
        if env_file_values is not None
        else _read_env_file(repository_env_path(service_root))
    )

    mode = (
        _effective_value("MCP_RUNTIME_MODE", target_env, file_values) or "auto"
    ).lower()
    if mode not in _VALID_MODES:
        raise ValueError(
            "MCP_RUNTIME_MODE harus salah satu dari: auto, host, container."
        )

    use_host = force_host
    if use_host is None:
        use_host = mode == "host" or (
            mode == "auto"
            and (not app_root.is_dir() or not os.access(app_root, os.W_OK))
        )
    if mode == "container":
        use_host = False
    if not use_host:
        return {}

    configured_host_base = _effective_value(
        "MCP_HOST_DATA_DIR", target_env, file_values
    )
    host_base = (
        _resolve_host_path(configured_host_base, service_root)
        if configured_host_base
        else (service_root / "data").resolve()
    )
    configured_sqlite = _effective_value(
        "MCP_HOST_SQLITE_PATH", target_env, file_values
    )
    sqlite_path = (
        _resolve_host_path(configured_sqlite, service_root)
        if configured_sqlite
        else host_base / "xninetzy.sqlite3"
    )

    destinations = {
        key: str(host_base / Path(relative).relative_to("data"))
        for key, relative in _CONTAINER_PATHS.items()
        if key not in {"DATA_DIR", "SQLITE_PATH"}
    }
    destinations["DATA_DIR"] = str(host_base)
    destinations["SQLITE_PATH"] = str(sqlite_path)

    overrides: dict[str, str] = {}
    resolved_app_root = app_root.resolve()
    for name, destination in destinations.items():
        current = _effective_value(name, target_env, file_values)
        if not _is_container_path(current, resolved_app_root):
            continue
        target_env[name] = destination
        overrides[name] = destination
    return overrides


MCP_PATH_OVERRIDES = configure_mcp_runtime_paths()
