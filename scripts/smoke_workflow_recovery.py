"""Exercise persisted workflow recovery over real MCP with disposable state.

Business writes use a synthetic SQLite fixture; resume uses canonical reminder
reads and final synthesis. No owner database, vault, session or provider is used.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path


async def check(root: Path) -> dict:
    os.environ.update(
        MCP_RUNTIME_MODE="container", SQLITE_PATH=str(root / "state.sqlite3"), DATA_DIR=str(root),
        MCP_PRINCIPAL_ID="workflow-fixture-owner", MCP_DEFAULT_CHAT_ID="workflow-fixture-owner",
        XNINETZY_MCP_TRANSPORT="stdio", ACTION_POLICY_DEFAULT_MODE="auto",
        WORKFLOW_NOTIFY_ENABLED="false", LIGHTNING_ENABLED="false", AUTO_MEMORY_ENABLED="false",
        AUTO_GRAPH_ENABLED="false", AUTO_IMPROVE_ENABLED="false", NEO4J_ENABLED="false",
        NEO4J_AUTOSTART_ENABLED="false", EXTERNAL_MCP_ENABLED="false", OS_SCHEDULER_ENABLED="false",
    )
    for setting in ("OUTPUT_DIR", "BACKUP_DIR", "HEBAT_DATA_DIR", "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_PATH", "VECTOR_DATA_DIR", "GRAPH_VECTOR_DATA_DIR", "XNINETZY_SKILLS_DIR"):
        os.environ[setting] = str(root / setting.lower())
    for setting in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
        os.environ.pop(setting, None)
    from xninetzy.core.config import Settings, get_settings
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db, connect
    from xninetzy.workflow.executor import WorkflowExecutor
    from xninetzy.workflow.models import WorkflowAction, WorkflowActionResult, WorkflowActionStatus as Status, WorkflowActionType as Type, WorkflowPlan
    from xninetzy.workflow.store import WorkflowStore
    init_db()
    store = WorkflowStore()
    with connect() as conn:
        conn.execute("CREATE TABLE smoke_effects (workflow_id TEXT PRIMARY KEY)")

    def plan(identifier):
        return WorkflowPlan(id=identifier, chat_id="workflow-fixture-owner", title="Recovery fixture", original_user_message="Inspect local reminders after a fixture write", final_goal="Fixture outcome", created_at="2026-11-15T00:00:00+00:00", actions=[
            WorkflowAction(id="write", type=Type.TASK_PLANNING, title="Fixture write", goal="Fixture", critical=True),
            WorkflowAction(id="read", type=Type.REMINDER_LIST, title="Read reminders", goal="Fixture", depends_on=["write"], critical=True),
            WorkflowAction(id="final", type=Type.FINAL_SYNTHESIS, title="Review", goal="Fixture", depends_on=["read"]),
        ])

    async def write(action, state):
        with connect() as conn:
            conn.execute("INSERT INTO smoke_effects VALUES (?)", (state.plan_id,))
        state.artifacts["record"] = state.plan_id
        return WorkflowActionResult(action_id=action.id, status=Status.SUCCESS, summary="Synthetic record persisted")

    async def failed_read(action, state):
        return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Synthetic temporary read failure")

    async def uncertain_write(action, state):
        await write(action, state)
        return WorkflowActionResult(action_id=action.id, status=Status.FAILED, error="Synthetic uncertain write outcome")

    await WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: write, Type.REMINDER_LIST: failed_read}).execute(plan("recoverable-fixture"))
    await WorkflowExecutor(store=store, handlers={Type.TASK_PLANNING: uncertain_write}).execute(plan("uncertain-fixture"))
    with connect() as conn:
        before = [tuple(row) for row in conn.execute("SELECT id,result_json,finished_at FROM workflow_action_runs WHERE action_type='task_planning' ORDER BY id")]

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    parameters = StdioServerParameters(command=sys.executable, args=["-I", "-m", "xninetzy.interfaces.mcp_server"], env=dict(os.environ), cwd=str(root))
    with (root / "server.stderr").open("w") as errors:
        async with asyncio.timeout(90):
            async with stdio_client(parameters, errlog=errors) as streams:
                async with ClientSession(*streams) as session:
                    initialized = await session.initialize()
                    for key in ("resume-first", "resume-completed"):
                        result = await session.call_tool("workflow_resume", {"workflow_id": "recoverable-fixture", "idempotency_key": key})
                        assert not result.isError and "selesai" in str(result)
                    held = await session.call_tool("workflow_resume", {"workflow_id": "uncertain-fixture", "idempotency_key": "resume-uncertain"})
                    assert "workflow_uncertain_outcome_reconcile" in str(held)
    assert store.get("recoverable-fixture")["status"] == "success"
    with connect() as conn:
        after = [tuple(row) for row in conn.execute("SELECT id,result_json,finished_at FROM workflow_action_runs WHERE action_type='task_planning' ORDER BY id")]
        assert before == after
        assert conn.execute("SELECT count(*) FROM smoke_effects").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM workflow_runs").fetchone()[0] == 2
    return {"protocol": initialized.protocolVersion, "same_workflow_resume": "passed",
            "completed_replay_without_step_updates": "passed", "uncertain_mutation_held": "passed",
            "synthetic_effect_count": 2, "workflow_count": 2, "owner_data_used": False,
            "limitations": "Synthetic SQLite writes, canonical local reads/synthesis; real host UI and external effects not tested."}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="xn-workflow-smoke-") as directory:
        print(json.dumps(asyncio.run(check(Path(directory))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
