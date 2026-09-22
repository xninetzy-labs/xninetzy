from __future__ import annotations

import os
import re
from pathlib import Path

from xninetzy.core.config import expand_path, get_settings


WORKSPACE_ENV = "XNINETZY_TABLEAU_WORKSPACE"
TEMPLATES_ENV = "XNINETZY_TABLEAU_TEMPLATES_DIR"
SUBDIRS = (
    "templates",
    "workbooks",
    "hyper",
    "twbx",
    "metadata",
    "staging",
    "temp",
)


def _output_root() -> Path:
    try:
        return Path(expand_path(str(get_settings().OUTPUT_DIR)))
    except Exception:
        return Path(expand_path("~/Documents/xninetzy/output"))


def workspace_root(override: Path | None = None) -> Path:
    base: Path
    if override is not None:
        base = override
    elif env := os.environ.get(WORKSPACE_ENV):
        base = Path(expand_path(env))
    else:
        base = _output_root() / "tableau"
    base.mkdir(parents=True, exist_ok=True)
    for name in SUBDIRS:
        (base / name).mkdir(parents=True, exist_ok=True)
    return base


def templates_root(override: Path | None = None) -> Path:
    if env := os.environ.get(TEMPLATES_ENV):
        root = Path(expand_path(env))
    else:
        root = _output_root() / "tableau" / "templates"
    root.mkdir(parents=True, exist_ok=True)
    return root


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_workspace_subdir(name: str | None) -> str:
    if not name:
        return "default"
    cleaned = str(name).replace("\\", "/").strip()
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    parts = [p for p in cleaned.split("/") if p not in {"", ".", ".."}]
    if not parts:
        return "default"
    safe = _SAFE_NAME.sub("_", "_".join(parts)).strip("._-")
    if not safe:
        return "default"
    return safe


def resolve_template_path(name: str, workspace: Path | None = None) -> Path:
    candidates: list[Path] = []
    env = os.environ.get(TEMPLATES_ENV)
    if env:
        candidates.append(Path(expand_path(env)))
    candidates.append(_output_root() / "tableau" / "templates")
    repo = Path(__file__).resolve().parents[2] / "templates" / "tableau"
    candidates.append(repo)
    if workspace is not None:
        candidates.append(workspace / "templates")
    for base in candidates:
        path = base / name
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"Tableau template '{name}' not found in any known template root"
    )


__all__ = [
    "workspace_root",
    "templates_root",
    "safe_workspace_subdir",
    "resolve_template_path",
    "WORKSPACE_ENV",
    "TEMPLATES_ENV",
    "SUBDIRS",
]
