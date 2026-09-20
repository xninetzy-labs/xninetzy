from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ContextAudit:
    retrieved_count: int
    relevant_count: int
    stale_count: int
    duplicate_count: int
    precision: float
    recall: float
    freshness: float
    coverage: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieved_count": self.retrieved_count,
            "relevant_count": self.relevant_count,
            "stale_count": self.stale_count,
            "duplicate_count": self.duplicate_count,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "freshness": round(self.freshness, 4),
            "coverage": round(self.coverage, 4),
            "notes": list(self.notes),
        }


def evaluate_context(
    *,
    retrieved: tuple[str, ...],
    relevant: tuple[str, ...],
    required: tuple[str, ...],
    stale: tuple[str, ...] = (),
    duplicates: tuple[str, ...] = (),
) -> ContextAudit:
    retrieved_set = set(retrieved)
    relevant_set = set(retrieved_set & set(relevant))
    stale_set = set(retrieved_set & set(stale))
    duplicate_set = set(retrieved_set & set(duplicates))
    required_set = set(required)
    precision = (len(relevant_set) / len(retrieved_set)) if retrieved_set else 0.0
    recall = (len(relevant_set) / len(required_set)) if required_set else 1.0
    fresh_count = len(retrieved_set - stale_set)
    freshness = (fresh_count / len(retrieved_set)) if retrieved_set else 1.0
    coverage = (len(relevant_set) / max(1, len(required_set)))
    notes: list[str] = []
    if precision < 0.4:
        notes.append("precision low — many irrelevant items")
    if recall < 0.5:
        notes.append("recall low — required items missing")
    if freshness < 0.7:
        notes.append("freshness low — stale items present")
    if duplicate_set:
        notes.append(f"duplicates present: {len(duplicate_set)}")
    return ContextAudit(
        retrieved_count=len(retrieved_set),
        relevant_count=len(relevant_set),
        stale_count=len(stale_set),
        duplicate_count=len(duplicate_set),
        precision=precision,
        recall=recall,
        freshness=freshness,
        coverage=coverage,
        notes=tuple(notes),
    )
