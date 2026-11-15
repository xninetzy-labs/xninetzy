from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xninetzy.context.routing.baselines import (
    CombinedBaseline,
)
from xninetzy.context.routing.pipeline import run_pipeline

SHADOW_VERSION = "1.0.0"
SHADOW_DEFAULT_SAMPLE_RATE = 0.10


@dataclass(frozen=True, slots=True)
class ShadowDecision:
    run_id: str
    query: str
    timestamp: str
    legacy_top1: str
    legacy_topk: tuple[str, ...]
    new_top1: str
    new_topk: tuple[str, ...]
    agreement_top1: bool
    agreement_topk: int
    domain_overlap: tuple[str, ...]
    latency_legacy_ms: float
    latency_new_ms: float
    sampling_rate: float
    reason_codes: tuple[str, ...] = ()


class ShadowStore:
    def __init__(self, storage_dir: str | Path = "data/routing_shadow") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[ShadowDecision] = []

    def append(self, decision: ShadowDecision) -> None:
        self._records.append(decision)
        daily = self.storage_dir / f"{decision.timestamp[:10]}.jsonl"
        daily.parent.mkdir(parents=True, exist_ok=True)
        with open(daily, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(decision), ensure_ascii=False, default=str) + "\n")

    def records(self) -> list[ShadowDecision]:
        return list(self._records)


def _legacy_route(query: str, baseline: Any) -> dict[str, Any]:
    decision = baseline.route(query, top_k=5)
    selected = list(decision.selected)
    return {
        "top1": selected[0] if selected else "",
        "topk": tuple(selected),
        "latency_ms": float(decision.latency_ms),
    }


def _new_route(query: str) -> dict[str, Any]:
    import time as _t

    t0 = _t.perf_counter()
    outcome = run_pipeline(query, persist=False, idempotency_key=None)
    elapsed = (_t.perf_counter() - t0) * 1000.0
    selected = [outcome.selected_tool] + list(outcome.tool_decision.selected[1:5])
    return {
        "top1": outcome.selected_tool,
        "topk": tuple(selected),
        "latency_ms": elapsed,
    }


def run_shadow_once(
    query: str,
    *,
    store: ShadowStore | None = None,
    legacy_baseline: Any | None = None,
    sampling_rate: float = SHADOW_DEFAULT_SAMPLE_RATE,
    run_id: str | None = None,
) -> ShadowDecision:
    if legacy_baseline is None:
        legacy_baseline = CombinedBaseline()
    legacy = _legacy_route(query, legacy_baseline)
    new = _new_route(query)
    agreement_top1 = bool(legacy["top1"]) and bool(new["top1"]) and legacy["top1"] == new["top1"]
    agreement_topk = len(set(legacy["topk"]) & set(new["topk"]))
    rid = run_id or f"shadow-{abs(hash(query)) % 10**9}"
    decision = ShadowDecision(
        run_id=rid,
        query=query,
        timestamp=datetime.now(UTC).isoformat(),
        legacy_top1=str(legacy["top1"]),
        legacy_topk=tuple(legacy["topk"]),
        new_top1=str(new["top1"]),
        new_topk=tuple(new["topk"]),
        agreement_top1=agreement_top1,
        agreement_topk=agreement_topk,
        domain_overlap=(),
        latency_legacy_ms=float(legacy["latency_ms"]),
        latency_new_ms=float(new["latency_ms"]),
        sampling_rate=float(sampling_rate),
        reason_codes=("shadow_compare",),
    )
    if store is not None:
        store.append(decision)
    return decision


def compare_summary(decisions: list[Any]) -> dict[str, Any]:
    if not decisions:
        return {"n": 0}
    n = len(decisions)
    agreement = sum(1 for d in decisions if _get(d, "agreement_top1"))
    avg_topk_overlap = sum(_get(d, "agreement_topk") for d in decisions) / n
    latencies = [_get(d, "latency_new_ms") for d in decisions]
    latencies = [latency for latency in latencies if isinstance(latency, (int, float))]
    if not latencies:
        return {
            "n": n,
            "agreement_top1": agreement / n,
            "avg_topk_overlap": avg_topk_overlap,
            "new_latency_p50_ms": 0.0,
            "new_latency_p95_ms": 0.0,
            "new_latency_max_ms": 0.0,
        }
    p50 = sorted(latencies)[n // 2]
    p95_idx = max(0, min(len(latencies) - 1, int(len(latencies) * 0.95)))
    p95 = sorted(latencies)[p95_idx]
    return {
        "n": n,
        "agreement_top1": agreement / n,
        "avg_topk_overlap": avg_topk_overlap,
        "new_latency_p50_ms": p50,
        "new_latency_p95_ms": p95,
        "new_latency_max_ms": max(latencies),
    }


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, False)
    return getattr(obj, key, False)
