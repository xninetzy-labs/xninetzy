from __future__ import annotations

import json

import pytest

from xninetzy.tools.internal import process_engineering as pe_tools


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for var in (
        "XNINETZY_ENABLE_PM4PY",
        "XNINETZY_FLOWABLE_BASE_URL",
        "XNINETZY_ENABLE_NATIVE_MINING",
    ):
        monkeypatch.delenv(var, raising=False)


def test_process_list_providers_includes_core():
    result = pe_tools.process_list_providers.invoke({})
    ids = {p["provider_id"] for p in result}
    assert "native_xninetzy" in ids
    assert "bpmn_js" in ids
    assert "simpy" in ids


def test_process_select_provider_returns_decision():
    result = pe_tools.process_select_provider.invoke(
        {"capability": "process_modeling"}
    )
    assert result["chosen"] is not None
    assert result["chosen"]["provider_id"] == "native_xninetzy"


def test_process_select_provider_mining_disabled():
    result = pe_tools.process_select_provider.invoke(
        {"capability": "process_mining"}
    )
    assert result["chosen"] is None


def test_process_is_provider_enabled_native():
    out = pe_tools.process_is_provider_enabled.invoke(
        {"provider_id": "native_xninetzy"}
    )
    assert out is True


def test_process_capability_providers_filters_by_capability():
    result = pe_tools.process_capability_providers.invoke(
        {"capability": "process_mining"}
    )
    assert result == []


def test_process_discover_from_event_log_csv():
    csv_text = (
        "case_id,activity,timestamp\n"
        "c1,a,2026-01-01T00:00:00Z\n"
        "c1,b,2026-01-01T00:01:00Z\n"
        "c2,a,2026-01-01T00:00:00Z\n"
    )
    result = pe_tools.process_discover_from_event_log.invoke(
        {"csv_text": csv_text}
    )
    assert result["case_count"] == 2


def test_process_discover_rejects_missing_columns():
    with pytest.raises(Exception):
        pe_tools.process_discover_from_event_log.invoke(
            {"csv_text": "case_id,activity\nc1,a\n"}
        )


def test_process_simulate_runs():
    nodes = json.dumps(
        [
            {"node_id": "start", "duration_minutes": 0.0},
            {
                "node_id": "task1",
                "duration_minutes": 2.0,
                "required_resource": "agent",
            },
            {"node_id": "end", "duration_minutes": 0.0},
        ]
    )
    result = pe_tools.process_simulate.invoke(
        {
            "case_count": 3,
            "interarrival_minutes": 1.0,
            "nodes_json": nodes,
            "seed": 7,
        }
    )
    assert result["outcome"] == "ok"
    assert result["cases_completed"] == 3


def test_process_plan_execution_dry_run():
    result = pe_tools.process_plan_execution.invoke(
        {
            "deployment_key": "dep-1",
            "business_key": "case-1",
            "process_definition_key": "proc-1",
            "bpmn_xml_length": 100,
        }
    )
    assert result["dry_run"] is True


def test_process_plan_execution_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "http://flowable")
    result = pe_tools.process_plan_execution.invoke(
        {
            "deployment_key": "dep-1",
            "business_key": "case-1",
            "process_definition_key": "proc-1",
            "bpmn_xml_length": 100,
        }
    )
    assert result["dry_run"] is False
    assert result["base_url"] == "http://flowable"


def test_process_is_flowable_enabled_default_false():
    out = pe_tools.process_is_flowable_enabled.invoke({})
    assert out is False


def test_process_is_native_mining_enabled_default_false():
    out = pe_tools.process_is_native_mining_enabled.invoke({})
    assert out is False
