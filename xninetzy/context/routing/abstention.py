from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_ABSTENTION_MIN = 0.05
DEFAULT_ABSTENTION_MAX = 0.25
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.40
DEFAULT_MARGIN_THRESHOLD = 0.10


@dataclass(frozen=True, slots=True)
class AbstentionResult:
    should_abstain: bool
    reason_codes: tuple[str, ...] = ()
    abstention_rate_estimate: float = 0.0
    selected: tuple[str, ...] = ()
    confidence: dict[str, float] = field(default_factory=dict)


def decide_abstention(
    *,
    confidence: dict[str, float],
    top_k: int = 5,
    low_conf_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
    min_abstention_rate: float = DEFAULT_ABSTENTION_MIN,
    max_abstention_rate: float = DEFAULT_ABSTENTION_MAX,
    historical_abstention_rate: float = 0.0,
) -> AbstentionResult:
    if not confidence:
        return AbstentionResult(
            should_abstain=True,
            reason_codes=("abstain_empty_confidence",),
            abstention_rate_estimate=1.0,
        )
    ordered = sorted(confidence.items(), key=lambda x: x[1], reverse=True)
    selected = tuple(name for name, _ in ordered[:top_k])
    top_score = ordered[0][1]
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    margin = top_score - second_score
    reasons: list[str] = []
    if top_score < low_conf_threshold:
        reasons.append(f"abstain_low_conf={top_score:.3f}<{low_conf_threshold:.3f}")
    if margin < margin_threshold:
        reasons.append(f"abstain_low_margin={margin:.3f}<{margin_threshold:.3f}")
    should_abstain = bool(reasons)
    target_abstention = _target_abstention(
        historical=historical_abstention_rate,
        lo=min_abstention_rate,
        hi=max_abstention_rate,
    )
    if should_abstain and historical_abstention_rate < target_abstention:
        reasons.append(
            f"abstain_below_band={historical_abstention_rate:.3f}<{target_abstention:.3f}"
        )
    if not should_abstain and historical_abstention_rate < min_abstention_rate:
        should_abstain = True
        reasons.append(
            f"abstain_floor_below_min={historical_abstention_rate:.3f}<{min_abstention_rate:.3f}"
        )
    if should_abstain and historical_abstention_rate > max_abstention_rate:
        should_abstain = False
        reasons = [f"abstain_ceiling_above_max={historical_abstention_rate:.3f}>{max_abstention_rate:.3f}"]
    return AbstentionResult(
        should_abstain=should_abstain,
        reason_codes=tuple(reasons),
        abstention_rate_estimate=1.0 if should_abstain else 0.0,
        selected=selected if not should_abstain else (),
        confidence=dict(confidence),
    )


def _target_abstention(*, historical: float, lo: float, hi: float) -> float:
    if historical >= lo:
        return historical
    return lo
