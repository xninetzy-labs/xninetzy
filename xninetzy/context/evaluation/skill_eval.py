from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SKILL_EXCELLENT: str = "excellent"
SKILL_USEFUL: str = "useful"
SKILL_NEUTRAL: str = "neutral"
SKILL_POOR: str = "poor"
SKILL_DEPRECATED: str = "deprecated"

VALID_SKILL_VERDICTS: frozenset[str] = frozenset(
    {
        SKILL_EXCELLENT,
        SKILL_USEFUL,
        SKILL_NEUTRAL,
        SKILL_POOR,
        SKILL_DEPRECATED,
    }
)


@dataclass(frozen=True, slots=True)
class SkillAudit:
    skill_name: str
    invocation_count: int
    success_count: int
    reuse_count: int
    complexity_score: float
    verdict: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "invocation_count": self.invocation_count,
            "success_count": self.success_count,
            "reuse_count": self.reuse_count,
            "complexity_score": round(self.complexity_score, 4),
            "verdict": self.verdict,
            "notes": list(self.notes),
        }


def evaluate_skill(
    *,
    skill_name: str,
    invocation_count: int,
    success_count: int,
    reuse_count: int = 0,
    complexity_score: float = 0.5,
) -> SkillAudit:
    if invocation_count <= 0:
        return SkillAudit(
            skill_name=skill_name,
            invocation_count=0,
            success_count=0,
            reuse_count=0,
            complexity_score=complexity_score,
            verdict=SKILL_DEPRECATED,
            notes=("never invoked",),
        )
    success_rate = success_count / invocation_count
    reuse_ratio = reuse_count / invocation_count
    notes: list[str] = []
    if success_rate >= 0.9 and reuse_ratio >= 0.4:
        verdict = SKILL_EXCELLENT
    elif success_rate >= 0.7:
        verdict = SKILL_USEFUL
    elif success_rate >= 0.4:
        verdict = SKILL_NEUTRAL
    else:
        verdict = SKILL_POOR
        notes.append("consider deprecation or rework")
    if reuse_ratio < 0.1 and invocation_count >= 5:
        notes.append("low reuse — consider retiring")
    if complexity_score > 0.8:
        notes.append("high complexity — consider splitting")
    return SkillAudit(
        skill_name=skill_name,
        invocation_count=invocation_count,
        success_count=success_count,
        reuse_count=reuse_count,
        complexity_score=complexity_score,
        verdict=verdict,
        notes=tuple(notes),
    )
