from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xninetzy.context.obsidian_ops.vault_health import _vault_root


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class TemplateInfo:
    template_id: str
    name: str
    path: str
    size_bytes: int
    uses_date_variables: bool
    uses_time_variables: bool
    has_frontmatter: bool
    variables: tuple[str, ...]
    preview: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "uses_date_variables": self.uses_date_variables,
            "uses_time_variables": self.uses_time_variables,
            "has_frontmatter": self.has_frontmatter,
            "variables": list(self.variables),
            "preview": self.preview,
        }


import re

DATE_VAR_RE = re.compile(r"\{\{\s*(date|time)\b[^}]*\}\}", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)")
FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _iter_templates(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    excluded = {".obsidian", ".trash"}
    for folder in root.rglob("*"):
        if not folder.is_dir():
            continue
        if folder.name.lower() != "templates":
            continue
        if set(folder.relative_to(root).parts) & excluded:
            continue
        for f in folder.rglob("*.md"):
            out.append(f)
    if not out:
        for f in root.rglob("*.md"):
            rel_parts = set(f.relative_to(root).parts)
            if rel_parts & {".obsidian", ".trash"}:
                continue
            if "templates" in (p.lower() for p in rel_parts):
                out.append(f)
    return sorted(set(out))


def list_templates(vault_root: str | Path | None = None) -> tuple[TemplateInfo, ...]:
    root = Path(vault_root) if vault_root else _vault_root()
    out: list[TemplateInfo] = []
    for p in _iter_templates(root):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        variables = sorted(set(PLACEHOLDER_RE.findall(text)))
        has_fm = bool(FRONTMATTER_RE.match(text))
        out.append(
            TemplateInfo(
                template_id=f"tmpl-{uuid.uuid4().hex[:12]}",
                name=p.stem,
                path=str(p.relative_to(root)),
                size_bytes=p.stat().st_size,
                uses_date_variables=bool(DATE_VAR_RE.search(text)),
                uses_time_variables=bool(
                    re.search(r"\{\{\s*time\b", text, re.IGNORECASE)
                ),
                has_frontmatter=has_fm,
                variables=tuple(variables),
                preview=text[:400],
            )
        )
    return tuple(out)
