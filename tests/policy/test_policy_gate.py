from __future__ import annotations

from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_LOCAL,
    TRUST_TIER_THIRD_PARTY,
    TRUST_TIER_UNVERIFIED,
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
    POLICY_BLOCK,
    POLICY_REQUIRE_APPROVAL,
    evaluate_policy,
    is_terminal_decision,
)


def test_evaluate_policy_blocks_blocked_trust_tier():
    decision = evaluate_policy(trust_tier=TRUST_TIER_BLOCKED, side_effect=SIDE_EFFECT_READ_ONLY)
    assert decision.outcome == POLICY_BLOCK
    assert "blocked" in decision.reason


def test_evaluate_policy_allows_read_only_at_any_trust():
    for tier in (
        TRUST_TIER_LOCAL,
        TRUST_TIER_KNOWN_EXTERNAL,
        TRUST_TIER_THIRD_PARTY,
        TRUST_TIER_UNVERIFIED,
    ):
        decision = evaluate_policy(trust_tier=tier, side_effect=SIDE_EFFECT_READ_ONLY)
        assert decision.outcome == POLICY_ALLOW


def test_evaluate_policy_allows_idempotent_for_unverified():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_UNVERIFIED,
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        idempotency_key="k1",
    )
    assert decision.outcome == POLICY_ALLOW


def test_evaluate_policy_requires_idempotency_key_for_writes():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        idempotency_key=None,
    )
    assert decision.outcome == POLICY_BLOCK


def test_evaluate_policy_blocks_unverified_for_non_idempotent_write():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_UNVERIFIED,
        side_effect=SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        idempotency_key="k1",
    )
    assert decision.outcome == POLICY_BLOCK


def test_evaluate_policy_blocks_unverified_for_external_side_effect():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_UNVERIFIED,
        side_effect=SIDE_EFFECT_EXTERNAL,
        idempotency_key="k1",
    )
    assert decision.outcome == POLICY_BLOCK


def test_evaluate_policy_requires_approval_for_irreversible():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="k1",
        approval_id=None,
    )
    assert decision.outcome == POLICY_REQUIRE_APPROVAL


def test_evaluate_policy_allows_irreversible_with_approval():
    decision = evaluate_policy(
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="k1",
        approval_id=42,
    )
    assert decision.outcome == POLICY_ALLOW


def test_is_terminal_decision_classifies_outcomes():
    assert is_terminal_decision(POLICY_ALLOW) is True
    assert is_terminal_decision(POLICY_BLOCK) is True
    assert is_terminal_decision(POLICY_REQUIRE_APPROVAL) is False
