from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import re
import time
import tempfile
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class BackupError(RuntimeError):
    pass


_DATABASE = "xninetzy.sqlite3"
_VECTORS = ("vector/faiss.index", "vector/faiss_map.json")
_FILES = {_DATABASE, *_VECTORS}


def _local_path(value: str | Path) -> Path:
    path = Path(value).expanduser().absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise BackupError("backup_symlink_path")
    return path.resolve()


def _sqlite_valid(path: Path) -> bool:
    try:
        # A snapshot is standalone: never pair it with an adjacent WAL/journal.
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
            db.execute("PRAGMA trusted_schema=OFF")
            return db.execute("PRAGMA integrity_check").fetchall() == [("ok",)] and not db.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
    except sqlite3.Error:
        return False


def _manifest(directory: Path) -> dict:
    path = directory / "manifest.json"
    if path.is_symlink() or not path.is_file():
        raise BackupError("backup_manifest_invalid")
    try:
        with path.open("rb") as handle:
            data = handle.read(65537)
        value = json.loads(data) if len(data) <= 65536 else None
    except (OSError, ValueError, UnicodeError):
        raise BackupError("backup_manifest_invalid") from None
    if not isinstance(value, dict) or type(value.get("version")) is not int or value["version"] != 1:
        raise BackupError("backup_manifest_invalid")
    files = value.get("files")
    if not isinstance(files, dict) or set(files) not in ({_DATABASE}, _FILES):
        raise BackupError("backup_manifest_invalid")
    for entry in files.values():
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("sha256"), str)
            or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"])
            or type(entry.get("size")) is not int
            or entry["size"] < 0
        ):
            raise BackupError("backup_manifest_invalid")
    return value


def _snapshot_errors(directory: Path, manifest: dict) -> list[str]:
    errors = []
    if any((directory / (_DATABASE + suffix)).exists() or (directory / (_DATABASE + suffix)).is_symlink()
           for suffix in ("-wal", "-shm", "-journal")):
        errors.append("sqlite:sidecar")
    for relative in _FILES:
        candidate = directory / relative
        if candidate.is_symlink() or any(p.is_symlink() for p in candidate.parents):
            errors.append(f"symlink:{relative}")
        elif relative not in manifest["files"]:
            if candidate.exists():
                errors.append(f"unlisted:{relative}")
        elif not candidate.is_file():
            errors.append(f"missing:{relative}")
        elif _sha256(candidate) != manifest["files"][relative]["sha256"]:
            errors.append(f"checksum:{relative}")
        elif candidate.stat().st_size != manifest["files"][relative]["size"]:
            errors.append(f"size:{relative}")
    if not errors and not _sqlite_valid(directory / _DATABASE):
        errors.append("sqlite:integrity")
    return sorted(errors)


def _offline(database: Path) -> None:
    if any(Path(str(database) + suffix).exists() or Path(str(database) + suffix).is_symlink()
           for suffix in ("-wal", "-shm", "-journal")):
        raise BackupError("restore_requires_offline_database")
    if database.exists():
        try:
            with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=0)) as db:
                db.execute("BEGIN EXCLUSIVE")
                db.rollback()
        except sqlite3.Error:
            raise BackupError("restore_requires_offline_database") from None


