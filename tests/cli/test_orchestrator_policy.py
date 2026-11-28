from types import SimpleNamespace

import pytest

from xninetzy.cli import orchestrator
from xninetzy.core.config import get_settings


@pytest.fixture
def policy(monkeypatch):
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "approval")
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "")
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "false")
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


async def run_tick(monkeypatch, calls):
    async def invoke(args):
        calls.append(args)
        return {"ok": True}

    monkeypatch.setattr(orchestrator, "_build_tool_map", lambda: {"kaggle_pipeline_tick": SimpleNamespace(ainvoke=invoke)})
    return await orchestrator.execute_plan({"steps": [
        {"id": "tick", "tool": "kaggle_pipeline_tick", "tier": 1, "args": {"name": "fixture"}},
    ]})


@pytest.mark.asyncio
async def test_native_cli_does_not_bypass_required_approval(policy):
    calls = []
    result = await run_tick(policy, calls)
    assert result.status == "partial"
    assert result.steps[0].status == "halted"
    assert "POLICY_HELD" in result.steps[0].error
    assert calls == []


@pytest.mark.asyncio
async def test_owner_auto_override_allows_native_tool_and_revocation_stops_it(policy):
    calls = []
    policy.setenv("ACTION_POLICY_OVERRIDES", "kaggle_pipeline_tick=auto")
    get_settings.cache_clear()
    assert (await run_tick(policy, calls)).status == "ok"
    assert len(calls) == 1
    policy.setenv("ACTION_POLICY_OVERRIDES", "")
    get_settings.cache_clear()
    assert (await run_tick(policy, calls)).steps[0].status == "halted"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_kill_switch_stops_even_owner_enabled_automation(policy):
    calls = []
    policy.setenv("ACTION_POLICY_OVERRIDES", "kaggle_pipeline_tick=auto")
    policy.setenv("ACTION_POLICY_KILL_SWITCH", "true")
    get_settings.cache_clear()
    result = await run_tick(policy, calls)
    assert result.steps[0].status == "halted"
    assert calls == []
