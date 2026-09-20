from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

PATTERN_TYPE_SUCCESS: str = "success"
PATTERN_TYPE_FAILURE: str = "failure"


@dataclass(frozen=True, slots=True)
class PatternSignal:
    pattern_id: str
    pattern_type: str
    frequency: int
    context_key: str
    summary: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "frequency": self.frequency,
            "context_key": self.context_key,
            "summary": self.summary,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class DetectedPattern:
    signals: tuple[PatternSignal, ...]
    success_patterns: tuple[str, ...]
    failure_patterns: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signals": [s.to_dict() for s in self.signals],
            "success_patterns": list(self.success_patterns),
            "failure_patterns": list(self.failure_patterns),
            "notes": list(self.notes),
        }


def detect_patterns(
    *,
    observations: tuple[dict[str, Any], ...],
    min_frequency: int = 3,
    context_keys: tuple[str, ...] = (),
) -> DetectedPattern:
    counter: Counter[tuple[str, str, str]] = Counter()
    notes: list[str] = []
    filtered = observations
    if context_keys:
        filtered = tuple(
            obs for obs in observations
            if obs.get("context_key") in context_keys
        )
        if len(filtered) < len(observations):
            notes.append(f"filtered to {len(context_keys)} contexts")
    for obs in filtered:
        outcome = str(obs.get("outcome", ""))
        category = str(obs.get("category", ""))
        ctx = str(obs.get("context_key", ""))
        if outcome not in ("success", "failure"):
            continue
        counter[(ctx, category, outcome)] += 1
    signals: list[PatternSignal] = []
    success: list[str] = []
    failure: list[str] = []
    for (ctx, category, outcome), freq in counter.items():
        if freq < min_frequency:
            continue
        pattern_type = (
            PATTERN_TYPE_SUCCESS if outcome == "success" else PATTERN_TYPE_FAILURE
        )
        pattern_id = f"{ctx}:{category}:{outcome}"
        summary = (
            f"context={ctx} category={category} "
            f"outcome={outcome} frequency={freq}"
        )
        signals.append(
            PatternSignal(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                frequency=freq,
                context_key=ctx,
                summary=summary,
            )
        )
        if outcome == "success":
            success.append(pattern_id)
        else:
            failure.append(pattern_id)
    if not signals:
        notes.append("no patterns above frequency threshold")
    return DetectedPattern(
        signals=tuple(signals),
        success_patterns=tuple(success),
        failure_patterns=tuple(failure),
        notes=tuple(notes),
    )
