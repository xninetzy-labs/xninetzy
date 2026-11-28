import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from xninetzy.core.config import get_settings
from xninetzy.db.migrations import run_migrations
from xninetzy.interfaces.mcp_tool_adapter import MCPPrincipal, langchain_tool_as_mcp_callable
from xninetzy.os.graph.v3 import graph_service
from xninetzy.os.lightning import rl
from xninetzy.os.memory import session_tools


@pytest.fixture
def settings_for_test(monkeypatch):
    monkeypatch.setenv("ACTION_POLICY_OVERRIDES", "memory_session_checkpoint=auto")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_shared_mcp_checkpoint_and_idempotent_replay(tmp_path, settings_for_test):
    run_migrations()
    principal = MCPPrincipal("continuity-fixture-owner", "Fixture", "tab-a")
    save = langchain_tool_as_mcp_callable(session_tools.memory_session_checkpoint, principal)
    load = langchain_tool_as_mcp_callable(
        session_tools.memory_session_resume,
        MCPPrincipal(principal.sender_id, "Fixture", "tab-b"),
    )
    denied = langchain_tool_as_mcp_callable(
        session_tools.memory_session_resume,
        MCPPrincipal("another-fixture-owner", "Fixture", "tab-b"),
    )
    workspace = str(tmp_path)
    args = dict(workspace=workspace, task="audit", expected_revision=0,
                summary="Reviewed the source", next_action="Run the unit tests",
                idempotency_key="audit-source")
    first = asyncio.run(save(**args))
    assert first == asyncio.run(save(**args))
    resumed = asyncio.run(load(workspace=workspace))
    assert resumed["checkpoint"]["revision"] == 1
    assert resumed["checkpoint"]["next_action"] == args["next_action"]
    assert asyncio.run(denied(workspace=workspace, task="audit"))["status"] == "not_found"
    assert asyncio.run(load(workspace=workspace + "/other", task="audit"))["status"] == "not_found"


def test_concurrent_tabs_cannot_overwrite_checkpoint(tmp_path):
    run_migrations()
    save = session_tools.memory_session_checkpoint.func
    read = session_tools.memory_session_resume.func
    workspace = str(tmp_path)
    args = dict(workspace=workspace, task="change", expected_revision=0,
                summary="Reviewed the source", next_action="Run the unit tests",
                sender_id="owner")
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(save, **args, idempotency_key="first-tab")
        second = pool.submit(save, **args, idempotency_key="second-tab")
        results = [first.result(), second.result()]
    assert {r["status"] for r in results} == {"saved", "revision_conflict"}
    assert read(workspace, "change", sender_id="owner")["checkpoint"]["revision"] == 1


def test_context_budget_keeps_next_action_and_isolates_tasks(tmp_path):
    run_migrations()
    workspace = str(tmp_path)
    save = session_tools.memory_session_checkpoint.func
    read = session_tools.memory_session_resume.func
    next_action = "Open the migration report"
    for task in ("alpha", "beta"):
        save(workspace, task, 0, "界" * 600, next_action, task,
             references=["α" * 120] * 5, sender_id="owner")
    assert read(workspace, sender_id="owner")["status"] == "choose_task"
    result = read(workspace, "alpha", max_context_bytes=1024, sender_id="owner")
    assert len(json.dumps(result, ensure_ascii=False).encode()) <= 1024
    assert result["checkpoint"]["next_action"] == next_action
    assert result["truncated"]


def test_graph_context_revalidates_edges_without_promoting_text_to_graph(tmp_path, monkeypatch):
    run_migrations()
    monkeypatch.setattr(graph_service, "enabled", lambda: True)
    anchor = graph_service.upsert_node(node_type="project", title="Continuity fixture")
    dependency = graph_service.upsert_node(node_type="project", title="SQLite fixture")
    edge = graph_service.upsert_edge(
        source_key=anchor.key, target_key=dependency.key, edge_type="depends_on"
    )
    workspace = str(tmp_path)
    session_tools.memory_session_checkpoint.func(
        workspace, "graph", 0, "Reviewed graph", "Verify source", "graph-1",
        graph_anchors=[{"node_type": "project", "title": "Continuity fixture"}], sender_id="owner",
    )
    resume = session_tools.memory_session_resume.func
    first = resume(workspace, "graph", sender_id="owner")
    assert first["graph"][0]["edge_key"] == edge.key
    graph_service.soft_delete_node(dependency.key)
    second = resume(workspace, "graph", sender_id="owner")
    assert second["graph_status"] == "no_active_links"
    assert second["checkpoint"]["next_action"] == "Verify source"


def test_lightning_records_metrics_without_checkpoint_text(tmp_path, monkeypatch, settings_for_test):
    run_migrations()
    monkeypatch.setenv("LIGHTNING_ENABLED", "true")
    monkeypatch.setenv("LIGHTNING_READ_SAMPLE_RATE", "1")
    get_settings.cache_clear()
    events = []
    monkeypatch.setattr(rl, "start_episode", lambda **_: {"episode_id": "fixture"})
    monkeypatch.setattr(rl, "record_action", lambda **data: events.append(data))
    monkeypatch.setattr(rl, "record_outcome", lambda **data: events.append(data))
    principal = MCPPrincipal("lightning-continuity-fixture", "Fixture", "tab")
    load = langchain_tool_as_mcp_callable(session_tools.memory_session_resume, principal)
    workspace = str(tmp_path)
    session_tools.memory_session_checkpoint.func(
        workspace, "metrics", 0, "Private fixture summary", "Verify fixture", "metrics-1",
        sender_id=principal.sender_id,
    )
    result = asyncio.run(load(workspace=workspace, task="metrics"))
    assert events[0]["input_data"] == {}
    assert events[0]["output_data"]["context_bytes"] == result["context_bytes"]
    assert events[1]["outcome_code"] == "resumed"
    assert "Private fixture summary" not in json.dumps(events)


@pytest.mark.asyncio
async def test_second_stdio_process_resumes_first_process_checkpoint(tmp_path):
    env = dict(os.environ, SQLITE_PATH=str(tmp_path / "session.sqlite3"),
               ACTION_POLICY_OVERRIDES="memory_session_checkpoint=auto")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "xninetzy.interfaces.mcp_server"],
        cwd=str(Path(__file__).resolve().parents[3]),
        env=env,
    )

    async def call(tool, arguments):
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments)
                assert not result.isError, result.content
                return result.structuredContent or json.loads(result.content[0].text)

    scope = {"workspace": str(tmp_path), "task": "stdio-handoff"}
    saved = await call("memory_session_checkpoint", {
        **scope, "expected_revision": 0, "summary": "Validated the report",
        "next_action": "Review the evidence", "idempotency_key": "stdio-handoff-1",
    })
    resumed = await call("memory_session_resume", scope)
    assert resumed["checkpoint"]["revision"] == saved["revision"] == 1
    assert resumed["checkpoint"]["next_action"] == "Review the evidence"
