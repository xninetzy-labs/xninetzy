"""Verify online SQLite snapshot and offline restore over real MCP, using only temporary state."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path


async def check(root: Path) -> dict:
    database, vectors, backups = root / "state.sqlite3", root / "vectors", root / "backups"
    os.environ.update(
        MCP_RUNTIME_MODE="container", SQLITE_PATH=str(database), DATA_DIR=str(root),
        MCP_PRINCIPAL_ID="backup-fixture-owner", MCP_DEFAULT_CHAT_ID="backup-fixture-owner",
        XNINETZY_MCP_TRANSPORT="stdio", ACTION_POLICY_DEFAULT_MODE="auto",
        WORKFLOW_NOTIFY_ENABLED="false", LIGHTNING_ENABLED="false", AUTO_MEMORY_ENABLED="false",
        AUTO_GRAPH_ENABLED="false", AUTO_IMPROVE_ENABLED="false", NEO4J_ENABLED="false",
        NEO4J_AUTOSTART_ENABLED="false", EXTERNAL_MCP_ENABLED="false", OS_SCHEDULER_ENABLED="false",
        VECTOR_DATA_DIR=str(vectors), BACKUP_DIR=str(backups),
    )
    for setting in ("OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR", "UNTRACKED_OUTPUT_DIR",
                    "HEBAT_DATA_DIR", "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_PATH", "GRAPH_VECTOR_DATA_DIR", "XNINETZY_SKILLS_DIR"):
        os.environ[setting] = str(root / setting.lower())
    for setting in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
        os.environ.pop(setting, None)
    from xninetzy.core.config import Settings, get_settings
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    from xninetzy.os.backup.service import create_backup, restore_backup, verify_backup
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    parameters = StdioServerParameters(command=sys.executable, args=["-I", "-m", "xninetzy.interfaces.mcp_server"], env=dict(os.environ), cwd=str(root))
    baseline = {"title": "fixture-snapshot-task", "idempotency_key": "fixture-baseline"}
    with (root / "server.stderr").open("w") as errors:
        async def session_action(stage):
            async with stdio_client(parameters, errlog=errors) as streams:
                async with ClientSession(*streams) as session:
                    initialized = await session.initialize()
                    if stage == "snapshot":
                        captured = await session.call_tool("task_capture", baseline)
                        assert not captured.isError
                        # Snapshot a live fixture server's WAL database without changing its state.
                        snapshot = await asyncio.to_thread(create_backup, database, vectors, backups)
                        return snapshot, str(captured), initialized.protocolVersion
                    if stage == "change":
                        changed = await session.call_tool("task_capture", {"title": "fixture-after-snapshot", "idempotency_key": "fixture-after"})
                        assert not changed.isError
                        tasks = str(await session.call_tool("task_list", {}))
                        assert "fixture-after-snapshot" in tasks
                        return None
                    replay = await session.call_tool("task_capture", baseline)
                    assert not replay.isError and str(replay) == first_result
                    tasks = str(await session.call_tool("task_list", {}))
                    assert tasks.count("fixture-snapshot-task") == 1
                    assert "fixture-after-snapshot" not in tasks
                    return None

        async with asyncio.timeout(120):
            snapshot, first_result, protocol = await session_action("snapshot")
            assert verify_backup(backups, snapshot["name"])["valid"]
            await session_action("change")
            # All child sessions have exited. No owner service is stopped or inspected.
            restored = restore_backup(backups, snapshot["name"], database, vectors, confirmed=True)
            assert verify_backup(backups, restored["pre_restore_backup"])["valid"]
            await session_action("verify")
    return {"protocol": protocol, "online_snapshot": "passed", "offline_restore": "passed",
            "pre_restore_snapshot": "passed", "mcp_restart_and_task_state": "passed",
            "saved_local_idempotency_replay": "passed", "owner_data_used": False,
            "limitations": "Temporary local task fixture; no external effects, owner restore, live FAISS or cross-store consistency proof."}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="xn-backup-smoke-") as directory:
        print(json.dumps(asyncio.run(check(Path(directory))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
