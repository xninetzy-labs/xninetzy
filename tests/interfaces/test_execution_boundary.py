from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from langchain_core.tools import StructuredTool

from xninetzy.interfaces import mcp_tool_adapter as adapter


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    from xninetzy.core.config import Settings, get_settings

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("MCP_RUNTIME_MODE", "container")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "gateway.sqlite3"))
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "auto")
    for flag in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED", "LIGHTNING_ENABLED"):
        monkeypatch.setenv(flag, "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["hebat_upload_submission", "hebat_remove_submission", "qa_fill_kuesioner", "external_mcp_call", "graph_v3_rebuild", "unknown_submit"])
async def test_unverified_approval_never_reaches_effect(name):
    effects = []

    def effect(approval_id: int = 0, confirm: bool = False, side_effect: str = "read_only") -> str:
        effects.append(True)
        return "effect"

    tool = StructuredTool.from_function(effect, name=name, description="synthetic effect")
    with pytest.raises(Exception, match="approval_channel_unverified|unknown_tool_policy"):
        await adapter.langchain_tool_as_mcp_callable(tool)(approval_id=987654, confirm=True, side_effect="read_only")
    assert effects == []


@pytest.mark.asyncio
async def test_kill_switch_precedes_handler(monkeypatch):
    effects = []

    def effect() -> str:
        effects.append(True)
        return "ok"

    from xninetzy.core.config import get_settings
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "true")
    get_settings.cache_clear()
    tool = StructuredTool.from_function(effect, name="datetime_now", description="synthetic")
    with pytest.raises(Exception, match="policy_kill_switch"):
        await adapter.langchain_tool_as_mcp_callable(tool)()
    assert effects == []


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,code", [("approval", "approval_channel_unverified"), ("manual", "policy_manual")])
async def test_global_owner_restrictions_cannot_be_bypassed_by_local_write(monkeypatch, mode, code):
    from xninetzy.core.config import get_settings
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", mode)
    get_settings.cache_clear()
    effects = []

    def effect() -> str:
        effects.append(True)
        return "ok"

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(
        effect, name="task_capture", description="synthetic"))
    with pytest.raises(Exception, match=code):
        await call(idempotency_key="owner-policy")
    assert effects == []


@pytest.mark.asyncio
async def test_handler_error_does_not_expose_private_exception():
    def effect() -> str:
        raise RuntimeError("password=synthetic-private-sentinel")

    tool = StructuredTool.from_function(effect, name="datetime_now", description="synthetic")
    with pytest.raises(Exception) as captured:
        await adapter.langchain_tool_as_mcp_callable(tool)()
    assert "synthetic-private-sentinel" not in str(captured.value)


@pytest.mark.parametrize("hook", ["memory", "graph", "improve"])
def test_auto_hook_error_trace_does_not_persist_private_exception(monkeypatch, hook):
    from xninetzy.core.config import get_settings
    from xninetzy.observability import trace
    for flag in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED"):
        monkeypatch.setenv(flag, "true")
    monkeypatch.setenv("AUTO_MEMORY_SAMPLE_RATE", "1")
    monkeypatch.setenv("AUTO_MEMORY_MIN_CONTENT_CHARS", "0")
    get_settings.cache_clear()
    events = []
    monkeypatch.setattr(trace, "emit", lambda *args, **kwargs: events.append(kwargs))

    def broken(*args, **kwargs):
        raise RuntimeError("password=private-hook-sentinel")

    if hook == "memory":
        from xninetzy.os.memory import memory_store
        monkeypatch.setattr(memory_store, "add_memory", broken)
        adapter._auto_memory_record("task_capture", {}, "result", "owner")
    elif hook == "graph":
        from xninetzy.os.graph import graph_store
        monkeypatch.setattr(graph_store, "search_nodes", broken)
        adapter._auto_graph_record("task_capture", {}, "result", "write", "owner")
    else:
        from xninetzy.tools.ecosystem import improvement_tools
        monkeypatch.setattr(improvement_tools, "improvement_detect", broken)
        adapter._auto_improve_record("task_capture", {}, RuntimeError("synthetic"), "owner")
    assert events
    assert "private-hook-sentinel" not in str(events)


@pytest.mark.asyncio
async def test_timeout_boundary(monkeypatch):
    async def slow() -> str:
        await asyncio.sleep(0.15)
        return "late"

    tool = StructuredTool.from_function(coroutine=slow, name="datetime_now", description="synthetic")
    from xninetzy.core.config import get_settings
    current = get_settings().model_dump()
    current["XNINETZY_TOOL_TIMEOUT_SECONDS"] = 0.01
    monkeypatch.setattr(adapter, "get_settings", lambda: SimpleNamespace(**current))
    with pytest.raises(Exception, match="tool_timeout"):
        await adapter.langchain_tool_as_mcp_callable(tool)()


