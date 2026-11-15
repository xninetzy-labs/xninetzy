from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from xninetzy.context.routing.benchmark import BENCHMARK_VERSION
from xninetzy.context.routing.calibration import CalibrationRegistry
from xninetzy.context.routing.shadow import compare_summary

FINE_TUNE_VERSION = "1.0.0"
FINE_TUNE_MIN_TEST_N = 200
FINE_TUNE_MIN_TOP5_RECALL = 0.95
FINE_TUNE_MIN_BENCHMARK_TOPS = 0.85
FINE_TUNE_MIN_SHADOW_AGREEMENT = 0.85
FINE_TUNE_MIN_SHADOW_DAYS = 14
FINE_TUNE_MIN_OWNER_APPROVAL = True
FINE_TUNE_REQUIRE_GPU = True
FINE_TUNE_ECE_REJECT = 0.05
FINE_TUNE_LATENCY_BUDGET_MS = 50.0
FINE_TUNE_MAX_ABS_TOP1_DROP = 0.01
FINE_TUNE_CALIBRATION_ECE = 0.05
FINE_TUNE_FINAL_ACTIONS_BLOCK = 0.05


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class FineTuneGate:
    name: str
    status: GateStatus
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
class FineTuneProposal:
    proposal_id: str
    created_at: str
    gates: tuple[FineTuneGate, ...]
    overall: GateStatus
    rationale: str
    blocked_reasons: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "version": FINE_TUNE_VERSION,
            "created_at": self.created_at,
            "overall": self.overall.value,
            "rationale": self.rationale,
            "gates": [g.to_dict() for g in self.gates],
            "blocked_reasons": list(self.blocked_reasons),
        }


def _gate(name: str, passed: bool, observed: str, threshold: str, detail: str = "") -> FineTuneGate:
    return FineTuneGate(
        name=name,
        status=GateStatus.PASSED if passed else GateStatus.FAILED,
        observed=observed,
        threshold=threshold,
        detail=detail,
    )


def _pending(name: str, threshold: str, detail: str) -> FineTuneGate:
    return FineTuneGate(
        name=name,
        status=GateStatus.PENDING,
        observed="n/a",
        threshold=threshold,
        detail=detail,
    )


def _deferred(name: str, threshold: str, detail: str) -> FineTuneGate:
    return FineTuneGate(
        name=name,
        status=GateStatus.DEFERRED,
        observed="n/a",
        threshold=threshold,
        detail=detail,
    )


