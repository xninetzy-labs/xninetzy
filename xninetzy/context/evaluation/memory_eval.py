from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class MemoryAudit:
    memory_count: int
    useful_count: int
    conflicting_count: int
    duplicate_count: int
    usefulness_ratio: float
    conflict_ratio: float
    recommendations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_count": self.memory_count,
            "useful_count": self.useful_count,
            "conflicting_count": self.conflicting_count,
            "duplicate_count": self.duplicate_count,
            "usefulness_ratio": round(self.usefulness_ratio, 4),
            "conflict_ratio": round(self.conflict_ratio, 4),
            "recommendations": list(self.recommendations),
        }


def evaluate_memory(
    *,
    memories: tuple[dict[str, Any], ...],
) -> MemoryAudit:
    total = len(memories)
    useful = 0
    conflicts = 0
    duplicates = 0
    seen_keys: set[tuple[Any, ...]] = set()
    for mem in memories:
        usefulness = mem.get("usefulness", 0)
        if isinstance(usefulness, (int, float)) and usefulness >= 0.5:
            useful += 1
        if mem.get("conflict"):
            conflicts += 1
        key = tuple(sorted((k, v) for k, v in mem.items() if k not in {"id", "usefulness"}))
        if key in seen_keys:
            duplicates += 1
        else:
            seen_keys.add(key)
    usefulness_ratio = (useful / total) if total else 0.0
    conflict_ratio = (conflicts / total) if total else 0.0
    recs: list[str] = []
    if usefulness_ratio < 0.5:
        recs.append("archive low-usefulness memories")
    if conflict_ratio > 0.1:
        recs.append("resolve conflicting memories")
    if duplicates > 0:
        recs.append(f"merge {duplicates} duplicate memories")
    return MemoryAudit(
        memory_count=total,
        useful_count=useful,
        conflicting_count=conflicts,
        duplicate_count=duplicates,
        usefulness_ratio=usefulness_ratio,
        conflict_ratio=conflict_ratio,
        recommendations=tuple(recs),
    )
