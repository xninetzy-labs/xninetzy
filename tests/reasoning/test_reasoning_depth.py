from __future__ import annotations

from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_READ_ONLY,
)
from xninetzy.context.reasoning.depth import (
    REASONING_DEPTH_COMPLEX,
    REASONING_DEPTH_HIGH_RISK,
    REASONING_DEPTH_ROUTINE,
    REASONING_DEPTH_TRIVIAL,
    ReasoningDepth,
    classify_request_depth,
    get_depth,
    is_terminal_depth,
)


def test_depth_table_covers_all_levels():
    for name in (
        REASONING_DEPTH_TRIVIAL,
        REASONING_DEPTH_ROUTINE,
        REASONING_DEPTH_COMPLEX,
        REASONING_DEPTH_HIGH_RISK,
    ):
        depth = get_depth(name)
        assert isinstance(depth, ReasoningDepth)
        assert depth.name == name
        assert depth.rank >= 0
        assert depth.min_tool_budget >= 1
        assert depth.min_evidence_budget >= 0


def test_get_depth_unknown_falls_back_to_routine():
    depth = get_depth("not-a-depth")
    assert depth.name == REASONING_DEPTH_ROUTINE


def test_classify_read_only_without_unverified_returns_trivial():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_READ_ONLY,
        trust_tier=0,
    )
    assert depth.name == REASONING_DEPTH_TRIVIAL


def test_classify_idempotent_write_returns_routine():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        trust_tier=0,
    )
    assert depth.name == REASONING_DEPTH_ROUTINE


def test_classify_unverified_third_party_returns_complex():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_READ_ONLY,
        trust_tier=2,
    )
    assert depth.name == REASONING_DEPTH_COMPLEX


def test_classify_external_returns_high_risk():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_EXTERNAL,
        trust_tier=1,
    )
    assert depth.name == REASONING_DEPTH_HIGH_RISK


def test_classify_irreversible_returns_high_risk():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        trust_tier=0,
    )
    assert depth.name == REASONING_DEPTH_HIGH_RISK


def test_classify_blocked_tier_always_high_risk():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_READ_ONLY,
        trust_tier=4,
    )
    assert depth.name == REASONING_DEPTH_HIGH_RISK


def test_classify_multi_domain_flag_promotes_to_complex():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_READ_ONLY,
        trust_tier=0,
        multi_domain=True,
    )
    assert depth.name == REASONING_DEPTH_COMPLEX


def test_classify_high_value_flag_promotes_to_high_risk():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_READ_ONLY,
        trust_tier=0,
        high_value=True,
    )
    assert depth.name == REASONING_DEPTH_HIGH_RISK


def test_hint_overrides_classification():
    depth = classify_request_depth(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        trust_tier=0,
        hint=REASONING_DEPTH_TRIVIAL,
    )
    assert depth.name == REASONING_DEPTH_TRIVIAL


def test_is_terminal_depth_trivial_and_high_risk():
    assert is_terminal_depth(REASONING_DEPTH_TRIVIAL) is True
    assert is_terminal_depth(REASONING_DEPTH_HIGH_RISK) is True
    assert is_terminal_depth(REASONING_DEPTH_ROUTINE) is False
    assert is_terminal_depth(REASONING_DEPTH_COMPLEX) is False


def test_depth_budgets_increase_with_rank():
    trivial = get_depth(REASONING_DEPTH_TRIVIAL)
    routine = get_depth(REASONING_DEPTH_ROUTINE)
    complex = get_depth(REASONING_DEPTH_COMPLEX)
    high = get_depth(REASONING_DEPTH_HIGH_RISK)
    assert trivial.min_tool_budget <= routine.min_tool_budget
    assert routine.min_tool_budget <= complex.min_tool_budget
    assert complex.min_tool_budget <= high.min_tool_budget
    assert trivial.min_evidence_budget <= high.min_evidence_budget


def test_depth_verification_required_for_routine_and_above():
    assert get_depth(REASONING_DEPTH_TRIVIAL).requires_verification is False
    assert get_depth(REASONING_DEPTH_ROUTINE).requires_verification is True
    assert get_depth(REASONING_DEPTH_COMPLEX).requires_verification is True
    assert get_depth(REASONING_DEPTH_HIGH_RISK).requires_verification is True


def test_depth_alternatives_and_counterexample_for_complex_and_above():
    trivial = get_depth(REASONING_DEPTH_TRIVIAL)
    routine = get_depth(REASONING_DEPTH_ROUTINE)
    complex = get_depth(REASONING_DEPTH_COMPLEX)
    high = get_depth(REASONING_DEPTH_HIGH_RISK)
    assert trivial.requires_alternatives is False
    assert routine.requires_alternatives is False
    assert complex.requires_alternatives is True
    assert high.requires_alternatives is True
    assert complex.requires_counterexample is True
    assert high.requires_counterexample is True


def test_depth_to_dict_round_trip():
    depth = get_depth(REASONING_DEPTH_HIGH_RISK)
    data = depth.to_dict()
    assert data["name"] == REASONING_DEPTH_HIGH_RISK
    assert data["rank"] == 3
    assert data["requires_verification"] is True