@contextmanager
def _restore_lock(database: Path):
    try:
        import fcntl
    except ImportError:
        raise BackupError("restore_requires_posix_lock") from None
    path = database.with_name(f".{database.name}.restore.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BackupError("restore_in_progress") from None
        yield
    finally:
        os.close(fd)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as dest, source.open("rb") as src:
            shutil.copyfileobj(src, dest)
            dest.flush()
            os.fsync(dest.fileno())
        os.replace(temporary, target)
        _sync_directory(target.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _sync_directory(path: Path) -> None:
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _safe_backup_path(backup_root: Path, backup_name: str) -> Path:
    root = _local_path(backup_root)
    if not backup_name or Path(backup_name).name != backup_name or backup_name in (".", ".."):
        raise BackupError("Backup name must be a direct child of BACKUP_DIR")
    candidate = _local_path(root / backup_name)
    if candidate.parent != root:
        raise BackupError("Backup name must be a direct child of BACKUP_DIR")
    return candidate


def create_backup(
    sqlite_path: str | Path,
    vector_dir: str | Path,
    backup_root: str | Path,
    *,
    retention: int | None = 14,
    now: datetime | None = None,
) -> dict:
    database = _local_path(sqlite_path)
    vectors = _local_path(vector_dir)
    root = _local_path(backup_root)
    if not database.is_file():
        raise BackupError("backup_database_missing")
    vector_files = [vectors / name for name in ("faiss.index", "faiss_map.json")]
    if any(p.is_symlink() for p in vector_files) or sum(p.is_file() for p in vector_files) not in (0, 2):
        raise BackupError("backup_vector_pair_invalid")
    root.mkdir(parents=True, mode=0o700, exist_ok=True)

    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    backup_name = f"xninetzy-{timestamp}-{uuid4().hex[:8]}"
    target = root / backup_name
    staging = root / f".{backup_name}.tmp"
    staging.mkdir(parents=True, exist_ok=False)
    os.chmod(staging, 0o700)

    try:
        database_copy = staging / "xninetzy.sqlite3"
        deadline = time.monotonic() + 30

        def progress(status, remaining, total):
            if time.monotonic() > deadline:
                raise BackupError("backup_timeout")

        with (
            closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(database_copy)) as dest,
        ):
            source.backup(dest, pages=256, progress=progress)
        os.chmod(database_copy, 0o600)
        if not _sqlite_valid(database_copy):
            raise BackupError("backup_sqlite_integrity")

        copied = [database_copy]
        vector_target = staging / "vector"
        for filename in ("faiss.index", "faiss_map.json"):
            source = vectors / filename
            if source.is_file():
                vector_target.mkdir(parents=True, exist_ok=True)
                destination = vector_target / filename
                _atomic_copy(source, destination)
                copied.append(destination)

        manifest = {
            "version": 1,
            "created_at": (now or datetime.now(timezone.utc)).isoformat(),
            "contains_secrets": None,
            "vector_consistency": "offline_required" if len(copied) > 1 else "absent",
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
        os.chmod(staging / "manifest.json", 0o600)
        with (staging / "manifest.json").open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(staging, target)
        _sync_directory(root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    if retention is not None:
        prune_backups(root, retention, keep=backup_name)
    return {"name": backup_name, "path": str(target), **manifest}


def list_backups(backup_root: str | Path) -> list[dict]:
    root = _local_path(backup_root)
    if not root.exists():
        return []
    results: list[dict] = []
    for directory in sorted(root.glob("xninetzy-*"), reverse=True):
        manifest_path = directory / "manifest.json"
        if directory.is_symlink() or not directory.is_dir() or not manifest_path.is_file():
            continue
        try:
            manifest = _manifest(directory)
            results.append({**manifest, "name": directory.name, "path": str(directory)})
        except (OSError, BackupError):
            continue
    return results


def verify_backup(backup_root: str | Path, backup_name: str) -> dict:
    directory = _safe_backup_path(Path(backup_root), backup_name)
    try:
        manifest = _manifest(directory)
        errors = _snapshot_errors(directory, manifest)
    except (BackupError, OSError):
        errors = ["manifest:invalid"]
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
    database = _local_path(sqlite_path)
    vectors = _local_path(vector_dir)
    root = _local_path(backup_root)
    directory = _safe_backup_path(root, backup_name)
    if database.is_relative_to(root) or vectors.is_relative_to(root) or database in (
        vectors / "faiss.index", vectors / "faiss_map.json"
    ):
        raise BackupError("restore_target_overlap")
    verification = verify_backup(root, backup_name)
    if not verification["valid"]:
        raise BackupError(f"Backup verification failed: {verification['errors']}")

    manifest = _manifest(directory)
    _offline(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    with _restore_lock(database), tempfile.TemporaryDirectory(prefix=".restore-", dir=database.parent) as tmp:
        targets = [vectors / Path(relative).name for relative in _VECTORS]
        if any(p.is_symlink() for p in targets):
            raise BackupError("restore_vector_symlink")
        if any(p.exists() for p in targets) and not all(relative in manifest["files"] for relative in _VECTORS):
            raise BackupError("restore_vector_reconciliation_required")
        staged = Path(tmp)
        for relative in manifest["files"]:
            _atomic_copy(directory / relative, staged / relative)
        if _snapshot_errors(staged, manifest):
            raise BackupError("restore_staged_verification_failed")
        _offline(database)
        safety = None
        if database.exists():
            # Under the offline operator contract, capture the current standalone
            # file privately. Opening the original WAL-format file read-only can
            # itself leave -wal/-shm files; do not remove or bypass that guard.
            current = staged / "pre_restore.sqlite3"
            _atomic_copy(database, current)
            safety = create_backup(current, vectors, root, retention=None)
        try:
            for relative in _VECTORS:
                if relative in manifest["files"]:
                    _atomic_copy(staged / relative, vectors / Path(relative).name)
            # Canonical cutover last; optional files are not a multi-file transaction.
            _offline(database)
            _atomic_copy(staged / _DATABASE, database)
        except Exception:
            reference = safety["name"] if safety else "no_previous_database"
            raise BackupError(f"restore_interrupted; keep services offline; safety={reference}") from None
    return {"name": backup_name, "restored": True, "pre_restore_backup": safety["name"] if safety else None}


def prune_backups(backup_root: str | Path, retention: int, *, keep: str | None = None) -> None:
    root = _local_path(backup_root)
    backups = [_safe_backup_path(root, item["name"]) for item in list_backups(root)]
    if keep is not None:
        protected = _safe_backup_path(root, keep)
        backups.sort(key=lambda path: path != protected)
    for directory in backups[max(1, retention) :]:
        shutil.rmtree(directory)
