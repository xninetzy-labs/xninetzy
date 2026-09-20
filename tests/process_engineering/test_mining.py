from __future__ import annotations

import pytest

from xninetzy.context.process_engineering.mining import (
    discover_process,
    is_native_mining_enabled,
    parse_event_log_csv,
)


def test_parse_event_log_csv_minimal():
    csv_text = (
        "case_id,activity,timestamp,resource\n"
        "c1,a,2026-01-01T00:00:00Z,r1\n"
        "c1,b,2026-01-01T00:01:00Z,r1\n"
        "c1,c,2026-01-01T00:02:00Z,r2\n"
        "c2,a,2026-01-01T00:00:00Z,r1\n"
        "c2,c,2026-01-01T00:01:00Z,r2\n"
    )
    rows = parse_event_log_csv(csv_text)
    assert len(rows) == 5
    assert rows[0].case_id == "c1"
    assert rows[0].activity == "a"


def test_parse_event_log_csv_missing_columns():
    with pytest.raises(ValueError):
        parse_event_log_csv("case_id,activity\nc1,a\n")


def test_parse_event_log_csv_resource_optional():
    csv_text = (
        "case_id,activity,timestamp\n"
        "c1,a,2026-01-01T00:00:00Z\n"
        "c1,b,2026-01-01T00:01:00Z\n"
    )
    rows = parse_event_log_csv(csv_text)
    assert rows[0].resource is None


def test_discover_process_counts_cases_and_activities():
    csv_text = (
        "case_id,activity,timestamp\n"
        "c1,a,2026-01-01T00:00:00Z\n"
        "c1,b,2026-01-01T00:01:00Z\n"
        "c2,a,2026-01-01T00:00:00Z\n"
        "c2,b,2026-01-01T00:01:00Z\n"
    )
    rows = parse_event_log_csv(csv_text)
    report = discover_process(rows)
    assert report.case_count == 2
    assert report.activity_count == 2
    assert report.activity_frequency["a"] == 2
    assert report.activity_frequency["b"] == 2


def test_discover_process_variants():
    csv_text = (
        "case_id,activity,timestamp\n"
        "c1,a,2026-01-01T00:00:00Z\n"
        "c1,b,2026-01-01T00:01:00Z\n"
        "c1,c,2026-01-01T00:02:00Z\n"
        "c2,a,2026-01-01T00:00:00Z\n"
        "c2,c,2026-01-01T00:01:00Z\n"
        "c3,a,2026-01-01T00:00:00Z\n"
        "c3,b,2026-01-01T00:01:00Z\n"
    )
    rows = parse_event_log_csv(csv_text)
    report = discover_process(rows)
    assert report.case_count == 3
    assert len(report.variants) == 3


def test_discover_process_empty_log():
    report = discover_process(())
    assert report.case_count == 0
    assert report.activity_count == 0


def test_discover_process_notes_mention_pm4py():
    csv_text = "case_id,activity,timestamp\nc1,a,2026-01-01T00:00:00Z\n"
    rows = parse_event_log_csv(csv_text)
    report = discover_process(rows)
    assert any("PM4Py" in note for note in report.notes)


def test_is_native_mining_enabled_default_false(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("XNINETZY_ENABLE_NATIVE_MINING", raising=False)
    assert is_native_mining_enabled() is False


def test_is_native_mining_enabled_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_ENABLE_NATIVE_MINING", "1")
    assert is_native_mining_enabled() is True
