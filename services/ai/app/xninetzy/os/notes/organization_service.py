from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.notes.folder_policy import (
    CANONICAL_FOLDERS,
    canonical_path,
    note_type_from_path,
)
from app.xninetzy.os.notes.markdown_service import MarkdownService
from app.xninetzy.os.notes.obsidian_config import vault_path
from app.xninetzy.os.notes.safety import ensure_readable_file, ensure_write_allowed, resolve_vault_path


class ObsidianOrganizationError(RuntimeError):
    pass


class ObsidianOrganizationService:
    def __init__(self) -> None:
        self.vault = vault_path()
        self.markdown = MarkdownService()

    def ensure_structure(self) -> dict[str, Any]:
        if not get_settings().OBSIDIAN_FOLDERING_ENABLED:
            raise ObsidianOrganizationError("Obsidian foldering sedang disabled")
        created: list[str] = []
        for folder in CANONICAL_FOLDERS:
            target = resolve_vault_path(folder, for_write=True)
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                created.append(folder)
        home = resolve_vault_path("Home.md", for_write=True)
        if not home.exists():
            home.parent.mkdir(parents=True, exist_ok=True)
            home.write_text(self._home_content(), encoding="utf-8")
            created.append("Home.md")
        return {"created": created, "folders": list(CANONICAL_FOLDERS)}

    def refresh_mocs(self) -> dict[str, Any]:
        self.ensure_structure()
        specs = {
            "Learning/MOCs/Index.md": "Learning",
            "Projects/Index.md": "Projects",
            "Academic/Index.md": "Academic",
            "Research/MOCs/Index.md": "Research",
            "Life/Index.md": "Life",
            "Knowledge/MOCs/Index.md": "Knowledge",
            "System/MOCs/Index.md": "System",
        }
        written: list[str] = []
        backups: list[str] = []
        for target, folder in specs.items():
            notes = []
            root = self.vault / folder
            if root.exists():
                for item in sorted(root.rglob("*.md")):
                    relative = item.resolve().relative_to(self.vault.resolve()).as_posix()
                    if relative == target or relative.endswith("/Index.md"):
                        continue
                    notes.append(f"- [[{Path(relative).with_suffix('').as_posix()}]]")
            content = (
                f"# {Path(target).stem}\n\n## Notes\n\n"
                + ("\n".join(notes) if notes else "- Belum ada note.")
                + "\n"
            )
            destination = resolve_vault_path(target, for_write=True)
            ensure_write_allowed(destination, overwrite=True)
            backup = self._backup(destination)
            if backup:
                backups.append(backup)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            written.append(target)
        return {"written": written, "backups": backups}

    def inventory(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.vault.rglob("*.md")):
            relative = path.resolve().relative_to(self.vault.resolve()).as_posix()
            if relative.startswith(".backup/"):
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            metadata = self.markdown.parse_frontmatter(content)
            items.append(
                {
                    "path": relative,
                    "type": metadata.get("type") or note_type_from_path(relative),
                    "title": metadata.get("title") or self._title(path, content),
                    "hash": _sha256(content),
                    "canonical": self._is_canonical(relative),
                    "size": path.stat().st_size,
                }
            )
        return items

    def preview(self) -> dict[str, Any]:
        if not get_settings().OBSIDIAN_FOLDERING_ENABLED:
            raise ObsidianOrganizationError("Obsidian foldering sedang disabled")
        items = self.inventory()
        moves: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        for item in items:
            target = self._target_for(item)
            if not target:
                if not item["canonical"]:
                    unresolved.append(item)
                continue
            if target == item["path"]:
                continue
            target_path = self.vault / target
            entry = {"source": item["path"], "target": target, "source_hash": item["hash"], "type": item["type"]}
            if target_path.exists():
                conflicts.append(entry)
            else:
                moves.append(entry)
        return {
            "mode": "hybrid",
            "total_notes": len(items),
            "canonical_notes": sum(1 for item in items if item["canonical"]),
            "moves": moves,
            "conflicts": conflicts,
            "unresolved": unresolved,
            "structure": list(CANONICAL_FOLDERS),
        }

    def apply(self, plan: dict[str, Any]) -> dict[str, Any]:
        self.ensure_structure()
        moves = list(plan.get("moves") or [])
        applied: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for move in moves:
            source = str(move.get("source") or "")
            target = str(move.get("target") or "")
            if not source or not target:
                skipped.append({"source": source, "target": target, "reason": "invalid"})
                continue
            source_path = resolve_vault_path(source)
            target_path = resolve_vault_path(target, for_write=True)
            ensure_readable_file(source_path)
            current = source_path.read_text(encoding="utf-8")
            if move.get("source_hash") and move["source_hash"] != _sha256(current):
                skipped.append({"source": source, "target": target, "reason": "source_changed"})
                continue
            if target_path.exists():
                skipped.append({"source": source, "target": target, "reason": "target_exists"})
                continue
            ensure_write_allowed(target_path, overwrite=False)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            backup = self._backup(source_path)
            title = self.markdown.parse_frontmatter(current).get("title") or self._title(source_path, current)
            metadata = {"canonical_path": target, "updated": self._now()}
            migrated = self.markdown.upsert_frontmatter(current, metadata)
            source_path.write_text(migrated, encoding="utf-8")
            shutil.move(str(source_path), str(target_path))
            applied.append({"source": source, "target": target, "backup": backup, "title": title})
        links_updated = self._update_links(applied)
        return {
            "applied": applied,
            "skipped": skipped,
            "links_updated": links_updated,
            "verified": self.verify(),
        }

    def verify(self) -> dict[str, Any]:
        items = self.inventory()
        ids: dict[str, list[str]] = {}
        missing_structure = [folder for folder in CANONICAL_FOLDERS if not (self.vault / folder).is_dir()]
        for item in items:
            path = self.vault / item["path"]
            metadata = self.markdown.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            note_id = str(metadata.get("id") or "")
            if note_id:
                ids.setdefault(note_id, []).append(item["path"])
        duplicate_ids = {key: value for key, value in ids.items() if len(value) > 1}
        return {
            "notes": len(items),
            "missing_structure": missing_structure,
            "duplicate_ids": duplicate_ids,
            "healthy": not missing_structure and not duplicate_ids,
        }

    def _target_for(self, item: dict[str, Any]) -> str | None:
        path = item["path"]
        if item["canonical"]:
            return path
        note_type = item.get("type")
        title = str(item.get("title") or Path(path).stem)
        parts = path.split("/")
        if note_type == "daily":
            date_text = self._date_from_path(path) or self._now()[:10]
            return canonical_path("daily", title=title, date_value=date_text)
        if note_type == "learning":
            return canonical_path("learning_note", title=title)
        if note_type == "project":
            project = parts[1] if len(parts) > 1 else title
            return canonical_path("project", title=title, project=project)
        if note_type == "task":
            return canonical_path("task", title=title)
        if note_type == "goal":
            domain = parts[1] if len(parts) > 1 else "personal"
            return canonical_path("goal", title=title, domain=domain)
        if note_type == "hebat_material":
            course = parts[1] if len(parts) > 1 else "course"
            return canonical_path("hebat_material", title=title, course=course)
        if note_type == "helper":
            return canonical_path("helper", title=title)
        if note_type == "system_log":
            return canonical_path("system_log", title=title)
        return None

    def _is_canonical(self, path: str) -> bool:
        parts = path.strip("/").split("/")
        if path == "Home.md":
            return True
        if len(parts) >= 3 and parts[0] == "Daily" and re.fullmatch(r"\d{4}", parts[1]) and re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", parts[2]):
            return True
        if parts[0] == "Learning" and len(parts) >= 3 and parts[1] in {"Roadmaps", "Concepts", "Sessions", "Notes", "Reviews", "MOCs"}:
            return True
        if parts[0] == "Projects" and len(parts) >= 3 and parts[-1] == "README.md":
            return True
        if parts[0] in {"Academic", "Research", "Life", "Knowledge", "Attachments", "System", "Archive", "Inbox"}:
            return True
        return False

    def _update_links(self, applied: list[dict[str, Any]]) -> int:
        if not applied:
            return 0
        replacements: dict[str, str] = {}
        for item in applied:
            source = Path(item["source"]).with_suffix("").as_posix()
            target = Path(item["target"]).with_suffix("").as_posix()
            replacements[f"[[{source}"] = f"[[{target}"
        updated = 0
        for path in self.vault.rglob("*.md"):
            if str(path).startswith(str(self.vault / ".backup")):
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
            if new_content != content:
                path.write_text(new_content, encoding="utf-8")
                updated += 1
        return updated

    def _backup(self, path: Path) -> str:
        if not get_settings().OBSIDIAN_BACKUP_BEFORE_WRITE or not path.exists():
            return ""
        today = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")
        backup_root = self.vault / ".backup" / today
        backup_root.mkdir(parents=True, exist_ok=True)
        relative = path.resolve().relative_to(self.vault.resolve())
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        return backup.relative_to(self.vault).as_posix()

    def _title(self, path: Path, content: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return path.stem.replace("-", " ").replace("_", " ").strip() or "Untitled"

    def _date_from_path(self, path: str) -> str | None:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path)
        return match.group(1) if match else None

    def _now(self) -> str:
        return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()

    def _home_content(self) -> str:
        links = [
            "[[Daily]]",
            "[[Learning/MOCs/Index]]",
            "[[Projects/Index]]",
            "[[Academic/Index]]",
            "[[Research/MOCs/Index]]",
            "[[Life/Index]]",
            "[[Knowledge/MOCs/Index]]",
        ]
        return "# Xninetzy OS\n\n## Navigation\n\n" + "\n".join(f"- {link}" for link in links) + "\n"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
