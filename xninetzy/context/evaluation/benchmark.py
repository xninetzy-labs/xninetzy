from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class BenchmarkMetric:
    name: str
    baseline: float
    candidate: float
    higher_is_better: bool = True

    def delta(self) -> float:
        return self.candidate - self.baseline

    def improved(self) -> bool:
        return self.delta() > 0 if self.higher_is_better else self.delta() < 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "delta": round(self.delta(), 4),
            "higher_is_better": self.higher_is_better,
            "improved": self.improved(),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    name: str
    metrics: tuple[BenchmarkMetric, ...]
    overall_improved: bool
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "metrics": [m.to_dict() for m in self.metrics],
            "overall_improved": self.overall_improved,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    baseline_name: str
    candidate_name: str
    improvements: tuple[str, ...]
    regressions: tuple[str, ...]
    neutral: tuple[str, ...]
    net_score: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_name": self.baseline_name,
            "candidate_name": self.candidate_name,
            "improvements": list(self.improvements),
            "regressions": list(self.regressions),
            "neutral": list(self.neutral),
            "net_score": round(self.net_score, 4),
            "notes": list(self.notes),
        }


class BenchmarkEngine:
    def __init__(self) -> None:
        self._benchmarks: dict[str, BenchmarkResult] = {}

    def register(self, result: BenchmarkResult) -> None:
        self._benchmarks[result.name] = result

    def get(self, name: str) -> BenchmarkResult | None:
        return self._benchmarks.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._benchmarks))

    def clear(self) -> None:
        self._benchmarks.clear()


_ENGINE = BenchmarkEngine()


def get_engine() -> BenchmarkEngine:
    return _ENGINE


def run_benchmark(
    *,
    name: str,
    metrics: tuple[BenchmarkMetric, ...],
    notes: tuple[str, ...] = (),
) -> BenchmarkResult:
    overall = all(m.improved() for m in metrics) if metrics else False
    result = BenchmarkResult(
        name=name,
        metrics=metrics,
        overall_improved=overall,
        notes=notes,
    )
    _ENGINE.register(result)
    return result


def compare_to_benchmark(
    *,
    name: str,
    candidate_metrics: tuple[BenchmarkMetric, ...],
    notes: tuple[str, ...] = (),
) -> BenchmarkComparison:
    baseline = _ENGINE.get(name)
    if baseline is None:
        return BenchmarkComparison(
            baseline_name=name,
            candidate_name=f"{name}#candidate",
            improvements=(),
            regressions=(),
            neutral=tuple(m.name for m in candidate_metrics),
            net_score=0.0,
            notes=("no baseline registered",),
        )
    base_by_name = {m.name: m for m in baseline.metrics}
    improvements: list[str] = []
    regressions: list[str] = []
    neutral: list[str] = []
    net = 0.0
    for metric in candidate_metrics:
        base = base_by_name.get(metric.name)
        if base is None:
            neutral.append(metric.name)
            continue
        delta = metric.delta()
        if metric.improved():
            improvements.append(metric.name)
            net += abs(delta)
        elif abs(delta) < 1e-9:
            neutral.append(metric.name)
        else:
            regressions.append(metric.name)
            net -= abs(delta)
    return BenchmarkComparison(
        baseline_name=name,
        candidate_name=f"{name}#candidate",
        improvements=tuple(improvements),
        regressions=tuple(regressions),
        neutral=tuple(neutral),
        net_score=net,
        notes=notes,
    )
