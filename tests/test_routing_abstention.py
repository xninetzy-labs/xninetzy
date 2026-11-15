from __future__ import annotations

from xninetzy.context.routing.abstention import (
    decide_abstention,
)


def test_empty_confidence_abstains() -> None:
    r = decide_abstention(confidence={})
    assert r.should_abstain
    assert "abstain_empty_confidence" in r.reason_codes


def test_high_confidence_does_not_abstain() -> None:
    r = decide_abstention(
        confidence={"a": 0.9, "b": 0.1},
        historical_abstention_rate=0.10,
    )
    assert not r.should_abstain
    assert r.selected


def test_low_confidence_abstains() -> None:
    r = decide_abstention(
        confidence={"a": 0.3, "b": 0.3},
        historical_abstention_rate=0.10,
    )
    assert r.should_abstain
    assert any("low_conf" in r for r in r.reason_codes)


def test_low_margin_abstains() -> None:
    r = decide_abstention(
        confidence={"a": 0.5, "b": 0.45},
        historical_abstention_rate=0.10,
    )
    assert r.should_abstain
    assert any("low_margin" in r for r in r.reason_codes)


def test_abstention_floor_enforced() -> None:
    r = decide_abstention(
        confidence={"a": 0.95, "b": 0.05},
        historical_abstention_rate=0.01,
        min_abstention_rate=0.05,
    )
    assert r.should_abstain
    assert "abstain_floor_below_min" in " ".join(r.reason_codes)


def test_abstention_ceiling_overrides() -> None:
    r = decide_abstention(
        confidence={"a": 0.3, "b": 0.3},
        historical_abstention_rate=0.50,
        max_abstention_rate=0.25,
    )
    assert not r.should_abstain
    assert "ceiling" in " ".join(r.reason_codes)
