from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DomainScore:
    domain: str
    score: float
    weight: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def weighted(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "score": round(self.score, 4),
            "weight": round(self.weight, 4),
            "weighted": round(self.weighted(), 4),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class QualityScores:
    domain_scores: tuple[DomainScore, ...]
    overall: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_scores": [d.to_dict() for d in self.domain_scores],
            "overall": round(self.overall, 4),
            "notes": list(self.notes),
        }


def score_domain(
    *,
    domain: str,
    score: float,
    weight: float = 1.0,
    notes: tuple[str, ...] = (),
) -> DomainScore:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score must be in [0,1]; got {score}")
    if weight <= 0:
        raise ValueError(f"weight must be > 0; got {weight}")
    return DomainScore(
        domain=domain,
        score=score,
        weight=weight,
        notes=notes,
    )


def aggregate_scores(scores: tuple[DomainScore, ...]) -> QualityScores:
    if not scores:
        return QualityScores(
            domain_scores=(),
            overall=0.0,
            notes=("no domain scores",),
        )
    total_weight = sum(d.weight for d in scores)
    weighted_sum = sum(d.weighted() for d in scores)
    overall = (weighted_sum / total_weight) if total_weight else 0.0
    notes: list[str] = []
    low = [d.domain for d in scores if d.score < 0.5]
    if low:
        notes.append(f"low scoring domains: {low}")
    return QualityScores(
        domain_scores=scores,
        overall=overall,
        notes=tuple(notes),
    )
