from __future__ import annotations

import pytest

from xninetzy.context.process_engineering.execution import (
    get_flowable_base_url,
    is_flowable_enabled,
    plan_execution,
)


def test_is_flowable_disabled_without_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("XNINETZY_FLOWABLE_BASE_URL", raising=False)
    assert is_flowable_enabled() is False


def test_is_flowable_enabled_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "http://localhost:8080")
    assert is_flowable_enabled() is True


def test_get_base_url_returns_none_when_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("XNINETZY_FLOWABLE_BASE_URL", raising=False)
    assert get_flowable_base_url() is None


def test_get_base_url_trims_whitespace(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "  http://flow  ")
    assert get_flowable_base_url() == "http://flow"


def test_plan_execution_dry_run_without_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("XNINETZY_FLOWABLE_BASE_URL", raising=False)
    plan = plan_execution(
        deployment_key="dep-1",
        bpmn_xml="<xml/>",
        business_key="case-1",
        process_definition_key="proc-1",
        variables={"k": "v"},
    )
    assert plan.dry_run is True
    assert plan.base_url == ""


def test_plan_execution_uses_env_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "http://flowable:8080")
    plan = plan_execution(
        deployment_key="dep-1",
        bpmn_xml="<xml/>",
        business_key="case-1",
        process_definition_key="proc-1",
    )
    assert plan.dry_run is False
    assert plan.base_url == "http://flowable:8080"


def test_plan_execution_carries_variables():
    plan = plan_execution(
        deployment_key="dep-1",
        bpmn_xml="<xml/>",
        business_key="case-1",
        process_definition_key="proc-1",
        variables={"k1": "v1", "k2": 2},
    )
    assert plan.instance.variables == {"k1": "v1", "k2": 2}


def test_plan_execution_tenant_id():
    plan = plan_execution(
        deployment_key="dep-1",
        bpmn_xml="<xml/>",
        business_key="case-1",
        process_definition_key="proc-1",
        tenant_id="acme",
    )
    assert plan.deployment.tenant_id == "acme"


def test_plan_execution_to_dict_structure():
    plan = plan_execution(
        deployment_key="dep-1",
        bpmn_xml="<xml/>",
        business_key="case-1",
        process_definition_key="proc-1",
    )
    data = plan.to_dict()
    for key in ("deployment", "instance", "base_url", "dry_run"):
        assert key in data
