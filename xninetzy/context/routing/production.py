from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from xninetzy.context.routing.regression import (
    RegressionReport,
    RegressionStatus,
)

PROD_VERSION = "1.0.0"
ROLLOUT_PHASES: tuple[str, ...] = (
    "EXPERIMENTAL",
    "BENCHMARK",
    "SHADOW",
    "CANARY",
    "REGRESSION",
    "APPROVED",
    "PRODUCTION",
    "DEPRECATED",
)

CANARY_DEFAULT_SAMPLE_RATE = 0.10
SHADOW_MIN_DAYS = 14
CANARY_MIN_DAYS = 7
PRODUCTION_MIN_DAYS = 7


class RolloutStage(str, Enum):
    EXPERIMENTAL = "experimental"
    BENCHMARK = "benchmark"
    SHADOW = "shadow"
    CANARY = "canary"
    REGRESSION = "regression"
    APPROVED = "approved"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class RolloutState:
    stage: RolloutStage
    entered_at: str
    days_in_stage: int
    canary_sample_rate: float
    shadow_days: int
    canary_days: int
    production_days: int
    promotion_blocked: bool
    block_reasons: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": PROD_VERSION,
            "stage": self.stage.value,
            "entered_at": self.entered_at,
            "days_in_stage": self.days_in_stage,
            "canary_sample_rate": self.canary_sample_rate,
            "shadow_days": self.shadow_days,
            "canary_days": self.canary_days,
            "production_days": self.production_days,
            "promotion_blocked": self.promotion_blocked,
            "block_reasons": list(self.block_reasons),
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class RolloutPromotionRequest:
    request_id: str
    from_stage: RolloutStage
    to_stage: RolloutStage
    requested_at: str
    owner_approved: bool
    regression_report_path: str | None = None
    block_reasons: tuple[str, ...] = ()
    approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": PROD_VERSION,
            "request_id": self.request_id,
            "from_stage": self.from_stage.value,
            "to_stage": self.to_stage.value,
            "requested_at": self.requested_at,
            "owner_approved": self.owner_approved,
            "regression_report_path": self.regression_report_path,
            "block_reasons": list(self.block_reasons),
            "approved": self.approved,
        }


def evaluate_rollout_promotion(
    *,
    current_state: RolloutState,
    target_stage: RolloutStage,
    regression_report: RegressionReport,
    feature_flag_name: str = "xninetzy_routing_canary",
) -> RolloutPromotionRequest:
    block_reasons: list[str] = []
    if regression_report.overall != RegressionStatus.PASSED:
        block_reasons.append(
            f"regression gate status={regression_report.overall.value}"
        )
    if regression_report.block_reasons:
        block_reasons.extend(regression_report.block_reasons)
    if target_stage == RolloutStage.PRODUCTION and current_state.shadow_days < SHADOW_MIN_DAYS:
        block_reasons.append(
            f"shadow duration {current_state.shadow_days} < {SHADOW_MIN_DAYS} required"
        )
    if target_stage == RolloutStage.PRODUCTION and current_state.canary_days < CANARY_MIN_DAYS:
        block_reasons.append(
            f"canary duration {current_state.canary_days} < {CANARY_MIN_DAYS} required"
        )
    if target_stage == RolloutStage.PRODUCTION and current_state.production_days < PRODUCTION_MIN_DAYS:
        block_reasons.append(
            f"production duration {current_state.production_days} < {PRODUCTION_MIN_DAYS} required"
        )
    if not _stage_transition_allowed(current_state.stage, target_stage):
        block_reasons.append(
            f"illegal stage transition {current_state.stage.value} -> {target_stage.value}"
        )
    return RolloutPromotionRequest(
        request_id=f"prm-{int(time.time() * 1000)}",
        from_stage=current_state.stage,
        to_stage=target_stage,
        requested_at=datetime.now(UTC).isoformat(),
        owner_approved=not block_reasons,
        regression_report_path=None,
        block_reasons=tuple(block_reasons),
        approved=not block_reasons,
    )


def _stage_transition_allowed(from_stage: RolloutStage, to_stage: RolloutStage) -> bool:
    transitions: dict[RolloutStage, set[RolloutStage]] = {
        RolloutStage.EXPERIMENTAL: {RolloutStage.BENCHMARK, RolloutStage.DEPRECATED},
        RolloutStage.BENCHMARK: {RolloutStage.SHADOW, RolloutStage.DEPRECATED},
        RolloutStage.SHADOW: {RolloutStage.CANARY, RolloutStage.DEPRECATED},
        RolloutStage.CANARY: {RolloutStage.REGRESSION, RolloutStage.DEPRECATED},
        RolloutStage.REGRESSION: {RolloutStage.APPROVED, RolloutStage.DEPRECATED},
        RolloutStage.APPROVED: {RolloutStage.PRODUCTION, RolloutStage.DEPRECATED},
        RolloutStage.PRODUCTION: {RolloutStage.DEPRECATED},
        RolloutStage.DEPRECATED: set(),
    }
    return to_stage in transitions.get(from_stage, set())


def write_state(state: RolloutState, output_dir: str | Path = "data/routing_production") -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "state.json"
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    return str(path)


def write_promotion_request(
    req: RolloutPromotionRequest,
    output_dir: str | Path = "data/routing_production",
) -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{req.request_id}.json"
    path.write_text(json.dumps(req.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    return str(path)
