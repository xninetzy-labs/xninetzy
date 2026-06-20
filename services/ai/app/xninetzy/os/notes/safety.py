from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.notes.obsidian_config import vault_path

BLOCKED_PARTS = {
    ".env",
    "sessions",
    "node_modules",
    "__pycache__",
    ".git",
    "id_rsa",
    "credentials",
    "token",
    "secret",
}

READ_EXTENSIONS = {".md", ".txt", ".json", ".csv"}
WRITE_EXTENSIONS = {".md", ".txt", ".json"}


class ObsidianSafetyError(ValueError):
    pass


def resolve_vault_path(path: str | None, *, for_write: bool = False) -> Path:
    raw = (path or "").strip()
    if not raw:
      raw = "."

    if "\x00" in raw or "~" in raw:
        raise ObsidianSafetyError("Path tidak aman untuk vault Obsidian")

    candidate_raw = Path(raw)
    if candidate_raw.is_absolute():
        raise ObsidianSafetyError("Absolute path tidak diizinkan")

    if ".." in candidate_raw.parts:
        raise ObsidianSafetyError("Path traversal tidak diizinkan")

    lowered_parts = {part.lower() for part in candidate_raw.parts}
    if lowered_parts & BLOCKED_PARTS:
        raise ObsidianSafetyError("Path mengandung nama yang diblokir")

    root = vault_path()
    resolved = (root / candidate_raw).resolve()
    if root != resolved and root not in resolved.parents:
        raise ObsidianSafetyError("Path harus berada di dalam vault Obsidian")

    if resolved.name.lower() in BLOCKED_PARTS:
        raise ObsidianSafetyError("File diblokir")

    if resolved.suffix:
        allowed = WRITE_EXTENSIONS if for_write else READ_EXTENSIONS
        if resolved.suffix.lower() not in allowed:
            raise ObsidianSafetyError(f"Ekstensi {resolved.suffix} tidak diizinkan")

    return resolved


def ensure_readable_file(path: Path) -> None:
    settings = get_settings()
    if not path.exists() or not path.is_file():
        raise ObsidianSafetyError("Note tidak ditemukan")
    max_size = settings.OBSIDIAN_MAX_FILE_SIZE_MB * 1024 * 1024
    if path.stat().st_size > max_size:
        raise ObsidianSafetyError("File terlalu besar untuk dibaca")


def ensure_write_allowed(path: Path, *, overwrite: bool = False) -> None:
    settings = get_settings()
    if not settings.OBSIDIAN_ENABLED:
        raise ObsidianSafetyError("Obsidian integration sedang disabled")
    if not settings.OBSIDIAN_ALLOW_WRITE:
        raise ObsidianSafetyError("Write ke Obsidian sedang disabled")
    if path.exists() and not overwrite:
        raise ObsidianSafetyError("File sudah ada; overwrite butuh konfirmasi")


def ensure_delete_allowed() -> None:
    if not get_settings().OBSIDIAN_ALLOW_DELETE:
        raise ObsidianSafetyError("Delete file Obsidian disabled by default")
