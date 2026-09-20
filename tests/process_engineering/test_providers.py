from __future__ import annotations

import pytest

from xninetzy.context.process_engineering.providers import (
    CAPABILITY_EXECUTION,
    CAPABILITY_INTEROP,
    CAPABILITY_MINING,
    CAPABILITY_MODELING,
    CAPABILITY_SIMULATION,
    LICENSE_APACHE_2,
    LICENSE_BSDFREEWARE,
    LICENSE_MIT,
    PROVIDER_BIZAGI_COMPAT,
    PROVIDER_BPMN_JS,
    PROVIDER_CAMUNDA_COMPAT,
    PROVIDER_FLOWABLE,
    PROVIDER_NATIVE,
    PROVIDER_PM4PY,
    PROVIDER_SIMPY,
    ProviderProfile,
    is_provider_enabled,
    list_enabled_providers,
    list_providers_by_capability,
    select_provider,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for var in ("XNINETZY_ENABLE_PM4PY", "XNINETZY_FLOWABLE_BASE_URL"):
        monkeypatch.delenv(var, raising=False)


def test_native_provider_always_enabled():
    profile = next(p for p in list_enabled_providers() if p.provider_id == PROVIDER_NATIVE)
    assert isinstance(profile, ProviderProfile)
    assert profile.capability == CAPABILITY_MODELING
    assert profile.license == LICENSE_APACHE_2


def test_bpmn_js_enabled_by_default():
    profile = next(p for p in list_enabled_providers() if p.provider_id == PROVIDER_BPMN_JS)
    assert profile.capability == CAPABILITY_MODELING
    assert profile.license == LICENSE_MIT


def test_simpy_enabled_by_default():
    profile = next(p for p in list_enabled_providers() if p.provider_id == PROVIDER_SIMPY)
    assert profile.capability == CAPABILITY_SIMULATION


def test_pm4py_disabled_without_env():
    profile = next(p for p in PROVIDER_BY_ID_LOOKUP().values() if p.provider_id == PROVIDER_PM4PY)
    assert is_provider_enabled(profile) is False


def test_pm4py_enabled_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_ENABLE_PM4PY", "1")
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_PM4PY]
    assert is_provider_enabled(profile) is True


def test_flowable_disabled_without_env():
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_FLOWABLE]
    assert is_provider_enabled(profile) is False


def test_flowable_enabled_with_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "http://localhost:8080")
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_FLOWABLE]
    assert is_provider_enabled(profile) is True


def test_bizagi_interop_provider_metadata():
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_BIZAGI_COMPAT]
    assert profile.license == LICENSE_BSDFREEWARE
    assert profile.capability == CAPABILITY_INTEROP


def test_camunda_interop_provider_metadata():
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_CAMUNDA_COMPAT]
    assert profile.license == LICENSE_APACHE_2


def test_select_native_for_modeling_returns_native():
    decision = select_provider(CAPABILITY_MODELING)
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_NATIVE


def test_select_simulation_returns_simpy():
    decision = select_provider(CAPABILITY_SIMULATION)
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_SIMPY


def test_select_mining_without_env_returns_none():
    decision = select_provider(CAPABILITY_MINING)
    assert decision.chosen is None
    assert decision.candidates == ()


def test_select_mining_with_env_returns_pm4py(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_ENABLE_PM4PY", "true")
    decision = select_provider(CAPABILITY_MINING)
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_PM4PY
    assert decision.license_warnings


def test_select_execution_without_env_returns_none():
    decision = select_provider(CAPABILITY_EXECUTION)
    assert decision.chosen is None


def test_select_execution_with_env_returns_flowable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XNINETZY_FLOWABLE_BASE_URL", "http://flow")
    decision = select_provider(CAPABILITY_EXECUTION)
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_FLOWABLE


def test_select_with_preferred_honors_choice():
    decision = select_provider(
        CAPABILITY_MODELING,
        preferred=PROVIDER_BPMN_JS,
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_BPMN_JS


def test_select_unknown_preferred_falls_back_to_native():
    decision = select_provider(
        CAPABILITY_MODELING,
        preferred="not-a-provider",
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == PROVIDER_NATIVE


def test_list_providers_by_capability_filters_correctly():
    mining_providers = list_providers_by_capability(CAPABILITY_MINING)
    assert all(p.capability == CAPABILITY_MINING for p in mining_providers)


def test_provider_to_dict_includes_all_fields():
    profile = PROVIDER_BY_ID_LOOKUP()[PROVIDER_NATIVE]
    data = profile.to_dict()
    for key in (
        "provider_id",
        "capability",
        "transport",
        "license",
        "runtime",
        "entrypoint",
        "requires_opt_in",
        "environment_var",
        "description",
    ):
        assert key in data


def PROVIDER_BY_ID_LOOKUP():
    from xninetzy.context.process_engineering.providers import PROVIDER_TABLE
    return PROVIDER_TABLE
