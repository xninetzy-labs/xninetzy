from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.context.learning.statistics import delta_with_confidence

ABTestStatus: str = "active"
ABTestAccepted: str = "accepted"
ABTestRejected: str = "rejected"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


@dataclass(frozen=True, slots=True)
class ABTest:
    test_id: str
    baseline: str
    candidate: str
    metric_name: str
    status: str = ABTestStatus
    observations: tuple["ExperimentOutcome", ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "metric_name": self.metric_name,
            "status": self.status,
            "observations": [o.to_dict() for o in self.observations],
        }


@dataclass(frozen=True, slots=True)
class ExperimentOutcome:
    variant: str
    metric_value: float
    sample_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "metric_value": round(self.metric_value, 4),
            "sample_size": self.sample_size,
        }


@dataclass(frozen=True, slots=True)
class ABTestResult:
    test_id: str
    status: str
    baseline_avg: float | None
    candidate_avg: float | None
    delta: float | None
    sample_total: int
    winner: str | None
    confidence: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "status": self.status,
            "baseline_avg": round(self.baseline_avg, 4) if self.baseline_avg is not None else None,
            "candidate_avg": round(self.candidate_avg, 4) if self.candidate_avg is not None else None,
            "delta": round(self.delta, 4) if self.delta is not None else None,
            "sample_total": self.sample_total,
            "winner": self.winner,
            "confidence": round(self.confidence, 4),
            "notes": list(self.notes),
        }


def _load_test(test_id: str) -> ABTest | None:
    _ensure_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM ab_tests WHERE test_id=?",
            (test_id,),
        ).fetchone()
    if row is None:
        return None
    raw_obs = str(row["observations_json"] or "[]")
    try:
        observations_data = json.loads(raw_obs)
    except (TypeError, ValueError):
        observations_data = []
    observations = tuple(
        ExperimentOutcome(
            variant=str(item.get("variant", "")),
            metric_value=float(item.get("metric_value", 0.0)),
            sample_size=int(item.get("sample_size", 1)),
        )
        for item in observations_data
    )
    return ABTest(
        test_id=str(row["test_id"]),
        baseline=str(row["baseline"]),
        candidate=str(row["candidate"]),
        metric_name=str(row["metric_name"]),
        status=str(row["status"] or ABTestStatus),
        observations=observations,
    )


def create_ab_test(
    *,
    test_id: str,
    baseline: str,
    candidate: str,
    metric_name: str,
    owner_scope: str = "system",
) -> ABTest:
    if not test_id:
        raise ValueError("test_id required")
    if baseline == candidate:
        raise ValueError("baseline and candidate must differ")
    test = ABTest(
        test_id=test_id,
        baseline=baseline,
        candidate=candidate,
        metric_name=metric_name,
        status=ABTestStatus,
        observations=(),
    )
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO ab_tests
              (test_id, owner_scope, baseline, candidate, metric_name, status,
               winner, baseline_avg, candidate_avg, confidence, sample_total,
               observations_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_id,
                owner_scope,
                baseline,
                candidate,
                metric_name,
                ABTestStatus,
                None,
                None,
                None,
                0.0,
                0,
                "[]",
                _utcnow(),
                _utcnow(),
            ),
        )
    return test


def record_observation(
    *,
    test_id: str,
    outcome: ExperimentOutcome,
) -> ABTest:
    test = _load_test(test_id)
    if test is None:
        raise ValueError(f"unknown test_id {test_id!r}")
    updated = ABTest(
        test_id=test.test_id,
        baseline=test.baseline,
        candidate=test.candidate,
        metric_name=test.metric_name,
        status=test.status,
        observations=tuple([*test.observations, outcome]),
    )
    obs_json = json.dumps([o.to_dict() for o in updated.observations], ensure_ascii=False)
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE ab_tests SET observations_json=?, updated_at=? WHERE test_id=?
            """,
            (obs_json, _utcnow(), test_id),
        )
    return updated


def finalize_test(
    *,
    test_id: str,
    min_samples: int = 5,
    min_confidence: float = 0.6,
    higher_is_better: bool = True,
    use_welch: bool = True,
    alpha: float = 0.05,
) -> ABTestResult:
    test = _load_test(test_id)
    if test is None:
        raise ValueError(f"unknown test_id {test_id!r}")
    baseline_values = tuple(
        o.metric_value for o in test.observations if o.variant == test.baseline
    )
    candidate_values = tuple(
        o.metric_value for o in test.observations if o.variant == test.candidate
    )
    sample_total = len(baseline_values) + len(candidate_values)
    base_avg = _avg(baseline_values)
    cand_avg = _avg(candidate_values)
    delta = (
        (cand_avg - base_avg)
        if base_avg is not None and cand_avg is not None
        else None
    )
    winner: str | None = None
    confidence = 0.0
    notes: list[str] = []
    stat = delta_with_confidence(
        baseline_values,
        candidate_values,
        higher_is_better=higher_is_better,
        baseline_name=test.baseline,
        candidate_name=test.candidate,
    )
    if sample_total < min_samples:
        notes.append(
            f"insufficient samples ({sample_total} < {min_samples})"
        )
        status = ABTestStatus
    elif delta is None:
        notes.append("missing variant averages")
        status = ABTestStatus
    else:
        if use_welch:
            if stat["welch_t"] == float("inf"):
                confidence = 1.0
            else:
                confidence = 1.0 - float(stat["welch_p"])
            significant = bool(stat["significant"])
            winner = stat["winner"]
            if not significant:
                notes.append(
                    f"welch p={stat['welch_p']:.4f} not significant at alpha={alpha}"
                )
        else:
            magnitude = abs(delta)
            confidence = min(1.0, magnitude + min_samples / (min_samples + sample_total))
            if base_avg is None or cand_avg is None:
                winner = None
            elif higher_is_better:
                winner = test.candidate if delta > 0 else test.baseline if delta < 0 else None
            else:
                winner = test.candidate if delta < 0 else test.baseline if delta > 0 else None
        if confidence < min_confidence:
            notes.append(
                f"confidence {confidence:.2f} below threshold {min_confidence:.2f}"
            )
        status = (
            ABTestAccepted
            if winner is not None and confidence >= min_confidence
            else ABTestRejected
            if sample_total >= min_samples
            else ABTestStatus
        )
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE ab_tests SET status=?, winner=?, baseline_avg=?, candidate_avg=?,
                                confidence=?, sample_total=?, updated_at=?
            WHERE test_id=?
            """,
            (
                status,
                winner,
                base_avg,
                cand_avg,
                confidence,
                sample_total,
                _utcnow(),
                test_id,
            ),
        )
    return ABTestResult(
        test_id=test_id,
        status=status,
        baseline_avg=base_avg,
        candidate_avg=cand_avg,
        delta=delta,
        sample_total=sample_total,
        winner=winner,
        confidence=confidence,
        notes=tuple(notes),
    )


def _avg(values: tuple[float, ...]) -> float | None:
    return (sum(values) / len(values)) if values else None


def get_test(test_id: str) -> ABTest | None:
    return _load_test(test_id)


def list_tests() -> tuple[str, ...]:
    _ensure_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT test_id FROM ab_tests ORDER BY test_id"
        ).fetchall()
    return tuple(str(row["test_id"]) for row in rows)


def clear_tests() -> None:
    _ensure_db()
    with connect() as conn:
        conn.execute("DELETE FROM ab_tests")
