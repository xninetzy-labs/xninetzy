from __future__ import annotations

import math
from typing import Any


def wilson_score(
    successes: float,
    trials: float,
    z: float = 1.96,
) -> float:
    """Lower bound of Wilson score interval (95% z=1.96). Returns 0..1."""
    if trials <= 0:
        return 0.0
    successes = max(0.0, min(successes, trials))
    p = successes / trials
    p = max(0.0, min(p, 1.0))
    denom = 1.0 + (z * z) / trials
    center = p + (z * z) / (2.0 * trials)
    variance_term = (p * (1.0 - p) / trials) + (z * z) / (4.0 * trials * trials)
    variance_term = max(0.0, variance_term)
    margin = z * math.sqrt(variance_term)
    lower = (center - margin) / denom
    return max(0.0, min(1.0, lower))


def welch_t(
    a_values: tuple[float, ...],
    b_values: tuple[float, ...],
) -> tuple[float, float]:
    """Welch's t-statistic and approximate p-value via two-sided normal approx.
    Returns (t_stat, p_value_two_sided). Returns (0.0, 1.0) if either sample < 2."""
    if len(a_values) < 2 or len(b_values) < 2:
        return 0.0, 1.0
    ma = sum(a_values) / len(a_values)
    mb = sum(b_values) / len(b_values)
    va = sum((v - ma) ** 2 for v in a_values) / (len(a_values) - 1)
    vb = sum((v - mb) ** 2 for v in b_values) / (len(b_values) - 1)
    se_sq = va / len(a_values) + vb / len(b_values)
    if se_sq <= 1e-12:
        if abs(ma - mb) < 1e-9:
            return 0.0, 1.0
        return float("inf"), 0.0
    se = math.sqrt(se_sq)
    t = (mb - ma) / se
    z_abs = abs(t)
    p = math.erfc(z_abs / math.sqrt(2.0))
    return t, max(0.0, min(1.0, p))


def delta_with_confidence(
    baseline_values: tuple[float, ...],
    candidate_values: tuple[float, ...],
    higher_is_better: bool,
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
) -> dict[str, Any]:
    """Compute delta + Welch p + Wilson lower bound for candidate success-rate."""
    if not baseline_values or not candidate_values:
        return {
            "delta": None,
            "welch_t": 0.0,
            "welch_p": 1.0,
            "wilson_lower": 0.0,
            "winner": None,
            "significant": False,
        }
    base_avg = sum(baseline_values) / len(baseline_values)
    cand_avg = sum(candidate_values) / len(candidate_values)
    raw_delta = cand_avg - base_avg
    t, p = welch_t(baseline_values, candidate_values)
    wilson = wilson_score(cand_avg, 1.0)
    delta_clear = abs(raw_delta) > 1e-9
    if higher_is_better:
        winner = candidate_name if raw_delta > 0 else baseline_name if raw_delta < 0 else None
        significant = (p < 0.05 or t == float("inf")) and raw_delta > 0 and delta_clear
    else:
        winner = candidate_name if raw_delta < 0 else baseline_name if raw_delta > 0 else None
        significant = (p < 0.05 or t == float("inf")) and raw_delta < 0 and delta_clear
    return {
        "delta": raw_delta,
        "welch_t": t,
        "welch_p": p,
        "wilson_lower": wilson,
        "winner": winner,
        "significant": significant,
    }
