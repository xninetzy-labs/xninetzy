from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect
from app.obsidian.config import vault_path
from app.obsidian.markdown_service import MarkdownService
from app.obsidian.safety import ensure_readable_file, ensure_write_allowed, resolve_vault_path


class ObsidianVaultService:
    def __init__(self) -> None:
        self.markdown = MarkdownService()

    def list_files(self, folder: str | None = None) -> list[dict]:
        root = resolve_vault_path(folder)
        if not root.exists():
            return []
        if root.is_file():
            files = [root]
        else:
            files = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".txt"}]
        return [self._file_info(path) for path in sorted(files)]

    def read_note(self, path: str) -> str:
        note = resolve_vault_path(path)
        ensure_readable_file(note)
        return note.read_text(encoding="utf-8")

    def search_notes(self, query: str, limit: int = 20) -> list[dict]:
        needle = query.casefold().strip()
        if not needle:
            return []
        matches: list[dict] = []
        for item in self.list_files():
            path = item["path"]
            try:
                content = self.read_note(path)
            except Exception:
                continue
            haystack = (path + "\n" + content).casefold()
            if needle in haystack:
                matches.append({**item, "preview": self._preview(content, needle)})
            if len(matches) >= limit:
                break
        return matches

    def create_note(self, path: str, content: str, overwrite: bool = False) -> dict:
        note = resolve_vault_path(path, for_write=True)
        ensure_write_allowed(note, overwrite=overwrite)
        old_content = note.read_text(encoding="utf-8") if note.exists() else ""
        backup = self._backup(note) if note.exists() and get_settings().OBSIDIAN_BACKUP_BEFORE_WRITE else None
        try:
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(content, encoding="utf-8")
            self._log_operation("create_note", note, old_content, content, backup, True, None)
            return {"path": self._relative(note), "created": not old_content, "backup_path": backup}
        except Exception as error:
            self._log_operation("create_note", note, old_content, content, backup, False, str(error))
            raise

    def append_note(self, path: str, content: str) -> dict:
        note = resolve_vault_path(path, for_write=True)
        old_content = note.read_text(encoding="utf-8") if note.exists() else ""
        ensure_write_allowed(note, overwrite=True)
        backup = self._backup(note) if note.exists() and get_settings().OBSIDIAN_BACKUP_BEFORE_WRITE else None
        new_content = old_content.rstrip() + "\n\n" + content.strip() + "\n"
        try:
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(new_content, encoding="utf-8")
            self._log_operation("append_note", note, old_content, new_content, backup, True, None)
            return {"path": self._relative(note), "backup_path": backup}
        except Exception as error:
            self._log_operation("append_note", note, old_content, new_content, backup, False, str(error))
            raise

    def update_section(self, path: str, heading: str, content: str) -> dict:
        note = resolve_vault_path(path, for_write=True)
        ensure_readable_file(note)
        ensure_write_allowed(note, overwrite=True)
        old_content = note.read_text(encoding="utf-8")
        new_content = self.markdown.update_heading_section(old_content, heading, content)
        backup = self._backup(note) if get_settings().OBSIDIAN_BACKUP_BEFORE_WRITE else None
        try:
            note.write_text(new_content, encoding="utf-8")
            self._log_operation("update_section", note, old_content, new_content, backup, True, None)
            return {"path": self._relative(note), "heading": heading, "backup_path": backup}
        except Exception as error:
            self._log_operation("update_section", note, old_content, new_content, backup, False, str(error))
            raise

    def create_folder(self, path: str) -> dict:
        folder = resolve_vault_path(path)
        folder.mkdir(parents=True, exist_ok=True)
        return {"path": self._relative(folder), "created": True}

    def extract_todos(self, folder: str | None = None) -> list[dict]:
        todos: list[dict] = []
        for item in self.list_files(folder):
            content = self.read_note(item["path"])
            for line_no, line in enumerate(content.splitlines(), start=1):
                if line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"):
                    todos.append({"path": item["path"], "line": line_no, "text": line.strip()})
        return todos

    def get_backlinks(self, note_path: str) -> list[dict]:
        note = Path(note_path).with_suffix("").name
        pattern = f"[[{note}"
        backlinks: list[dict] = []
        for item in self.list_files():
            content = self.read_note(item["path"])
            if pattern.casefold() in content.casefold():
                backlinks.append(item)
        return backlinks

    def generate_moc(self, folder: str | None = None, title: str = "Index") -> dict:
        files = self.list_files(folder)
        lines = [f"# {title}", "", "## Notes"]
        for item in files:
            note_name = Path(item["path"]).with_suffix("").as_posix()
            lines.append(f"- {self.markdown.wikilink(note_name)}")
        path = f"{folder.strip('/') + '/' if folder else ''}{title}.md"
        return self.create_note(path, "\n".join(lines).rstrip() + "\n", overwrite=True)

    def extract_headings(self, path: str) -> list[dict]:
        return self.markdown.extract_headings(self.read_note(path))

    def add_frontmatter(self, path: str, data: dict) -> dict:
        content = self.read_note(path)
        new_content = self.markdown.upsert_frontmatter(content, data)
        return self.create_note(path, new_content, overwrite=True)

    def add_tags(self, path: str, tags: list[str]) -> dict:
        content = self.read_note(path)
        new_content = self.markdown.add_tags(content, tags)
        return self.create_note(path, new_content, overwrite=True)

    def _backup(self, path: Path) -> str:
        if not path.exists():
            return ""
        today = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")
        backup_root = vault_path() / ".backup" / today
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / f"{path.stem}.bak{path.suffix}"
        shutil.copy2(path, backup)
        return self._relative(backup)

    def _file_info(self, path: Path) -> dict:
        stat = path.stat()
        return {"path": self._relative(path), "size": stat.st_size, "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()}

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(vault_path()).as_posix()

    def _preview(self, content: str, needle: str) -> str:
        index = content.casefold().find(needle)
        if index == -1:
            return content[:180]
        return content[max(0, index - 80) : index + 140].replace("\n", " ").strip()

    def _log_operation(self, operation: str, path: Path, old: str, new: str, backup: str | None, success: bool, error: str | None) -> None:
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO file_operations
                (operation, path, old_content_hash, new_content_hash, backup_path, success, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operation,
                    self._relative(path),
                    _sha256(old) if old else None,
                    _sha256(new) if new else None,
                    backup,
                    1 if success else 0,
                    error,
                    now,
                ),
            )


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
