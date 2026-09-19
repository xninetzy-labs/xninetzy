from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_UNVERIFIED,
)
from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    SIDE_EFFECT_READ_ONLY,
    SideEffectClass,
    classify_side_effect,
)


POLICY_ALLOW: str = "allow"
POLICY_BLOCK: str = "block"
POLICY_REQUIRE_APPROVAL: str = "require_approval"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    outcome: str
    side_effect_class: SideEffectClass
    trust_tier: int
    reason: str
    details: dict[str, Any]


def _min_tier_for_side_effect(class_name: str) -> int:
    if class_name == SIDE_EFFECT_READ_ONLY:
        return TRUST_TIER_UNVERIFIED
    if class_name == SIDE_EFFECT_IDEMPOTENT_WRITE:
        return TRUST_TIER_UNVERIFIED
    if class_name in (SIDE_EFFECT_NON_IDEMPOTENT_WRITE, SIDE_EFFECT_EXTERNAL):
        return TRUST_TIER_KNOWN_EXTERNAL
    if class_name == SIDE_EFFECT_IRREVERSIBLE:
        return TRUST_TIER_KNOWN_EXTERNAL
    return TRUST_TIER_UNVERIFIED


def evaluate_policy(
    *,
    trust_tier: int,
    side_effect: str | None,
    approval_id: int | None = None,
    idempotency_key: str | None = None,
) -> PolicyDecision:
    cls = classify_side_effect(side_effect)
    if trust_tier >= TRUST_TIER_BLOCKED:
        return PolicyDecision(
            outcome=POLICY_BLOCK,
            side_effect_class=cls,
            trust_tier=trust_tier,
            reason="provider trust_tier is blocked",
            details={"approval_id": approval_id, "idempotency_key": idempotency_key},
        )
    min_tier = _min_tier_for_side_effect(cls.name)
    if trust_tier > min_tier:
        return PolicyDecision(
            outcome=POLICY_BLOCK,
            side_effect_class=cls,
            trust_tier=trust_tier,
            reason=f"trust_tier {trust_tier} exceeds policy minimum {min_tier} for side_effect={cls.name}",
            details={
                "min_required_tier": min_tier,
                "approval_id": approval_id,
                "idempotency_key": idempotency_key,
            },
        )
    if cls.requires_approval and approval_id is None:
        return PolicyDecision(
            outcome=POLICY_REQUIRE_APPROVAL,
            side_effect_class=cls,
            trust_tier=trust_tier,
            reason=f"side_effect={cls.name} requires HITL approval_id",
            details={"idempotency_key": idempotency_key},
        )
    if cls.requires_idempotency_key and not idempotency_key:
        return PolicyDecision(
            outcome=POLICY_BLOCK,
            side_effect_class=cls,
            trust_tier=trust_tier,
            reason=f"side_effect={cls.name} requires idempotency_key",
            details={"approval_id": approval_id},
        )
    return PolicyDecision(
        outcome=POLICY_ALLOW,
        side_effect_class=cls,
        trust_tier=trust_tier,
        reason="policy satisfied",
        details={"approval_id": approval_id, "idempotency_key": idempotency_key},
    )


def is_terminal_decision(outcome: str) -> bool:
    return outcome in (POLICY_ALLOW, POLICY_BLOCK)
