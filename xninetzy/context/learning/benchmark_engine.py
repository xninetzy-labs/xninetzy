from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


@dataclass(frozen=True, slots=True)
class LearningBenchmark:
    name: str
    category: str
    description: str
    target_metrics: tuple[str, ...]
    last_score: float | None = None
    last_run_at: str | None = None
    baseline_score: float = 0.0
    delta: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "target_metrics": list(self.target_metrics),
            "last_score": round(self.last_score, 4) if self.last_score is not None else None,
            "baseline_score": round(self.baseline_score, 4),
            "delta": round(self.delta, 4),
            "last_run_at": self.last_run_at,
        }


class LearningBenchmarkRegistry:
    def __init__(self) -> None:
        self._items: dict[str, LearningBenchmark] = {}

    def register(self, benchmark: LearningBenchmark) -> None:
        self._items[benchmark.name] = benchmark

    def get(self, name: str) -> LearningBenchmark | None:
        return self._items.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def clear(self) -> None:
        self._items.clear()


_REGISTRY = LearningBenchmarkRegistry()


def get_benchmark_registry() -> LearningBenchmarkRegistry:
    return _REGISTRY


def reset_benchmark_registry() -> None:
    _REGISTRY.clear()


def register_benchmark(
    *,
    name: str,
    category: str,
    description: str,
    target_metrics: tuple[str, ...],
    owner_scope: str = "system",
) -> LearningBenchmark:
    benchmark = LearningBenchmark(
        name=name,
        category=category,
        description=description,
        target_metrics=target_metrics,
    )
    _REGISTRY.register(benchmark)
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO learning_benchmarks
              (name, owner_scope, category, description, target_metrics_json,
               last_score, baseline_score, delta, last_run_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                owner_scope,
                category,
                description,
                json.dumps(list(target_metrics), ensure_ascii=False),
                0.0,
                0.0,
                0.0,
                _utcnow(),
            ),
        )
    return benchmark


def run_learning_benchmark(
    *,
    name: str,
    score: float,
    last_run_at: str,
    owner_scope: str = "system",
) -> LearningBenchmark:
    existing = _REGISTRY.get(name)
    if existing is None:
        raise ValueError(f"benchmark {name!r} not registered")
    bounded = float(max(0.0, min(score, 1.0)))
    baseline = float(existing.baseline_score) if existing.baseline_score else bounded
    if not existing.last_score:
        baseline = bounded
    delta = bounded - baseline
    updated = LearningBenchmark(
        name=existing.name,
        category=existing.category,
        description=existing.description,
        target_metrics=existing.target_metrics,
        last_score=bounded,
        last_run_at=last_run_at,
        baseline_score=baseline,
        delta=delta,
    )
    _REGISTRY.register(updated)
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE learning_benchmarks
            SET last_score=?, baseline_score=?, delta=?, last_run_at=?
            WHERE name=? AND owner_scope=?
            """,
            (bounded, baseline, delta, last_run_at, name, owner_scope),
        )
    return updated
