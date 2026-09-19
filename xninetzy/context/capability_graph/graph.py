from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from xninetzy.db.sqlite import connect


@dataclass(frozen=True, slots=True)
class CapabilityNode:
    capability: str
    surface: str
    tool: str | None = None
    aliases: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SeedResult:
    inserted: int
    updated: int
    skipped: int
    capabilities: tuple[str, ...]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_aliases(values: Iterable[str]) -> tuple[str, ...]:
    seen: list[str] = []
    dedup: set[str] = set()
    for raw in values:
        if not raw:
            continue
        cleaned = raw.strip().lower()
        if not cleaned or cleaned in dedup:
            continue
        dedup.add(cleaned)
        seen.append(cleaned)
    return tuple(seen)


def _aliases_for_group(group: str, tool: str) -> tuple[str, ...]:
    base: list[str] = [group, tool]
    underscored = tool.replace("-", "_").replace(".", "_")
    if underscored != tool:
        base.append(underscored)
    spaced = tool.replace("_", " ").replace("-", " ")
    if spaced != tool:
        base.append(spaced)
    base.append(f"{group}:{tool}")
    base.append(f"{group} {tool}")
    return _normalize_aliases(base)


def _nodes_from_registry() -> list[CapabilityNode]:
    from xninetzy.tools.registry import get_tool_groups

    groups = get_tool_groups()
    nodes: list[CapabilityNode] = []
    for group, tools in groups.items():
        surface = f"tool_group:{group}"
        nodes.append(
            CapabilityNode(
                capability=group,
                surface=surface,
                tool=None,
                aliases=_aliases_for_group(group, group),
                metadata={"kind": "tool_group"},
            )
        )
        for tool in tools:
            tool_surface = f"tool:{tool}"
            nodes.append(
                CapabilityNode(
                    capability=tool,
                    surface=tool_surface,
                    tool=tool,
                    aliases=_aliases_for_group(group, tool),
                    metadata={"kind": "tool", "group": group},
                )
            )
    return nodes


def _existing_rows(conn) -> dict[tuple[str, str, str], dict[str, Any]]:
    rows = conn.execute(
        "SELECT capability, surface, alias, weight FROM capability_aliases"
    ).fetchall()
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        out[(row["capability"], row["surface"], row["alias"])] = {
            "weight": float(row["weight"]),
        }
    return out


def seed_from_registry(
    *,
    now: str | None = None,
    nodes: list[CapabilityNode] | None = None,
) -> SeedResult:
    stamp = now or _utcnow()
    selected = nodes if nodes is not None else _nodes_from_registry()
    inserted = 0
    updated = 0
    skipped = 0
    capabilities: set[str] = set()
    with connect() as conn:
        existing = _existing_rows(conn)
        for node in selected:
            capabilities.add(node.capability)
            for alias in node.aliases:
                key = (node.capability, node.surface, alias)
                if key in existing:
                    skipped += 1
                    continue
                payload = {
                    "capability": node.capability,
                    "surface": node.surface,
                    "alias": alias,
                    "weight": 1.0,
                    "metadata_json": "{}",
                    "created_at": stamp,
                }
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO capability_aliases
                        (capability, surface, alias, weight, metadata_json, created_at)
                    VALUES (:capability, :surface, :alias, :weight, :metadata_json, :created_at)
                    """,
                    payload,
                )
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
    return SeedResult(
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        capabilities=tuple(sorted(capabilities)),
    )
