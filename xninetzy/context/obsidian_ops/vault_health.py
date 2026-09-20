from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from xninetzy.core.config import get_settings

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
EMBED_RE = re.compile(r"!\[\[([^\]\|#]+)")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _vault_root() -> Path:
    settings = get_settings()
    raw = getattr(settings, "OBSIDIAN_VAULT_HOST_PATH", "")
    if not raw:
        return Path()
    return Path(raw).expanduser().resolve()


def _iter_markdown(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    excluded = {".obsidian", ".trash", ".git"}
    for path in root.rglob("*.md"):
        parts = set(path.relative_to(root).parts)
        if parts & excluded:
            continue
        yield path


def _extract_wikilinks(text: str) -> set[str]:
    return {m.strip() for m in WIKILINK_RE.findall(text)}


def _extract_frontmatter(text: str) -> dict[str, Any]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        return _parse_simple_yaml(match.group(1))
    except Exception:
        return {}


def _parse_simple_yaml(block: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    current_key: str | None = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("-\t"):
            if current_key is not None:
                value = line.split("-", 1)[1].strip().strip('"').strip("'")
                existing = out.get(current_key)
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    out[current_key] = [value]
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                out[key] = value.strip('"').strip("'")
            else:
                out[key] = ""
    return out


@dataclass(frozen=True, slots=True)
class HealthIssue:
    severity: str
    category: str
    note: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "note": self.note,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class HealthReport:
    vault_root: str
    note_count: int
    issue_count: int
    issues: tuple[HealthIssue, ...]
    broken_link_targets: tuple[str, ...]
    orphan_notes: tuple[str, ...]
    duplicate_titles: tuple[tuple[str, tuple[str, ...]], ...]
    notes_without_frontmatter: tuple[str, ...]
    generated_at: str = field(default_factory=_utcnow)
    report_id: str = field(default_factory=lambda: f"health-{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "vault_root": self.vault_root,
            "note_count": self.note_count,
            "issue_count": self.issue_count,
            "generated_at": self.generated_at,
            "broken_link_targets": list(self.broken_link_targets),
            "orphan_notes": list(self.orphan_notes),
            "duplicate_titles": [
                {"title": t, "paths": list(paths)}
                for t, paths in self.duplicate_titles
            ],
            "notes_without_frontmatter": list(self.notes_without_frontmatter),
            "issues": [i.to_dict() for i in self.issues],
        }


def run_vault_health(vault_root: str | Path | None = None) -> HealthReport:
    root = Path(vault_root) if vault_root else _vault_root()
    if not root.exists():
        return HealthReport(
            vault_root=str(root),
            note_count=0,
            issue_count=0,
            issues=(),
            broken_link_targets=(),
            orphan_notes=(),
            duplicate_titles=(),
            notes_without_frontmatter=(),
        )
    notes = list(_iter_markdown(root))
    note_names = {p.stem for p in notes}
    outgoing: dict[Path, set[str]] = {}
    frontmatter_flags: dict[Path, bool] = {}
    titles_by_value: dict[str, list[Path]] = {}
    for path in notes:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        outgoing[path] = _extract_wikilinks(text)
        fm = _extract_frontmatter(text)
        frontmatter_flags[path] = bool(fm)
        title_value = fm.get("title") or path.stem
        titles_by_value.setdefault(str(title_value), []).append(path)
    incoming: dict[str, set[Path]] = {name: set() for name in note_names}
    for source, targets in outgoing.items():
        for target in targets:
            if target in incoming:
                incoming[target].add(source)
    orphans = sorted(
        str(p.relative_to(root)) for p in notes if not incoming.get(p.stem)
    )
    duplicate_titles = tuple(
        (title, tuple(str(p.relative_to(root)) for p in paths))
        for title, paths in titles_by_value.items()
        if len(paths) > 1
    )
    no_fm = sorted(
        str(p.relative_to(root)) for p in notes if not frontmatter_flags.get(p, False)
    )
    broken_targets: list[str] = []
    issues: list[HealthIssue] = []
    for source, targets in outgoing.items():
        for target in targets:
            if target not in note_names:
                key = f"{target}"
                if key not in broken_targets:
                    broken_targets.append(key)
                issues.append(
                    HealthIssue(
                        severity="medium",
                        category="broken_link",
                        note=str(source.relative_to(root)),
                        detail=f"[[{target}]] not found",
                    )
                )
    for orphan in orphans:
        issues.append(
            HealthIssue(
                severity="low",
                category="orphan",
                note=orphan,
                detail="no incoming links",
            )
        )
    for title, paths in duplicate_titles:
        issues.append(
            HealthIssue(
                severity="medium",
                category="duplicate_title",
                note=title,
                detail=f"{len(paths)} notes share this title",
            )
        )
    for note in no_fm:
        issues.append(
            HealthIssue(
                severity="low",
                category="missing_frontmatter",
                note=note,
                detail="no YAML frontmatter",
            )
        )
    return HealthReport(
        vault_root=str(root),
        note_count=len(notes),
        issue_count=len(issues),
        issues=tuple(issues),
        broken_link_targets=tuple(sorted(set(broken_targets))),
        orphan_notes=tuple(orphans),
        duplicate_titles=duplicate_titles,
        notes_without_frontmatter=tuple(no_fm),
    )
