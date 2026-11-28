from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from xninetzy.core.config import expand_path, get_settings

try:
    import fcntl
except ImportError:
    fcntl = None

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
DATASET_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
KERNEL_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorkspaceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {"error_code": self.code, "message": self.message}


def workspace_dir() -> Path:
    path = Path(expand_path(get_settings().KAGGLE_WORKSPACE_DIR)).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def subdir(*parts: str) -> Path:
    path = workspace_dir().joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def source_roots() -> list[Path]:
    roots = [workspace_dir()]
    for raw in get_settings().KAGGLE_SOURCE_ROOTS.split(","):
        value = raw.strip()
        if value:
            roots.append(Path(expand_path(value)).expanduser().resolve())
    return roots


def resolve_source_path(value: str) -> Path:
    candidate = Path(expand_path(value)).expanduser()
    if not candidate.is_absolute():
        candidate = workspace_dir() / candidate
    resolved = candidate.resolve()
    if not any(resolved == root or root in resolved.parents for root in source_roots()):
        raise WorkspaceError(
            "KAGGLE_SOURCE_OUTSIDE_ROOTS",
            "source_path must be inside the Kaggle workspace or a root listed in KAGGLE_SOURCE_ROOTS",
        )
    if not resolved.is_file():
        raise WorkspaceError("KAGGLE_SOURCE_NOT_FOUND", "source_path is not a readable file")
    return resolved


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, default=str)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


@contextmanager
def locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+") as stream:
        if fcntl is not None:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise WorkspaceError("KAGGLE_STATE_LOCKED", "another operation holds this Kaggle state; retry shortly") from None
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(stream, fcntl.LOCK_UN)


def require_pattern(value: str, pattern: re.Pattern[str], code: str, label: str) -> str:
    cleaned = (value or "").strip()
    if not pattern.match(cleaned):
        raise WorkspaceError(code, f"{label} is invalid")
    return cleaned


__all__ = [
    "DATASET_REF_PATTERN",
    "KERNEL_REF_PATTERN",
    "NAME_PATTERN",
    "SLUG_PATTERN",
    "WorkspaceError",
    "locked",
    "read_json",
    "require_pattern",
    "resolve_source_path",
    "sha256_text",
    "source_roots",
    "subdir",
    "workspace_dir",
    "write_json",
]
