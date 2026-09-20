from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ROOT_CAUSE_CONFIDENCE_HIGH: str = "high"
ROOT_CAUSE_CONFIDENCE_MEDIUM: str = "medium"
ROOT_CAUSE_CONFIDENCE_LOW: str = "low"


@dataclass(frozen=True, slots=True)
class RootCauseAnalysis:
    symptom: str
    root_cause: str
    contributing_factors: tuple[str, ...]
    confidence: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symptom": self.symptom,
            "root_cause": self.root_cause,
            "contributing_factors": list(self.contributing_factors),
            "confidence": self.confidence,
            "evidence_refs": list(self.evidence_refs),
            "notes": list(self.notes),
        }


def analyze_root_cause(
    *,
    symptom: str,
    hypotheses: tuple[str, ...],
    evidence_refs: tuple[str, ...] = (),
    confidence_threshold: float = 0.7,
) -> RootCauseAnalysis:
    if not hypotheses:
        return RootCauseAnalysis(
            symptom=symptom,
            root_cause="undetermined",
            contributing_factors=(),
            confidence=ROOT_CAUSE_CONFIDENCE_LOW,
            evidence_refs=evidence_refs,
            notes=("no hypotheses provided",),
        )
    chosen = hypotheses[0]
    confidence = ROOT_CAUSE_CONFIDENCE_LOW
    note_extra = ""
    if len(evidence_refs) >= 3:
        confidence = ROOT_CAUSE_CONFIDENCE_HIGH
        note_extra = "multiple evidence sources"
    elif len(evidence_refs) >= 1:
        confidence = ROOT_CAUSE_CONFIDENCE_MEDIUM
        note_extra = "single evidence source"
    if confidence_threshold > 0.9 and confidence != ROOT_CAUSE_CONFIDENCE_HIGH:
        confidence = ROOT_CAUSE_CONFIDENCE_LOW
    return RootCauseAnalysis(
        symptom=symptom,
        root_cause=chosen,
        contributing_factors=tuple(hypotheses[1:]),
        confidence=confidence,
        evidence_refs=evidence_refs,
        notes=(note_extra,) if note_extra else (),
    )
