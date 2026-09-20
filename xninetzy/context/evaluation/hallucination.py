from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

HALLUCINATION_LEVEL_NONE: str = "none"
HALLUCINATION_LEVEL_LOW: str = "low"
HALLUCINATION_LEVEL_MEDIUM: str = "medium"
HALLUCINATION_LEVEL_HIGH: str = "high"
HALLUCINATION_LEVEL_CRITICAL: str = "critical"

VALID_HALLUCINATION_LEVELS: frozenset[str] = frozenset(
    {
        HALLUCINATION_LEVEL_NONE,
        HALLUCINATION_LEVEL_LOW,
        HALLUCINATION_LEVEL_MEDIUM,
        HALLUCINATION_LEVEL_HIGH,
        HALLUCINATION_LEVEL_CRITICAL,
    }
)


HALLUCINATION_MARKERS: tuple[str, ...] = (
    "as far as i know",
    "i believe",
    "i think",
    "probably",
    "maybe",
    "it should",
    "should be",
    "might be",
    "could be",
)


@dataclass(frozen=True, slots=True)
class HallucinationAudit:
    level: str
    flagged_claims: tuple[str, ...]
    hedging_score: float
    unsupported_claim_count: int
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "flagged_claims": list(self.flagged_claims),
            "hedging_score": round(self.hedging_score, 4),
            "unsupported_claim_count": self.unsupported_claim_count,
            "notes": list(self.notes),
        }


def detect_hallucination(
    *,
    claims: tuple[str, ...],
    supported_refs: dict[str, tuple[str, ...]] | None = None,
) -> HallucinationAudit:
    supported = supported_refs or {}
    flagged: list[str] = []
    unsupported = 0
    hedging_hits = 0
    for index, claim in enumerate(claims):
        key = str(index)
        lowered = claim.lower()
        if any(marker in lowered for marker in HALLUCINATION_MARKERS):
            hedging_hits += 1
            flagged.append(f"hedging:{claim}")
        if supported.get(key):
            continue
        unsupported += 1
        flagged.append(f"unsupported:{claim}")
    hedging_score = hedging_hits / max(1, len(claims))
    if unsupported == 0 and hedging_hits == 0:
        level = HALLUCINATION_LEVEL_NONE
    elif unsupported >= max(2, len(claims) // 2):
        level = HALLUCINATION_LEVEL_CRITICAL
    elif unsupported >= 2 or hedging_score >= 0.5:
        level = HALLUCINATION_LEVEL_HIGH
    elif unsupported >= 1:
        level = HALLUCINATION_LEVEL_MEDIUM
    else:
        level = HALLUCINATION_LEVEL_LOW
    notes: list[str] = []
    if hedging_hits:
        notes.append(f"{hedging_hits} hedging claims detected")
    if unsupported:
        notes.append(f"{unsupported} unsupported claims")
    return HallucinationAudit(
        level=level,
        flagged_claims=tuple(flagged),
        hedging_score=hedging_score,
        unsupported_claim_count=unsupported,
        notes=tuple(notes),
    )