@pytest.mark.asyncio
async def test_idempotency_payload_mismatch_and_replay():
    effects = []

    def effect(title: str, idempotency_key: str = "") -> str:
        effects.append(title)
        return title

    tool = StructuredTool.from_function(effect, name="task_capture", description="synthetic")
    call = adapter.langchain_tool_as_mcp_callable(tool)
    assert await call(title="one", idempotency_key="same") == "one"
    assert await call(title="one", idempotency_key="same") == "one"
    with pytest.raises(Exception, match="idempotency_payload_mismatch"):
        await call(title="two", idempotency_key="same")
    assert effects == ["one"]


@pytest.mark.asyncio
async def test_local_mutation_needs_key_before_effect():
    effects = []

    def effect(title: str) -> str:
        effects.append(title)
        return title

    tool = StructuredTool.from_function(effect, name="task_capture", description="synthetic")
    with pytest.raises(Exception, match="idempotency_key_required"):
        await adapter.langchain_tool_as_mcp_callable(tool)(title="one")
    assert effects == []


@pytest.mark.asyncio
@pytest.mark.parametrize("name,expected", [("datetime_now", 0), ("task_capture", 3)])
async def test_canonical_auto_hooks_do_not_mutate_reads_or_replayed_writes(monkeypatch, name, expected):
    hooks = []
    for hook in ("_auto_memory_record", "_auto_graph_record", "_auto_improve_record"):
        monkeypatch.setattr(adapter, hook, lambda *args, **kwargs: hooks.append(True))

    def effect() -> str:
        return "synthetic result"

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(
        effect, name=name, description="synthetic"))
    kwargs = {"idempotency_key": "hooks-replay"} if name == "task_capture" else {}
    assert await call(**kwargs) == "synthetic result"
    assert await call(**kwargs) == "synthetic result"
    assert len(hooks) == expected


@pytest.mark.asyncio
async def test_pending_concurrent_call_cannot_execute_twice():
    started, finish = asyncio.Event(), asyncio.Event()
    effects = []

    async def effect(title: str, idempotency_key: str = "") -> str:
        effects.append(title)
        started.set()
        await finish.wait()
        return title

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(coroutine=effect, name="task_capture", description="synthetic"))
    first = asyncio.create_task(call(title="one", idempotency_key="concurrent"))
    try:
        await asyncio.wait_for(started.wait(), 3)
        with pytest.raises(Exception, match="idempotency_pending"):
            await call(title="one", idempotency_key="concurrent")
    finally:
        finish.set()
        await first
    assert effects == ["one"]


@pytest.mark.asyncio
async def test_uncertain_handler_failure_is_not_retried():
    effects = []

    def effect(title: str, idempotency_key: str = "") -> str:
        effects.append(title)
        raise RuntimeError("synthetic delivery error")

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(effect, name="task_capture", description="synthetic"))
    with pytest.raises(Exception, match="tool_execution_failed"):
        await call(title="one", idempotency_key="uncertain")
    with pytest.raises(Exception, match="idempotency_pending"):
        await call(title="one", idempotency_key="uncertain")
    assert effects == ["one"]


@pytest.mark.asyncio
async def test_same_owner_cross_client_replay_and_other_owner_isolation():
    effects = []

    def effect(title: str, sender_id: str = "", idempotency_key: str = "") -> str:
        effects.append(sender_id)
        return title

    tool = StructuredTool.from_function(effect, name="task_capture", description="synthetic")
    for owner, chat in (("owner-a", "client-1"), ("owner-a", "client-2"), ("owner-b", "client-3")):
        call = adapter.langchain_tool_as_mcp_callable(tool, adapter.MCPPrincipal(owner, "Fixture", chat))
        assert await call(title="one", sender_id="spoof", idempotency_key="shared") == "one"
    assert effects == ["owner-a", "owner-b"]


@pytest.mark.asyncio
async def test_owner_scope_body_is_not_authority():
    captured = []

    def effect(owner: str = "system") -> str:
        captured.append(owner)
        return "ok"

    tool = StructuredTool.from_function(effect, name="memory_list", description="synthetic")
    call = adapter.langchain_tool_as_mcp_callable(tool)
    assert "owner" not in call.__signature__.parameters
    await call(owner="another-owner")
    assert captured == ["system"]


