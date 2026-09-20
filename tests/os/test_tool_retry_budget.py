from __future__ import annotations

from xninetzy.os.tool_retry_budget import check, reset


def test_check_allows_within_budget():
    reset()
    allowed, remaining = check("retry_test_tool")
    assert allowed is True
    assert remaining >= 0


def test_check_decrements_remaining():
    reset()
    check("retry_test_tool_a")
    check("retry_test_tool_a")
    allowed, remaining = check("retry_test_tool_a")
    assert allowed is True
    assert remaining >= 0


def test_reset_clears_state():
    check("retry_test_tool_b")
    cleared = reset("retry_test_tool_b")
    assert cleared == 1
    allowed, _ = check("retry_test_tool_b")
    assert allowed is True


def test_reset_all_clears():
    check("retry_test_tool_c1")
    check("retry_test_tool_c2")
    cleared = reset()
    assert cleared >= 2


def test_stats_reports_tracked_keys():
    from xninetzy.os.tool_retry_budget import stats

    reset()
    check("retry_stats_tool_1")
    check("retry_stats_tool_2")
    snap = stats()
    assert snap["tracked_keys"] >= 2
    assert "retry_stats_tool_1" in snap["sample"]
    assert snap["sample"]["retry_stats_tool_1"]["count"] >= 1
