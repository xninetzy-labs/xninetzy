from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from xninetzy.context.obsidian_ops.vault_health import (
    _extract_wikilinks,
    _iter_markdown,
    _vault_root,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class GraphReport:
    vault_root: str
    note_count: int
    edge_count: int
    orphans: tuple[str, ...]
    hubs: tuple[tuple[str, int], ...]
    weakly_connected_components: int
    density: float
    generated_at: str = field(default_factory=_utcnow)
    report_id: str = field(default_factory=lambda: f"graph-{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "vault_root": self.vault_root,
            "note_count": self.note_count,
            "edge_count": self.edge_count,
            "orphans": list(self.orphans),
            "hubs": [{"note": n, "degree": d} for n, d in self.hubs],
            "weakly_connected_components": self.weakly_connected_components,
            "density": self.density,
            "generated_at": self.generated_at,
        }


def _build_adjacency(notes: list[Path]) -> tuple[dict[str, set[str]], int]:
    names = {p.stem for p in notes}
    adjacency: dict[str, set[str]] = {n: set() for n in names}
    edges = 0
    for path in notes:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for target in _extract_wikilinks(text):
            if target in adjacency and target != path.stem:
                adjacency[path.stem].add(target)
                edges += 1
    return adjacency, edges


def _components(adjacency: dict[str, set[str]]) -> int:
    seen: set[str] = set()
    count = 0
    for start in adjacency:
        if start in seen:
            continue
        count += 1
        stack = [start]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency.get(node, ()))
    return count


def run_graph_analysis(
    vault_root: str | Path | None = None,
    hub_top_n: int = 10,
) -> GraphReport:
    root = Path(vault_root) if vault_root else _vault_root()
    notes = list(_iter_markdown(root)) if root.exists() else []
    adjacency, edges = _build_adjacency(notes)
    note_count = len(notes)
    density = edges / max(1, note_count * (note_count - 1))
    incoming: Counter[str] = Counter()
    for source, targets in adjacency.items():
        for t in targets:
            incoming[t] += 1
    orphans = sorted(
        str(p.relative_to(root))
        for p in notes
        if not adjacency.get(p.stem) and incoming.get(p.stem, 0) == 0
    )
    out_deg = {name: len(tgts) for name, tgts in adjacency.items()}
    combined = {n: out_deg.get(n, 0) + incoming.get(n, 0) for n in adjacency}
    hubs = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:hub_top_n]
    hubs = tuple((name, degree) for name, degree in hubs if degree > 0)
    return GraphReport(
        vault_root=str(root),
        note_count=note_count,
        edge_count=edges,
        orphans=tuple(orphans),
        hubs=hubs,
        weakly_connected_components=_components(adjacency),
        density=round(density, 6),
    )
