from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class BackupError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def _safe_backup_path(backup_root: Path, backup_name: str) -> Path:
    root = backup_root.expanduser().resolve()
    candidate = (root / backup_name).resolve()
    if candidate.parent != root:
        raise BackupError("Backup name must be a direct child of BACKUP_DIR")
    return candidate


def create_backup(
    sqlite_path: str | Path,
    vector_dir: str | Path,
    backup_root: str | Path,
    *,
    retention: int = 14,
    now: datetime | None = None,
) -> dict:
    database = Path(sqlite_path).expanduser().resolve()
    vectors = Path(vector_dir).expanduser().resolve()
    root = Path(backup_root).expanduser().resolve()
    if not database.is_file():
        raise BackupError(f"SQLite database not found: {database}")

    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    backup_name = f"xninetzy-{timestamp}-{uuid4().hex[:8]}"
    target = root / backup_name
    staging = root / f".{backup_name}.tmp"
    staging.mkdir(parents=True, exist_ok=False)
    os.chmod(staging, 0o700)

    try:
        database_copy = staging / "xninetzy.sqlite3"
        with (
            sqlite3.connect(database) as source,
            sqlite3.connect(database_copy) as dest,
        ):
            source.backup(dest)

        copied = [database_copy]
        vector_target = staging / "vector"
        for filename in ("faiss.index", "faiss_map.json"):
            source = vectors / filename
            if source.is_file():
                vector_target.mkdir(parents=True, exist_ok=True)
                destination = vector_target / filename
                shutil.copy2(source, destination)
                copied.append(destination)

        manifest = {
            "version": 1,
            "created_at": (now or datetime.now(timezone.utc)).isoformat(),
            "contains_secrets": False,
            "files": {
                str(path.relative_to(staging)): {
                    "sha256": _sha256(path),
                    "size": path.stat().st_size,
                }
                for path in copied
            },
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    prune_backups(root, retention)
    return {"name": backup_name, "path": str(target), **manifest}


def list_backups(backup_root: str | Path) -> list[dict]:
    root = Path(backup_root).expanduser().resolve()
    if not root.exists():
        return []
    results: list[dict] = []
    for directory in sorted(root.glob("xninetzy-*"), reverse=True):
        manifest_path = directory / "manifest.json"
        if not directory.is_dir() or not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            results.append({"name": directory.name, "path": str(directory), **manifest})
        except (OSError, json.JSONDecodeError):
            continue
    return results


def verify_backup(backup_root: str | Path, backup_name: str) -> dict:
    directory = _safe_backup_path(Path(backup_root), backup_name)
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise BackupError("Backup manifest not found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for relative, expected in manifest.get("files", {}).items():
        candidate = (directory / relative).resolve()
        if directory not in candidate.parents or not candidate.is_file():
            errors.append(f"missing:{relative}")
            continue
        if _sha256(candidate) != expected.get("sha256"):
            errors.append(f"checksum:{relative}")
    return {"name": backup_name, "valid": not errors, "errors": errors}


def restore_backup(
    backup_root: str | Path,
    backup_name: str,
    sqlite_path: str | Path,
    vector_dir: str | Path,
    *,
    confirmed: bool = False,
) -> dict:
    if not confirmed:
        raise BackupError("Restore requires explicit confirmation")
    verification = verify_backup(backup_root, backup_name)
    if not verification["valid"]:
        raise BackupError(f"Backup verification failed: {verification['errors']}")

    directory = _safe_backup_path(Path(backup_root), backup_name)
    _atomic_copy(
        directory / "xninetzy.sqlite3", Path(sqlite_path).expanduser().resolve()
    )
    vectors = Path(vector_dir).expanduser().resolve()
    for filename in ("faiss.index", "faiss_map.json"):
        source = directory / "vector" / filename
        if source.is_file():
            _atomic_copy(source, vectors / filename)
    return {"name": backup_name, "restored": True}


def prune_backups(backup_root: str | Path, retention: int) -> None:
    root = Path(backup_root).expanduser().resolve()
    backups = [Path(item["path"]) for item in list_backups(root)]
    for directory in backups[max(1, retention) :]:
        shutil.rmtree(directory)