@pytest.mark.asyncio
async def test_optional_telemetry_failure_does_not_fail_completed_call(monkeypatch):
    from xninetzy.os.lightning import rl
    from xninetzy.core.config import get_settings

    monkeypatch.setenv("LIGHTNING_ENABLED", "true")
    monkeypatch.setenv("LIGHTNING_READ_SAMPLE_RATE", "1")
    get_settings.cache_clear()

    def broken(**_):
        raise RuntimeError("password=synthetic-telemetry-sentinel")

    monkeypatch.setattr(rl, "start_episode", broken)
    tool = StructuredTool.from_function(lambda: "ok", name="datetime_now", description="synthetic")
    assert await adapter.langchain_tool_as_mcp_callable(tool)() == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize("structured", [True, False])
async def test_credentials_redacted_from_structured_and_json_text_results(structured):
    import json

    def read() -> dict | str:
        value = {"safe": "retained", "nested": {"password": "arbitrary-private-sentinel"}}
        return value if structured else json.dumps(value)

    tool = StructuredTool.from_function(read, name="datetime_now", description="synthetic")
    result = await adapter.langchain_tool_as_mcp_callable(tool)()
    assert "arbitrary-private-sentinel" not in str(result)
    assert "retained" in str(result)


@pytest.mark.asyncio
async def test_invalid_mutation_output_remains_quarantined():
    effects = []

    def effect() -> int:
        effects.append(True)
        return "invalid declared integer"

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(
        effect, name="task_capture", description="synthetic"))
    with pytest.raises(Exception, match="tool_output_validation_failed"):
        await call(idempotency_key="invalid-output")
    with pytest.raises(Exception, match="idempotency_pending"):
        await call(idempotency_key="invalid-output")
    assert effects == [True]


@pytest.mark.asyncio
async def test_input_and_output_are_bounded_before_side_effect():
    effects = []

    def effect(value: str) -> str:
        effects.append(True)
        return value

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(effect, name="calculate", description="synthetic"))
    with pytest.raises(Exception, match="tool_input_limit_exceeded"):
        await call(value="x" * 70000)
    assert effects == []
    assert "output_limit_exceeded" in await call(value="x" * 40000)


@pytest.mark.asyncio
async def test_all_canonical_consequential_operations_fail_closed_and_are_audited():
    from xninetzy.tools.manifest import policy_catalog
    from xninetzy.context.policy.audit import list_audit_entries
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    effects = []

    def effect(approval_id: int = 0) -> str:
        effects.append(True)
        return "forbidden"

    final_names = {name for name, risk in policy_catalog().items() if risk == "final"}
    assert len(final_names) >= 23
    for name in final_names:
        call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(effect, name=name, description="synthetic"))
        for identifier in (0, 123, -1):
            with pytest.raises(Exception, match="approval_channel_unverified"):
                await call(approval_id=identifier)
    assert effects == []
    rows = list_audit_entries(limit=200)
    assert {row.capability for row in rows} == final_names
    assert all(row.outcome == "blocked" and row.error == "approval_channel_unverified" for row in rows)


@pytest.mark.asyncio
async def test_timed_out_worker_keeps_concurrency_slot(monkeypatch):
    from xninetzy.core.config import get_settings

    current = get_settings().model_dump()
    current.update(AI_CPU_THREADS=1, XNINETZY_TOOL_TIMEOUT_SECONDS=0.03)
    monkeypatch.setattr(adapter, "get_settings", lambda: SimpleNamespace(**current))
    started, finish = asyncio.Event(), asyncio.Event()
    calls = []

    async def slow() -> str:
        calls.append(True)
        started.set()
        await finish.wait()
        return "ok"

    call = adapter.langchain_tool_as_mcp_callable(StructuredTool.from_function(coroutine=slow, name="datetime_now", description="synthetic"))
    first = asyncio.create_task(call())
    try:
        await asyncio.wait_for(started.wait(), 2)
        with pytest.raises(Exception, match="tool_timeout"):
            await first
        with pytest.raises(Exception, match="tool_timeout"):
            await call()
        assert len(calls) == 1
    finally:
        finish.set()
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_explicit_owner_override_is_not_weakened(monkeypatch):
    from xninetzy.core.config import get_settings

    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "datetime_now=manual")
    get_settings.cache_clear()
    tool = StructuredTool.from_function(lambda: "effect", name="datetime_now", description="synthetic")
    with pytest.raises(Exception, match="policy_manual"):
        await adapter.langchain_tool_as_mcp_callable(tool)()
