"""Exercise an existing image over MCP STDIO using disposable state only.

No owner .env, database, vault, network or production container is mounted.
Creates one named test container, restarts it, verifies persistence, and removes
only that container. Build the image separately before invoking this script.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f"Docker command {args[0]} failed: {result.stderr[:600]}")
    return result.stdout.strip()


async def session_check(name: str, log: Path, *, write: bool, validators_only: bool = False) -> dict:
    with log.open("w") as errors:
        parameters = StdioServerParameters(command="docker", args=["start", "-a", "-i", name])
        async with asyncio.timeout(90):
            async with stdio_client(parameters, errlog=errors) as streams:
                async with ClientSession(*streams) as session:
                    initialized = await session.initialize()
                    listed = await session.list_tools()
                    assert "task_capture" in {tool.name for tool in listed.tools}
                    catalog = {tool.name: tool for tool in listed.tools}
                    validated = []
                    for validator in ("skill_validate_anti_slop", "skill_validate_output", "skill_validate_submission_readiness"):
                        assert catalog[validator].annotations.readOnlyHint is True
                        assert "idempotency_key" not in catalog[validator].inputSchema["properties"]
                        payload = {"text": "A seamlessly integrated draft."}
                        if validator == "skill_validate_submission_readiness":
                            payload["requirements"] = ["Missing required section"]
                        checked = await session.call_tool(validator, payload)
                        assert not checked.isError, f"{validator} was policy-held"
                        envelope = json.loads("\n".join(getattr(block, "text", "") for block in checked.content))
                        report = json.loads(envelope["summary"])
                        assert report["passed"] is False, f"{validator} discarded the expected finding"
                        validated.append(validator)
                    if validators_only:
                        held = await session.call_tool("hebat_remove_submission", {
                            "assignment_id_or_url": "synthetic-no-network-target", "confirm": True,
                            "idempotency_key": "validator-not-an-approval",
                        })
                        assert held.isError and "approval_channel_unverified" in str(held)
                        return {"tools": len(listed.tools), "protocol": initialized.protocolVersion,
                                "validators": validated, "without_approval_or_key": "passed",
                                "validation_findings_preserved": True, "consequential_action_held": True}
                    assert catalog["datetime_now"].annotations.readOnlyHint is True
                    assert "sender_id" not in catalog["task_capture"].inputSchema["properties"]
                    assert "idempotency_key" in catalog["task_capture"].inputSchema["properties"]
                    now = await session.call_tool("datetime_now", {})
                    assert not now.isError and "ISO:" in str(now)
                    held = await session.call_tool("hebat_remove_submission", {
                        "assignment_id_or_url": "synthetic-no-network-target", "confirm": True,
                        "idempotency_key": "forged-approval-fixture",
                    })
                    assert held.isError and "approval_channel_unverified" in str(held)
                    no_key = await session.call_tool("task_capture", {"title": "must-not-persist"})
                    assert no_key.isError and "idempotency_key_required" in str(no_key)
                    result = await session.call_tool("task_capture", {
                        "title": "synthetic-container-restart-check",
                        "idempotency_key": "container-restart-fixture",
                    })
                    assert not result.isError and "Task dicatat" in str(result)
                    changed = await session.call_tool("task_capture", {
                        "title": "must-not-persist", "idempotency_key": "container-restart-fixture",
                    })
                    assert changed.isError and "idempotency_payload_mismatch" in str(changed)
                    tasks = await session.call_tool("task_list", {})
                    assert not tasks.isError and "synthetic-container-restart-check" in str(tasks)
                    task_text = "\n".join(getattr(block, "text", "") for block in tasks.content)
                    assert task_text.count("synthetic-container-restart-check") == 1
                    assert "must-not-persist" not in task_text
                    return {"tools": len(listed.tools), "protocol": initialized.protocolVersion,
                            "safe_read": "passed", "write" if write else "restart_persistence": "passed",
                            "unverified_confirmation_denied": True, "write_without_key_denied": True,
                            "modified_payload_denied": True, "schema_policy_metadata": "passed",
                            "idempotent_replay_after_restart": "not_applicable" if write else "passed"}


async def smoke(image: str, *, validators_only: bool = False) -> dict:
    if os.getuid() == 0:
        raise ValueError("Run this smoke as a non-root owner so the fixture uses an unprivileged UID")
    name = "xninetzy-smoke-" + uuid.uuid4().hex[:12]
    created = False
    with tempfile.TemporaryDirectory(prefix="xn-docker-smoke-") as temporary:
        root = Path(temporary)
        state = root / "data"
        state.mkdir()
        try:
            docker("create", "--name", name, "--interactive", "--network", "none", "--read-only",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                   "--tmpfs", "/tmp:mode=1777", "--user", f"{os.getuid()}:{os.getgid()}",
                   "--mount", f"type=bind,source={state},target=/app/data",
                   "--env", "AUTO_MEMORY_ENABLED=false", "--env", "AUTO_GRAPH_ENABLED=false",
                   "--env", "AUTO_IMPROVE_ENABLED=false", "--env", "LIGHTNING_ENABLED=false",
                   "--env", f"ACTION_POLICY_DEFAULT_MODE={'approval' if validators_only else 'auto'}",
                   "--env", "NEO4J_ENABLED=false", "--env", "NEO4J_AUTOSTART_ENABLED=false", image)
            created = True
            first = await session_check(name, root / "first.stderr", write=True, validators_only=validators_only)
            docker("stop", "--time", "3", name)
            second = await session_check(name, root / "restart.stderr", write=False, validators_only=validators_only)
            return {"image": image, "first_start": first, "restart": second,
                    "owner_data_mounted": False, "network": "none", "read_only_root": True,
                    "default_policy": "approval" if validators_only else "auto",
                    "limitations": "Synthetic local operations only; no live provider/graph or durable external workflow recovery."}
        finally:
            if created:
                docker("rm", "--force", name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--validators-only", action="store_true", help="Use the default approval policy; validate text without mutations")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke(args.image, validators_only=args.validators_only)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
