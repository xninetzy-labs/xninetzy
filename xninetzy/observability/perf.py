from __future__ import annotations

import time
from contextlib import contextmanager
from threading import Lock
from typing import Iterator


_METRICS: dict[str, list[float]] = {}
_LOCK = Lock()


@contextmanager
def measure(label: str) -> Iterator[None]:
    """Context manager to record wall-clock duration under a label."""
    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - started) * 1000.0
        with _LOCK:
            _METRICS.setdefault(label, []).append(elapsed)


def snapshot() -> dict:
    """Return p50/p95/avg per label from all measurements collected so far."""
    out: dict[str, dict] = {}
    with _LOCK:
        for label, samples in _METRICS.items():
            if not samples:
                continue
            ordered = sorted(samples)
            n = len(ordered)
            p50 = ordered[min(n - 1, int(0.50 * (n - 1)))]
            p95 = ordered[min(n - 1, int(0.95 * (n - 1)))]
            out[label] = {
                "samples": n,
                "avg_ms": round(sum(samples) / n, 3),
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "max_ms": round(max(samples), 3),
            }
    return out


def reset() -> None:
    with _LOCK:
        _METRICS.clear()
