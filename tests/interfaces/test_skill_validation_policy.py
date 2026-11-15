"""Writing checks are pure reads; document readiness never authorizes submission."""
from __future__ import annotations

import json

import pytest

from xninetzy.core.config import Settings, get_settings
from xninetzy.interfaces import mcp_tool_adapter as adapter
from xninetzy.tools.ecosystem import skill_routing_tools as validators
from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.tool_meta import meta_for


CASES = [
    ("skill_validate_anti_slop", {"text": "A clear draft."}),
    ("skill_validate_output", {"text": "A clear draft.", "requirements": ["draft"]}),
    ("skill_validate_submission_readiness", {"text": "A clear draft.", "requirements": ["draft"]}),
]


@pytest.fixture(autouse=True)
def isolated_policy(monkeypatch, tmp_path):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "validators.sqlite3"))
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "")
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["approval", "manual"])
@pytest.mark.parametrize("name,payload", CASES)
async def test_pure_validator_executes_without_write_approval_or_key(monkeypatch, mode, name, payload):
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", mode)
    get_settings.cache_clear()

    def forbidden_hook(*args, **kwargs):
        pytest.fail("Read-only validator initiated an automatic mutation")

    for hook in ("_auto_memory_record", "_auto_graph_record", "_auto_improve_record"):
        monkeypatch.setattr(adapter, hook, forbidden_hook)
    call = adapter.langchain_tool_as_mcp_callable(getattr(validators, name))
    result = await call(**payload)
    report = json.loads(json.loads(str(result))["summary"])
    assert isinstance(report["passed"], bool)
    manifest = manifest_for(name)
    assert manifest.risk.value == "read"
    assert not manifest.requires_approval and not manifest.requires_idempotency
    assert meta_for(name)["annotations"]["readOnlyHint"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,code", [("manual", "policy_manual"), ("approval", "approval_channel_unverified")])
@pytest.mark.parametrize("name,payload", CASES)
async def test_explicit_owner_restriction_still_holds_validator(monkeypatch, mode, code, name, payload):
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", f"{name}={mode}")
    get_settings.cache_clear()
    with pytest.raises(Exception, match=code):
        await adapter.langchain_tool_as_mcp_callable(getattr(validators, name))(**payload)


@pytest.mark.asyncio
async def test_validator_reports_problems_as_data_without_submitting_anything():
    call = adapter.langchain_tool_as_mcp_callable(validators.skill_validate_submission_readiness)
    result = await call(text="Draft.", requirements=["Missing required section"])
    report = json.loads(json.loads(str(result))["summary"])
    assert report["passed"] is False
    assert report["findings"]
