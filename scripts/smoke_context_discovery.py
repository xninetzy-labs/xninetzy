from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def decode(result):
    assert not result.isError, "Discovery returned an MCP error"
    if result.structuredContent is not None:
        content = result.structuredContent
        value = content.get("result", content)
        return [value] if isinstance(value, dict) and "name" in value else value
    blocks = [block.text for block in result.content if hasattr(block, "text")]
    values = [json.loads(block) for block in blocks]
    value = values[0] if len(values) == 1 else values
    return [value] if isinstance(value, dict) and "name" in value else value


async def check(root: Path) -> dict:
    fixture = Path(__file__).resolve().parents[1] / ".agents/skills/context-engineering"
    assert fixture.is_dir(), "Run with the repository's context-engineering fixture available"
    target = root / "skills/context-engineering"
    target.mkdir(parents=True)
    shutil.copyfile(fixture / "SKILL.md", target / "SKILL.md")
    (target / "references").mkdir()
    for reference in (fixture / "references").glob("*.md"):
        assert not reference.is_symlink(), "Fixture reference must be a regular reviewed file"
        shutil.copyfile(reference, target / "references" / reference.name)
    environment = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
    environment.update(MCP_RUNTIME_MODE="container", DATA_DIR=str(root), SQLITE_PATH=str(root / "fixture.sqlite3"),
                       XNINETZY_SKILLS_DIR=str(root / "skills"), XNINETZY_MCP_TRANSPORT="stdio",
                       MCP_PRINCIPAL_ID="discovery-fixture", MCP_DEFAULT_CHAT_ID="discovery-fixture",
                       ACTION_POLICY_DEFAULT_MODE="approval")
    for flag in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED", "LIGHTNING_ENABLED",
                 "NEO4J_ENABLED", "NEO4J_AUTOSTART_ENABLED", "EXTERNAL_MCP_ENABLED", "GRAPH_SYNC_WORKER_ENABLED"):
        environment[flag] = "false"
    bootstrap = ("from xninetzy.core.config import Settings; Settings.model_config['env_file']=None; "
                 "import runpy; runpy.run_module('xninetzy.interfaces.mcp_server',run_name='__main__')")
    parameters = StdioServerParameters(command=sys.executable, args=["-I", "-c", bootstrap], env=environment, cwd=str(root))
    with (root / "server.stderr").open("w") as errors:
        async with asyncio.timeout(60):
            async with stdio_client(parameters, errlog=errors) as streams:
                async with ClientSession(*streams) as session:
                    initialized = await session.initialize()
                    catalog = await session.list_tools()
                    schemas = {tool.name: tool.inputSchema for tool in catalog.tools}
                    assert "compact" in schemas["tool_catalog"]["properties"]
                    assert "offset" in schemas["skill_list"]["properties"]
                    assert "sender_id" not in schemas["tool_catalog"]["properties"]
                    full = decode(await session.call_tool("tool_catalog", {"risk": "read", "limit": 3}))
                    compact = decode(await session.call_tool("tool_catalog", {"risk": "read", "limit": 2, "compact": True}))
                    next_page = decode(await session.call_tool("tool_catalog", {"risk": "read", "limit": 1, "offset": 2, "compact": True}))
                    assert [row["name"] for row in compact + next_page] == [row["name"] for row in full]
                    protected = decode(await session.call_tool("tool_catalog", {"query": "hebat_remove_submission", "compact": True}))
                    assert len(protected) == 1 and protected[0]["requires_approval"] is True
                    skill = await session.call_tool("skill_list", {"query": "context-engineering", "limit": 1, "compact": True})
                    assert not skill.isError and "context-engineering" in str(skill)
                    body = await session.call_tool("skill_get", {"name": "context-engineering"})
                    reference = await session.call_tool("skill_resource_read", {"name": "context-engineering", "relative_path": "references/context-contract.md"})
                    assert not body.isError and not reference.isError
                    assert "context-contract.md" in str(body) and "Final Completion Contract" in str(reference)
                    denied = await session.call_tool("hebat_remove_submission", {"assignment_id_or_url": "synthetic-not-a-portal",
                        "confirm": True, "idempotency_key": "compact-is-not-approval"})
                    assert denied.isError and "approval_channel_unverified" in str(denied)
                    return {"protocol": initialized.protocolVersion, "tools": len(catalog.tools),
                            "compact_catalog_policy_and_pagination": "passed", "legacy_output": "passed",
                            "selected_skill_and_reference": "passed", "consequential_effect_held": True,
                            "owner_data_used": False, "host_configuration_changed": False,
                            "reviewed_skill_fixture_copied": True,
                            "limitations": "Isolated SDK client with one copied reviewed skill/reference. Does not prove wheel-bundled skill availability, native host reload, model quality or billed tokens."}


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="xn-context-wire-") as temporary:
        print(json.dumps(asyncio.run(check(Path(temporary))), indent=2))
