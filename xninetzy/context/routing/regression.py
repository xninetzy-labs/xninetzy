from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


REGRESSION_VERSION = "1.0.0"

GATE_NAMES: tuple[str, ...] = (
    "routing_quality",
    "unsafe_action_rate",
    "tool_recall_topk",
    "abstention_band",
    "latency_p95_budget",
    "memory_budget",
    "e2e_task_success",
    "calibration_refresh",
    "shadow_agreement",
    "provider_override_rate",
    "documentation_freshness",
)


class RegressionStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class RegressionCheck:
    name: str
    status: RegressionStatus
    observed: str
    threshold: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "observed": self.observed,
            "threshold": self.threshold,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class RegressionReport:
    version: str
    generated_at: str
    checks: tuple[RegressionCheck, ...]
    overall: RegressionStatus
    block_reasons: tuple[str, ...] = ()
    legacy_snapshot_path: str | None = None
    candidate_snapshot_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "checks": [c.to_dict() for c in self.checks],
            "overall": self.overall.value,
            "block_reasons": list(self.block_reasons),
            "legacy_snapshot_path": self.legacy_snapshot_path,
            "candidate_snapshot_path": self.candidate_snapshot_path,
        }


def _check(name: str, passed: bool, observed: str, threshold: str, detail: str = "") -> RegressionCheck:
    return RegressionCheck(
        name=name,
        status=RegressionStatus.PASSED if passed else RegressionStatus.FAILED,
        observed=observed,
        threshold=threshold,
        detail=detail,
    )


def _skipped(name: str, reason: str) -> RegressionCheck:
    return RegressionCheck(
        name=name,
        status=RegressionStatus.SKIPPED,
        observed="n/a",
        threshold="n/a",
        detail=reason,
    )


