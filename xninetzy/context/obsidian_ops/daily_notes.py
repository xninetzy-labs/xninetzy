from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xninetzy.context.obsidian_ops.vault_health import _iter_markdown, _vault_root


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


_DATE_PATTERNS = [
    re.compile(r"^(\d{4}-\d{2}-\d{2})$"),
    re.compile(r"^(\d{4}-\d{2}-\d{2})\s*[-_.]"),
    re.compile(r"^(\d{1,2}-\d{1,2}-\d{4})$"),
]


@dataclass(frozen=True, slots=True)
class DailyNoteInfo:
    daily_id: str
    path: str
    date: str
    size_bytes: int
    modified: str
    has_open_tasks: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_id": self.daily_id,
            "path": self.path,
            "date": self.date,
            "size_bytes": self.size_bytes,
            "modified": self.modified,
            "has_open_tasks": self.has_open_tasks,
        }


def _match_date(name: str) -> str | None:
    for pattern in _DATE_PATTERNS:
        match = pattern.match(name)
        if match:
            return match.group(1)
    return None


_TASK_RE = re.compile(r"^\s*-\s*\[\s\]\s", re.MULTILINE)


def find_daily_notes(vault_root: str | Path | None = None) -> tuple[DailyNoteInfo, ...]:
    root = Path(vault_root) if vault_root else _vault_root()
    out: list[DailyNoteInfo] = []
    for path in _iter_markdown(root):
        match = _match_date(path.stem)
        if match is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            stat = path.stat()
        except OSError:
            continue
        out.append(
            DailyNoteInfo(
                daily_id=f"daily-{uuid.uuid4().hex[:12]}",
                path=str(path.relative_to(root)),
                date=match,
                size_bytes=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                has_open_tasks=bool(_TASK_RE.search(text)),
            )
        )
    out.sort(key=lambda d: d.date, reverse=True)
    return tuple(out)
