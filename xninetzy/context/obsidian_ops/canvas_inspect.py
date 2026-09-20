from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xninetzy.context.obsidian_ops.vault_health import _vault_root


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class CanvasReport:
    vault_root: str
    canvas_path: str
    canvas_id: str
    node_count: int
    edge_count: int
    nodes_by_type: dict[str, int]
    references_to_notes: tuple[str, ...]
    external_urls: tuple[str, ...]
    valid: bool
    error: str | None = None
    generated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canvas_id": self.canvas_id,
            "vault_root": self.vault_root,
            "canvas_path": self.canvas_path,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "nodes_by_type": dict(self.nodes_by_type),
            "references_to_notes": list(self.references_to_notes),
            "external_urls": list(self.external_urls),
            "valid": self.valid,
            "error": self.error,
            "generated_at": self.generated_at,
        }


def inspect_canvas(
    canvas_path: str | Path,
    vault_root: str | Path | None = None,
) -> CanvasReport:
    root = Path(vault_root) if vault_root else _vault_root()
    p = Path(canvas_path)
    if not p.is_absolute():
        p = root / p
    rel = str(p.relative_to(root)) if root in p.parents else str(p)
    if not p.exists():
        return CanvasReport(
            vault_root=str(root),
            canvas_path=rel,
            canvas_id=f"canvas-{uuid.uuid4().hex[:12]}",
            node_count=0,
            edge_count=0,
            nodes_by_type={},
            references_to_notes=(),
            external_urls=(),
            valid=False,
            error="file not found",
        )
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CanvasReport(
            vault_root=str(root),
            canvas_path=rel,
            canvas_id=f"canvas-{uuid.uuid4().hex[:12]}",
            node_count=0,
            edge_count=0,
            nodes_by_type={},
            references_to_notes=(),
            external_urls=(),
            valid=False,
            error=f"invalid JSON: {exc}",
        )
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    by_type: dict[str, int] = {}
    refs: list[str] = []
    urls: list[str] = []
    for node in nodes:
        ntype = str(node.get("type", "unknown"))
        by_type[ntype] = by_type.get(ntype, 0) + 1
        if ntype == "file":
            file_value = node.get("file", "")
            if file_value:
                refs.append(str(file_value))
        if ntype == "web":
            url = node.get("url", "")
            if url:
                urls.append(str(url))
        if ntype == "text":
            label = node.get("text", "")
            for hit in __import__("re").findall(r"\[\[([^\]]+)\]\]", str(label)):
                refs.append(hit)
    return CanvasReport(
        vault_root=str(root),
        canvas_path=rel,
        canvas_id=f"canvas-{uuid.uuid4().hex[:12]}",
        node_count=len(nodes),
        edge_count=len(edges),
        nodes_by_type=by_type,
        references_to_notes=tuple(sorted(set(refs))),
        external_urls=tuple(sorted(set(urls))),
        valid=True,
    )