def _load_report(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_top1(report: dict[str, Any] | None) -> float:
    if not report:
        return 0.0
    for sc in report.get("scorecards", []) or []:
        if sc.get("baseline") == "D-rules+embeddings":
            return float(sc.get("top1", 0.0))
    return 0.0


def _extract_p95(report: dict[str, Any] | None) -> float:
    if not report:
        return 0.0
    for sc in report.get("scorecards", []) or []:
        if sc.get("baseline") == "D-rules+embeddings":
            return float(sc.get("latency_p95_ms", 0.0))
    return 0.0


def _extract_topk(report: dict[str, Any] | None) -> float:
    if not report:
        return 0.0
    for sc in report.get("scorecards", []) or []:
        if sc.get("baseline") == "D-rules+embeddings":
            return float(sc.get("topk", 0.0))
    return 0.0


def _extract_abstention(report: dict[str, Any] | None) -> float:
    if not report:
        return 0.0
    for sc in report.get("scorecards", []) or []:
        if sc.get("baseline") == "D-rules+embeddings":
            return float(sc.get("abstention_rate", 0.0))
    return 0.0


def run_regression_gate(
    *,
    legacy_report_path: str | Path = "data/routing_benchmarks/legacy_snapshot.json",
    candidate_report_path: str | Path = "data/routing_benchmarks/latest.json",
    top1_drop_max: float = 0.01,
    topk_floor: float = 0.80,
    abstention_band: tuple[float, float] = (0.05, 0.25),
    p95_budget_ms: float = 500.0,
    memory_budget_mb: float = 1024.0,
    unsafe_action_max: float = 0.05,
    e2e_min_success: float = 0.70,
    calibration_max_ece: float = 0.07,
    shadow_min_agreement: float = 0.85,
    provider_override_max: float = 0.05,
    doc_max_age_days: int = 30,
    candidate_observed_top1: float | None = None,
    candidate_observed_p95: float | None = None,
    candidate_observed_topk: float | None = None,
    candidate_observed_abstention: float | None = None,
    unsafe_action_rate: float | None = None,
    e2e_task_success_rate: float | None = None,
    shadow_agreement: float | None = None,
    provider_override_rate: float | None = None,
    calibration_max_observed_ece: float | None = None,
    memory_peak_mb: float | None = None,
    doc_age_days: int | None = None,
) -> RegressionReport:
    legacy = _load_report(legacy_report_path)
    candidate_path = Path(candidate_report_path)
    if candidate_observed_top1 is None or candidate_observed_p95 is None:
        cand_payload = _load_report(candidate_path)
        if cand_payload is not None and candidate_observed_top1 is None:
            candidate_observed_top1 = _extract_top1(cand_payload)
        if cand_payload is not None and candidate_observed_p95 is None:
            candidate_observed_p95 = _extract_p95(cand_payload)
        if cand_payload is not None and candidate_observed_topk is None:
            candidate_observed_topk = _extract_topk(cand_payload)
        if cand_payload is not None and candidate_observed_abstention is None:
            candidate_observed_abstention = _extract_abstention(cand_payload)
    legacy_top1 = _extract_top1(legacy)
    legacy_p95 = _extract_p95(legacy)

    checks: list[RegressionCheck] = []
    blockers: list[str] = []

    if candidate_observed_top1 is None:
        checks.append(
            _skipped("routing_quality", "no candidate top1 observed")
        )
    else:
        if legacy_top1 > 0:
            observed = f"top1={candidate_observed_top1:.4f} legacy_top1={legacy_top1:.4f} drop={legacy_top1 - candidate_observed_top1:.4f}"
            ok = (legacy_top1 - candidate_observed_top1) <= top1_drop_max
            checks.append(
                _check(
                    "routing_quality",
                    ok,
                    observed,
                    f"top1_drop ≤ {top1_drop_max}",
                )
            )
            if not ok:
                blockers.append("routing_quality: top-1 regressed beyond allowed drop")
        else:
            checks.append(
                _check(
                    "routing_quality",
                    candidate_observed_top1 >= 0.70,
                    f"top1={candidate_observed_top1:.4f}",
                    "top1 ≥ 0.70 (no legacy baseline to compare)",
                )
            )

    if unsafe_action_rate is None:
        checks.append(_skipped("unsafe_action_rate", "FINAL-action rate not observed"))
    else:
        ok = unsafe_action_rate <= unsafe_action_max
        checks.append(
            _check(
                "unsafe_action_rate",
                ok,
                f"final_rate={unsafe_action_rate:.4f}",
                f"≤{unsafe_action_max}",
            )
        )
        if not ok:
            blockers.append("unsafe_action_rate: exceeds safety threshold")

    if candidate_observed_topk is None:
        checks.append(_skipped("tool_recall_topk", "no candidate topk observed"))
    else:
        ok = candidate_observed_topk >= topk_floor
        checks.append(
            _check(
                "tool_recall_topk",
                ok,
                f"topk={candidate_observed_topk:.4f}",
                f"≥{topk_floor}",
            )
        )
        if not ok:
            blockers.append("tool_recall_topk: below mandatory floor")

    if candidate_observed_abstention is None:
        checks.append(_skipped("abstention_band", "no abstention rate observed"))
    else:
        lo, hi = abstention_band
        ok = lo <= candidate_observed_abstention <= hi
        checks.append(
            _check(
                "abstention_band",
                ok,
                f"abst={candidate_observed_abstention:.4f}",
                f"∈[{lo}, {hi}]",
            )
        )
        if not ok:
            blockers.append("abstention_band: outside acceptable range")

    if candidate_observed_p95 is None:
        checks.append(_skipped("latency_p95_budget", "no candidate p95 observed"))
    else:
        budget = p95_budget_ms + (legacy_p95 if legacy_p95 > 0 else 0.0) * 0.0
        ok = candidate_observed_p95 <= budget
        checks.append(
            _check(
                "latency_p95_budget",
                ok,
                f"p95={candidate_observed_p95:.1f}ms legacy_p95={legacy_p95:.1f}ms",
                f"≤{p95_budget_ms}ms",
            )
        )
        if not ok:
            blockers.append("latency_p95_budget: exceeds budget")

    if memory_peak_mb is None:
        checks.append(_skipped("memory_budget", "no memory peak observed"))
    else:
        ok = memory_peak_mb <= memory_budget_mb
        checks.append(
            _check(
                "memory_budget",
                ok,
                f"peak={memory_peak_mb:.0f}MB",
                f"≤{memory_budget_mb:.0f}MB",
            )
        )
        if not ok:
            blockers.append("memory_budget: exceeds budget")

    if e2e_task_success_rate is None:
        checks.append(_skipped("e2e_task_success", "no e2e success rate observed"))
    else:
        ok = e2e_task_success_rate >= e2e_min_success
        checks.append(
            _check(
                "e2e_task_success",
                ok,
                f"e2e={e2e_task_success_rate:.4f}",
                f"≥{e2e_min_success}",
            )
        )
        if not ok:
            blockers.append("e2e_task_success: below minimum")

    if calibration_max_observed_ece is None:
        checks.append(_skipped("calibration_refresh", "no calibration ECE observed"))
    else:
        ok = calibration_max_observed_ece <= calibration_max_ece
        checks.append(
            _check(
                "calibration_refresh",
                ok,
                f"max_ece={calibration_max_observed_ece:.4f}",
                f"≤{calibration_max_ece}",
            )
        )
        if not ok:
            blockers.append("calibration_refresh: ECE above threshold")

    if shadow_agreement is None:
        checks.append(_skipped("shadow_agreement", "no shadow comparison yet"))
    else:
        ok = shadow_agreement >= shadow_min_agreement
        checks.append(
            _check(
                "shadow_agreement",
                ok,
                f"agreement={shadow_agreement:.4f}",
                f"≥{shadow_min_agreement}",
            )
        )
        if not ok:
            blockers.append("shadow_agreement: below floor")

    if provider_override_rate is None:
        checks.append(_skipped("provider_override_rate", "no provider-override observed"))
    else:
        ok = provider_override_rate <= provider_override_max
        checks.append(
            _check(
                "provider_override_rate",
                ok,
                f"override={provider_override_rate:.4f}",
                f"≤{provider_override_max}",
            )
        )
        if not ok:
            blockers.append("provider_override_rate: above ceiling")

    if doc_age_days is None:
        checks.append(_skipped("documentation_freshness", "no doc age measured"))
    else:
        ok = doc_age_days <= doc_max_age_days
        checks.append(
            _check(
                "documentation_freshness",
                ok,
                f"age={doc_age_days}d",
                f"≤{doc_max_age_days}d",
            )
        )
        if not ok:
            blockers.append("documentation_freshness: docs stale")

    if any(c.status == RegressionStatus.FAILED for c in checks):
        overall = RegressionStatus.FAILED
    elif all(c.status == RegressionStatus.SKIPPED for c in checks):
        overall = RegressionStatus.SKIPPED
    else:
        overall = RegressionStatus.PASSED

    return RegressionReport(
        version=REGRESSION_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        checks=tuple(checks),
        overall=overall,
        block_reasons=tuple(blockers),
        legacy_snapshot_path=str(legacy_report_path),
        candidate_snapshot_path=str(candidate_path),
    )


def write_regression_report(
    report: RegressionReport,
    output_dir: str | Path = "data/routing_regression",
) -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat().replace(":", "").replace("-", "")[:15]
    path = root / f"regression-{stamp}.json"
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    (root / "latest.json").write_text(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    return str(path)
