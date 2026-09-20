from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LEARN: str = "learn"
MONITOR: str = "monitor"
IGNORE: str = "ignore"

VALID_SIGNAL_ACTIONS: frozenset[str] = frozenset({LEARN, MONITOR, IGNORE})


@dataclass(frozen=True, slots=True)
class LearningSignal:
    source: str
    action: str
    confidence: float
    summary: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "action": self.action,
            "confidence": round(self.confidence, 4),
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class LearningSignalBatch:
    signals: tuple[LearningSignal, ...]
    learn_count: int
    monitor_count: int
    ignore_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "signals": [s.to_dict() for s in self.signals],
            "learn_count": self.learn_count,
            "monitor_count": self.monitor_count,
            "ignore_count": self.ignore_count,
        }


_MIN_CONFIDENCE_TO_LEARN: float = 0.7
_MIN_CONFIDENCE_TO_MONITOR: float = 0.4


def extract_signals(
    *,
    findings: tuple[dict[str, Any], ...],
    min_confidence_to_learn: float = _MIN_CONFIDENCE_TO_LEARN,
    min_confidence_to_monitor: float = _MIN_CONFIDENCE_TO_MONITOR,
) -> LearningSignalBatch:
    signals: list[LearningSignal] = []
    learn = 0
    monitor = 0
    ignore = 0
    for finding in findings:
        confidence = float(finding.get("confidence", 0.0) or 0.0)
        source = str(finding.get("source", "unknown"))
        summary = str(finding.get("summary", ""))
        if confidence >= min_confidence_to_learn:
            action = LEARN
            learn += 1
        elif confidence >= min_confidence_to_monitor:
            action = MONITOR
            monitor += 1
        else:
            action = IGNORE
            ignore += 1
        signals.append(
            LearningSignal(
                source=source,
                action=action,
                confidence=confidence,
                summary=summary,
                evidence_refs=tuple(finding.get("evidence_refs", ()) or ()),
                notes=tuple(finding.get("notes", ()) or ()),
            )
        )
    return LearningSignalBatch(
        signals=tuple(signals),
        learn_count=learn,
        monitor_count=monitor,
        ignore_count=ignore,
    )
