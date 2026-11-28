from __future__ import annotations

import json
from typing import get_type_hints

import pytest
from langchain_core.tools import StructuredTool
from mcp.server.fastmcp.exceptions import ToolError

from xninetzy.interfaces.mcp_tool_adapter import langchain_tool_as_mcp_callable
from xninetzy.tools.ecosystem import kaggle_tools
from xninetzy.tools.manifest import manifest_for


@pytest.fixture
def capabilities_snapshot(monkeypatch):
    from xninetzy.core.config import get_settings

    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "approval")
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "")
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "false")
    get_settings.cache_clear()
    snapshot = {
        "provider": "kaggle",
        "auth": {"authenticated": False},
        "env_credentials_configured": False,
        "operations": ["search", "get", "validate", "register"],
    }
    monkeypatch.setattr(kaggle_tools.kaggle_services, "capabilities", lambda **kw: snapshot)
    monkeypatch.setattr(kaggle_tools.kaggle_services, "auth_status", lambda **kw: snapshot)
    yield snapshot
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["kaggle_auth_status", "kaggle_capabilities"])
async def test_status_queries_cross_mcp_boundary_under_approval_policy(name, capabilities_snapshot):
    function = getattr(kaggle_tools, name)
    tool = StructuredTool.from_function(function, name=name, description="Kaggle status query")
    result = await langchain_tool_as_mcp_callable(tool)()
    payload = json.loads(result)
    assert payload["summary"]["provider"] == "kaggle"
    assert payload["summary"]["auth"]["authenticated"] is False
    if name == "kaggle_auth_status":
        assert payload["summary"]["error"]["error_code"] == "KAGGLE_AUTH_REQUIRED"


def test_capabilities_query_requires_no_mutation_authority():
    manifest = manifest_for("kaggle_capabilities")
    assert manifest.risk.value == "read"
    assert not manifest.requires_idempotency
    assert not manifest.requires_approval


@pytest.mark.parametrize("name", kaggle_tools.__all__)
def test_kaggle_serialized_results_declare_string_contract(name):
    assert get_type_hints(getattr(kaggle_tools, name))["return"] is str


@pytest.fixture
def approval_policy(monkeypatch):
    from xninetzy.core.config import get_settings

    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "approval")
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "")
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "false")
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def _adapted(name):
    tool = StructuredTool.from_function(getattr(kaggle_tools, name), name=name, description="Kaggle tool")
    return langchain_tool_as_mcp_callable(tool)


@pytest.mark.parametrize(
    "name, risk",
    [
        ("kaggle_dataset_search", "read"),
        ("kaggle_dataset_get", "read"),
        ("kaggle_dataset_validate", "read"),
        ("kaggle_kernel_status", "read"),
        ("kaggle_kernel_output", "read"),
        ("kaggle_pipeline_status", "read"),
        ("kaggle_pipeline_plan", "draft"),
        ("kaggle_dataset_download", "write"),
        ("kaggle_dataset_register", "write"),
        ("kaggle_kernel_push", "write"),
        ("kaggle_pipeline_tick", "write"),
    ],
)
def test_kaggle_tools_carry_expected_risk_and_idempotency(name, risk):
    manifest = manifest_for(name)
    assert manifest.policy_known
    assert manifest.risk.value == risk
    assert manifest.requires_idempotency is (risk == "write")
    assert manifest.requires_approval is False


@pytest.mark.asyncio
async def test_dataset_search_is_no_longer_held_by_approval_policy(approval_policy, fake_backend):
    fake_backend.datasets["olistbr/brazilian-ecommerce"] = {"title": "Olist", "total_bytes": 1}
    result = await _adapted("kaggle_dataset_search")(query="olist")
    payload = json.loads(result)
    assert payload["summary"]["status"] == "ok"
    assert payload["summary"]["payload"]["matches"][0]["ref"] == "olistbr/brazilian-ecommerce"


@pytest.mark.asyncio
async def test_kernel_push_is_held_until_the_owner_opts_in(approval_policy, fake_backend):
    from xninetzy.core.config import get_settings

    callable_ = _adapted("kaggle_kernel_push")
    with pytest.raises(ToolError, match="POLICY_HELD"):
        await callable_(slug="held-by-policy", idempotency_key="k-1", source="print(1)\n")
    assert fake_backend.pushes == []
    approval_policy.setenv("ACTION_POLICY_OVERRIDES", "kaggle_kernel_push=auto,kaggle_pipeline_tick=auto")
    get_settings.cache_clear()
    result = await _adapted("kaggle_kernel_push")(slug="owner-enabled-job", idempotency_key="k-2", source="print(1)\n")
    assert json.loads(result)["summary"]["status"] == "submitted"
    assert len(fake_backend.pushes) == 1


@pytest.mark.asyncio
async def test_kernel_push_requires_idempotency_key_even_when_enabled(approval_policy, fake_backend):
    from xninetzy.core.config import get_settings

    approval_policy.setenv("ACTION_POLICY_OVERRIDES", "kaggle_kernel_push=auto")
    get_settings.cache_clear()
    with pytest.raises(ToolError, match="idempotency_key_required"):
        await _adapted("kaggle_kernel_push")(slug="needs-a-key", source="print(1)\n")
    assert fake_backend.pushes == []
