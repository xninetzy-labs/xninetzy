from __future__ import annotations

from xninetzy.context.routing.laya import (
    CARDI_OPTIONS,
    brier,
    ece,
    fit_platt,
    invoke_laya,
    _platt,
)


def test_platt_clips_extremes() -> None:
    assert 0.0 <= _platt(0.0, a=1.0, b=0.0) <= 1.0
    assert _platt(1.0, a=1.0, b=10.0) >= 0.999
    assert _platt(1.0, a=1.0, b=-10.0) <= 0.001


def test_ece_low_for_decent_calibration() -> None:
    probs = [0.05, 0.1, 0.3, 0.6, 0.7, 0.9, 0.95]
    labels = [0, 0, 0, 1, 1, 1, 1]
    assert ece(probs, labels) < 0.5


def test_brier_returns_zero_for_perfect_calibration() -> None:
    probs = [0.0, 1.0, 0.0, 1.0]
    labels = [0, 1, 0, 1]
    assert brier(probs, labels) == 0.0


def test_fit_platt_returns_tuple_or_none_for_bad_input() -> None:
    assert fit_platt([], []) is None
    assert fit_platt([0.1, 0.9, 0.5, 0.7, 0.2], [0, 1, 0, 1, 0]) is not None


def test_invoke_laya_abstains_on_unknown_layer() -> None:
    d = invoke_laya(layer="L99", query="x", menu=[])
    assert d.abstained
    assert "laya_invalid_layer" in d.reason_codes


def test_invoke_laya_handles_missing_provider_quietly() -> None:
    d = invoke_laya(
        layer="L2_domain",
        query="summarize",
        menu=[{"name": "research"}],
        provider_id="bogus",
        model="bogus",
        timeout_seconds=2.0,
    )
    assert d.abstained or d.metadata.get("menu_size", 0) > 0


def test_laya_cardinalities_constant() -> None:
    assert CARDI_OPTIONS[0] == 3
    assert CARDI_OPTIONS[-1] == 50
    assert len(CARDI_OPTIONS) == 10


def test_llm_chat_json_handles_invalid_response() -> None:
    class _BadClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **kw):
            raise RuntimeError("network unreachable")

    import xninetzy.context.routing.laya as m

    orig = m._llm_chat_json

    def stub(**kw):
        raise RuntimeError("no network")

    m._llm_chat_json = stub
    try:
        d = invoke_laya(layer="L2_domain", query="x", menu=[{"name": "r"}], provider_id="flaz")
        assert d.abstained
    finally:
        m._llm_chat_json = orig
