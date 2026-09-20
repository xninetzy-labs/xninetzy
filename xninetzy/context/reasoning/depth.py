from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IRREVERSIBLE,
    classify_side_effect,
)
from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_THIRD_PARTY,
    TRUST_TIER_UNVERIFIED,
)


REASONING_DEPTH_TRIVIAL: str = "trivial"
REASONING_DEPTH_ROUTINE: str = "routine"
REASONING_DEPTH_COMPLEX: str = "complex"
REASONING_DEPTH_HIGH_RISK: str = "high_risk"

REASONING_DEPTH_ORDER: tuple[str, ...] = (
    REASONING_DEPTH_TRIVIAL,
    REASONING_DEPTH_ROUTINE,
    REASONING_DEPTH_COMPLEX,
    REASONING_DEPTH_HIGH_RISK,
)


@dataclass(frozen=True, slots=True)
class ReasoningDepth:
    name: str
    rank: int
    min_tool_budget: int
    min_evidence_budget: int
    requires_verification: bool
    requires_alternatives: bool
    requires_counterexample: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rank": self.rank,
            "min_tool_budget": self.min_tool_budget,
            "min_evidence_budget": self.min_evidence_budget,
            "requires_verification": self.requires_verification,
            "requires_alternatives": self.requires_alternatives,
            "requires_counterexample": self.requires_counterexample,
            "description": self.description,
        }


DEPTH_TABLE: dict[str, ReasoningDepth] = {
    REASONING_DEPTH_TRIVIAL: ReasoningDepth(
        name=REASONING_DEPTH_TRIVIAL,
        rank=0,
        min_tool_budget=1,
        min_evidence_budget=0,
        requires_verification=False,
        requires_alternatives=False,
        requires_counterexample=False,
        description="direct lookup / deterministic transform",
    ),
    REASONING_DEPTH_ROUTINE: ReasoningDepth(
        name=REASONING_DEPTH_ROUTINE,
        rank=1,
        min_tool_budget=2,
        min_evidence_budget=1,
        requires_verification=True,
        requires_alternatives=False,
        requires_counterexample=False,
        description="standard task with decompose+verify",
    ),
    REASONING_DEPTH_COMPLEX: ReasoningDepth(
        name=REASONING_DEPTH_COMPLEX,
        rank=2,
        min_tool_budget=4,
        min_evidence_budget=3,
        requires_verification=True,
        requires_alternatives=True,
        requires_counterexample=True,
        description="multi-step / cross-domain with hypotheses+alternatives",
    ),
    REASONING_DEPTH_HIGH_RISK: ReasoningDepth(
        name=REASONING_DEPTH_HIGH_RISK,
        rank=3,
        min_tool_budget=6,
        min_evidence_budget=5,
        requires_verification=True,
        requires_alternatives=True,
        requires_counterexample=True,
        description="security/financial/irreversible with full triangulation",
    ),
}


def get_depth(name: str) -> ReasoningDepth:
    if name in DEPTH_TABLE:
        return DEPTH_TABLE[name]
    return DEPTH_TABLE[REASONING_DEPTH_ROUTINE]


def classify_request_depth(
    *,
    side_effect: str | None,
    trust_tier: int | None = None,
    irreversible: bool | None = None,
    high_value: bool | None = None,
    multi_domain: bool | None = None,
    hint: str | None = None,
) -> ReasoningDepth:
    if hint is not None and hint in DEPTH_TABLE:
        return DEPTH_TABLE[hint]
    cls = classify_side_effect(side_effect)
    is_irreversible = (
        irreversible
        if irreversible is not None
        else cls.name == SIDE_EFFECT_IRREVERSIBLE
    )
    is_external = cls.name == SIDE_EFFECT_EXTERNAL
    tier = trust_tier if trust_tier is not None else TRUST_TIER_UNVERIFIED
    if tier >= TRUST_TIER_BLOCKED:
        return DEPTH_TABLE[REASONING_DEPTH_HIGH_RISK]
    if is_irreversible or is_external:
        return DEPTH_TABLE[REASONING_DEPTH_HIGH_RISK]
    if high_value:
        return DEPTH_TABLE[REASONING_DEPTH_HIGH_RISK]
    if tier >= TRUST_TIER_THIRD_PARTY or multi_domain:
        return DEPTH_TABLE[REASONING_DEPTH_COMPLEX]
    if cls.requires_idempotency_key:
        return DEPTH_TABLE[REASONING_DEPTH_ROUTINE]
    return DEPTH_TABLE[REASONING_DEPTH_TRIVIAL]


def is_terminal_depth(name: str) -> bool:
    return name in (REASONING_DEPTH_TRIVIAL, REASONING_DEPTH_HIGH_RISK)
