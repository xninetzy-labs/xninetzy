from __future__ import annotations

import json
from typing import get_type_hints

import pytest
from langchain_core.tools import StructuredTool

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
