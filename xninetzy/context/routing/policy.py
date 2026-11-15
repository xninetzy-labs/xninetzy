from __future__ import annotations

from dataclasses import dataclass

from xninetzy.context.gateway.trust import (
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_LOCAL,
)
from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    SIDE_EFFECT_READ_ONLY,
)
from xninetzy.context.policy.gate import (
    POLICY_ALLOW,
    POLICY_REQUIRE_APPROVAL,
    PolicyDecision,
    evaluate_policy,
)
from xninetzy.tools.manifest import ToolManifest, manifest_for


_RISK_TO_SIDE_EFFECT = {
    "read": SIDE_EFFECT_READ_ONLY,
    "draft": SIDE_EFFECT_IDEMPOTENT_WRITE,
    "write": SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    "final": SIDE_EFFECT_IRREVERSIBLE,
}


@dataclass(frozen=True, slots=True)
class RoutingPolicyResult:
    tool: str
    manifest: ToolManifest
    decision: PolicyDecision
    requires_human_approval: bool
    reason_codes: tuple[str, ...] = ()


def _default_trust_tier(tool_name: str) -> int:
    if tool_name.startswith(("playwright_", "external_mcp_")):
        return TRUST_TIER_KNOWN_EXTERNAL
    return TRUST_TIER_LOCAL


def evaluate_routing_policy(
    tool_name: str,
    *,
    trust_tier: int | None = None,
    approval_id: int | None = None,
    idempotency_key: str | None = None,
) -> RoutingPolicyResult:
    manifest = manifest_for(tool_name)
    tier = trust_tier if trust_tier is not None else _default_trust_tier(tool_name)
    side_effect = _RISK_TO_SIDE_EFFECT.get(manifest.risk.value, SIDE_EFFECT_EXTERNAL)
    decision = evaluate_policy(
        trust_tier=tier,
        side_effect=side_effect,
        approval_id=approval_id,
        idempotency_key=idempotency_key,
    )
    requires_human_approval = decision.outcome == POLICY_REQUIRE_APPROVAL
    return RoutingPolicyResult(
        tool=tool_name,
        manifest=manifest,
        decision=decision,
        requires_human_approval=requires_human_approval,
        reason_codes=(
            "policy_satisfied" if decision.outcome == POLICY_ALLOW else f"policy_{decision.outcome}",
        ),
    )


def is_final_action(tool_name: str) -> bool:
    return manifest_for(tool_name).risk.value == "final"