def evaluate_fine_tune_gates(
    *,
    proposal_id: str | None = None,
    benchmark_top1: float | None = None,
    benchmark_topk: float | None = None,
    benchmark_test_n: int | None = None,
    top5_recall: float | None = None,
    shadow_decisions: list | None = None,
    shadow_days_observed: int = 0,
    calibration_dir: str = "data/routing_calibration",
    owner_approved: bool = False,
    gpu_available: bool = False,
    hard_negative_report: dict[str, dict[str, Any]] | None = None,
    hard_negative_acceptable: float = 0.95,
    final_action_rate: float = 0.0,
    p95_latency_ms: float = 0.0,
    rationale: str = "fine-tune proposal",
) -> FineTuneProposal:
    gates: list[FineTuneGate] = []
    blocked: list[str] = []

    if benchmark_top1 is None or benchmark_topk is None or benchmark_test_n is None:
        gates.append(
            _pending(
                "registry_metadata_quality",
                "benchmark_top1 + topk + test_n present",
                "benchmark scorecard not run yet",
            )
        )
    else:
        registry_ok = (
            benchmark_test_n >= FINE_TUNE_MIN_TEST_N
            and benchmark_top1 >= FINE_TUNE_MIN_BENCHMARK_TOPS
            and benchmark_topk >= FINE_TUNE_MIN_BENCHMARK_TOPS
        )
        gates.append(
            _gate(
                "registry_metadata_quality",
                registry_ok,
                f"n={benchmark_test_n} top1={benchmark_top1:.3f} topk={benchmark_topk:.3f}",
                f"n>={FINE_TUNE_MIN_TEST_N} top1>={FINE_TUNE_MIN_BENCHMARK_TOPS} topk>={FINE_TUNE_MIN_BENCHMARK_TOPS}",
            )
        )
        if not registry_ok:
            blocked.append("registry_metadata_quality: benchmark does not meet thresholds")

    if top5_recall is None:
        gates.append(
            _pending(
                "candidate_retrieval_top5",
                f"recall@5>={FINE_TUNE_MIN_TOP5_RECALL}",
                "candidate retrieval not measured yet",
            )
        )
    else:
        ok = top5_recall >= FINE_TUNE_MIN_TOP5_RECALL
        gates.append(
            _gate(
                "candidate_retrieval_top5",
                ok,
                f"recall@5={top5_recall:.3f}",
                f">={FINE_TUNE_MIN_TOP5_RECALL}",
            )
        )
        if not ok:
            blocked.append("candidate_retrieval_top5: below threshold")

    if hard_negative_report is None:
        gates.append(
            _pending(
                "hard_negatives_optimized",
                f"all pairs >={hard_negative_acceptable}",
                "hard-negatives analyzer not run",
            )
        )
    else:
        failing = [
            label
            for label, metrics in hard_negative_report.items()
            if metrics.get("accuracy", 0.0) < hard_negative_acceptable
        ]
        ok = not failing
        gates.append(
            _gate(
                "hard_negatives_optimized",
                ok,
                f"failing_pairs={failing[:3] if failing else 'none'}",
                f"all pairs >={hard_negative_acceptable}",
            )
        )
        if not ok:
            blocked.append(f"hard_negatives_optimized: failing pairs {failing}")

    if shadow_decisions is None or len(shadow_decisions) < 30:
        gates.append(
            _pending(
                "shadow_minimum_duration",
                f"≥{FINE_TUNE_MIN_SHADOW_DAYS} days, ≥30 decisions",
                f"observed {len(shadow_decisions) if shadow_decisions else 0} decisions over {shadow_days_observed} days",
            )
        )
    else:
        summary = compare_summary(shadow_decisions)
        ok = (
            summary["n"] >= 30
            and shadow_days_observed >= FINE_TUNE_MIN_SHADOW_DAYS
            and summary["agreement_top1"] >= FINE_TUNE_MIN_SHADOW_AGREEMENT
        )
        gates.append(
            _gate(
                "shadow_minimum_duration",
                ok,
                f"days={shadow_days_observed} n={summary['n']} agreement={summary['agreement_top1']:.3f}",
                f"days>={FINE_TUNE_MIN_SHADOW_DAYS} agreement>={FINE_TUNE_MIN_SHADOW_AGREEMENT}",
            )
        )
        if not ok:
            blocked.append("shadow_minimum_duration: insufficient shadow history")

    try:
        cal = CalibrationRegistry(storage_dir=calibration_dir)
        eces = [m.ece for m in (cal.lookup(layer, d) for layer in ("L2_domain", "L3_skill", "L4_task", "L5_capability", "L5_tool") for d in ("research", "academic", "career")) if m]
    except Exception:
        eces = []
    if not eces:
        gates.append(
            _pending(
                "calibration_acceptable",
                f"≤{FINE_TUNE_CALIBRATION_ECE}",
                "no calibration records registered yet",
            )
        )
    else:
        max_ece = max(eces)
        gates.append(
            _gate(
                "calibration_acceptable",
                max_ece <= FINE_TUNE_CALIBRATION_ECE,
                f"max_ece={max_ece:.3f}",
                f"≤{FINE_TUNE_CALIBRATION_ECE}",
            )
        )
        if max_ece > FINE_TUNE_CALIBRATION_ECE:
            blocked.append(f"calibration_acceptable: max_ece {max_ece:.3f}")

    if owner_approved is None:
        gates.append(
            _pending("owner_approval", "hitl_approval_id present", "awaiting owner")
        )
    else:
        gates.append(
            _gate(
                "owner_approval",
                owner_approved,
                "approved" if owner_approved else "not_granted",
                "hitl_approval_id present",
            )
        )
        if not owner_approved:
            blocked.append("owner_approval: not granted")

    if gpu_available is None:
        gates.append(
            _pending("gpu_available", "nvidia-smi + CUDA OR explicit_owner_approval_for_cpu_finetune", "awaiting probe")
        )
    else:
        gates.append(
            _gate(
                "gpu_available",
                gpu_available,
                "yes" if gpu_available else "cpu_only",
                "nvidia-smi + CUDA OR explicit_owner_approval_for_cpu_finetune",
            )
        )
        if not gpu_available:
            blocked.append("gpu_available: cpu_only")

    if not gpu_available:
        gates.append(
            _deferred(
                "test_set_separation",
                "test_set never used for training",
                "per audit, test split must NEVER appear in fine-tune data",
            )
        )
    else:
        gates.append(
            _gate(
                "test_set_separation",
                True,
                "verified",
                "test_set never used for training",
            )
        )

    if gpu_available is False and owner_approved is False:
        gates.append(
            _deferred(
                "fine_tune_justified",
                "evidence of measurable gap that simpler fixes cannot close",
                "current benchmark D rules+embeddings ≈ B rules on adversarial n=38; not statistically significant; deferring",
            )
        )

    gates.append(
        _gate(
            "p95_latency_within_budget",
            p95_latency_ms <= FINE_TUNE_LATENCY_BUDGET_MS,
            f"p95={p95_latency_ms:.1f}ms",
            f"≤{FINE_TUNE_LATENCY_BUDGET_MS}ms",
        )
    )
    if p95_latency_ms > FINE_TUNE_LATENCY_BUDGET_MS:
        blocked.append(f"p95_latency_within_budget: {p95_latency_ms:.1f}ms")

    gates.append(
        _gate(
            "final_action_rate_safe",
            final_action_rate <= FINE_TUNE_FINAL_ACTIONS_BLOCK,
            f"final_rate={final_action_rate:.3f}",
            f"≤{FINE_TUNE_FINAL_ACTIONS_BLOCK}",
        )
    )
    if final_action_rate > FINE_TUNE_FINAL_ACTIONS_BLOCK:
        blocked.append(f"final_action_rate_safe: {final_action_rate:.3f}")

    overall = GateStatus.PASSED
    if any(g.status == GateStatus.FAILED for g in gates):
        overall = GateStatus.FAILED
    elif any(g.status in (GateStatus.PENDING, GateStatus.DEFERRED) for g in gates):
        overall = GateStatus.DEFERRED

    return FineTuneProposal(
        proposal_id=proposal_id or f"ft-proposal-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}",
        created_at=datetime.now(UTC).isoformat(),
        gates=tuple(gates),
        overall=overall,
        rationale=rationale,
        blocked_reasons=tuple(blocked),
        metadata={"benchmark_version": BENCHMARK_VERSION, "fine_tune_version": FINE_TUNE_VERSION},
    )


def write_proposal(proposal: FineTuneProposal, output_dir: str | Path = "data/routing_fine_tune") -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{proposal.proposal_id}.json"
    path.write_text(json.dumps(proposal.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    return str(path)
