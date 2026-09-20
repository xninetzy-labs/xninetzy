from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from xninetzy.interfaces import external_mcp


def test_external_mcp_registry_add_list_remove(tmp_path, monkeypatch):
    monkeypatch.setattr(external_mcp, "_owner_allowed", lambda *_: True)
    monkeypatch.setattr(
        external_mcp,
        "get_settings",
        lambda: SimpleNamespace(
            EXTERNAL_MCP_REGISTRY_PATH=str(tmp_path / "external-mcp.json"),
            EXTERNAL_MCP_ENABLED=False,
            EXTERNAL_MCP_ALLOW_CALLS=False,
            EXTERNAL_MCP_TIMEOUT_SECONDS=1,
        ),
    )

    created = external_mcp.external_mcp_add.invoke(
        {
            "name": "demo-mcp",
            "command": "node",
            "args_json": "[\"server.js\"]",
            "env_vars_json": "[\"DEMO_API_KEY\"]",
        }
    )
    listed = external_mcp.external_mcp_list.invoke({})
    removed = external_mcp.external_mcp_remove.invoke({"name": "demo-mcp"})

    assert created["success"] is True
    assert listed["servers"][0]["name"] == "demo-mcp"
    assert listed["servers"][0]["env_vars"] == ["DEMO_API_KEY"]
    assert removed == {"success": True, "removed": "demo-mcp"}


def test_external_mcp_rejects_shell_command(tmp_path, monkeypatch):
    monkeypatch.setattr(external_mcp, "_owner_allowed", lambda *_: True)
    monkeypatch.setattr(
        external_mcp,
        "get_settings",
        lambda: SimpleNamespace(EXTERNAL_MCP_REGISTRY_PATH=str(tmp_path / "registry.json")),
    )

    result = external_mcp.external_mcp_add.invoke(
        {
            "name": "unsafe-mcp",
            "command": "node server.js",
            "args_json": "[]",
            "env_vars_json": "[]",
        }
    )

    assert result["success"] is False


def _seed_registry(path, last_reviewed_at=None):
    entry = {
        "name": "alpha",
        "command": "node",
        "args": ["alpha.js"],
        "enabled": True,
        "risk_level": "low",
        "allowed_tools": ["echo"],
    }
    if last_reviewed_at is not None:
        entry["last_reviewed_at"] = last_reviewed_at
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"servers": [entry]}), encoding="utf-8")


def test_external_mcp_call_refuses_unreviewed_server(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    _seed_registry(registry, last_reviewed_at=None)
    monkeypatch.setattr(external_mcp, "_owner_allowed", lambda *_: True)
    monkeypatch.setattr(
        external_mcp,
        "get_settings",
        lambda: SimpleNamespace(
            EXTERNAL_MCP_REGISTRY_PATH=str(registry),
            EXTERNAL_MCP_ENABLED=True,
            EXTERNAL_MCP_ALLOW_CALLS=True,
            EXTERNAL_MCP_TRUST_MAX_AGE_DAYS=30,
            XNINETZY_MCP_CALL_TIMEOUT_SECONDS=1,
        ),
    )
    import asyncio

    result = asyncio.run(
        external_mcp.external_mcp_call.ainvoke(
            {"name": "alpha", "tool_name": "echo", "arguments_json": "{}"}
        )
    )
    assert result["success"] is False
    assert "belum pernah divalidasi" in result["message"]


def test_external_mcp_call_refuses_stale_review(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    stale = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    _seed_registry(registry, last_reviewed_at=stale)
    monkeypatch.setattr(external_mcp, "_owner_allowed", lambda *_: True)
    monkeypatch.setattr(
        external_mcp,
        "get_settings",
        lambda: SimpleNamespace(
            EXTERNAL_MCP_REGISTRY_PATH=str(registry),
            EXTERNAL_MCP_ENABLED=True,
            EXTERNAL_MCP_ALLOW_CALLS=True,
            EXTERNAL_MCP_TRUST_MAX_AGE_DAYS=30,
            XNINETZY_MCP_CALL_TIMEOUT_SECONDS=1,
        ),
    )
    import asyncio

    result = asyncio.run(
        external_mcp.external_mcp_call.ainvoke(
            {"name": "alpha", "tool_name": "echo", "arguments_json": "{}"}
        )
    )
    assert result["success"] is False
    assert "kadaluarsa" in result["message"]


def test_external_mcp_call_passes_with_fresh_review(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    fresh = datetime.now(timezone.utc).isoformat()
    _seed_registry(registry, last_reviewed_at=fresh)
    monkeypatch.setattr(external_mcp, "_owner_allowed", lambda *_: True)
    monkeypatch.setattr(
        external_mcp,
        "get_settings",
        lambda: SimpleNamespace(
            EXTERNAL_MCP_REGISTRY_PATH=str(registry),
            EXTERNAL_MCP_ENABLED=True,
            EXTERNAL_MCP_ALLOW_CALLS=True,
            EXTERNAL_MCP_TRUST_MAX_AGE_DAYS=30,
            XNINETZY_MCP_CALL_TIMEOUT_SECONDS=1,
        ),
    )

    class _FakeSession:
        async def call_tool(self, name, args):
            return SimpleNamespace(content=[SimpleNamespace(text="ok")], isError=False)

    async def _fake_with_session(server, fn):
        return await fn(_FakeSession())

    monkeypatch.setattr(external_mcp, "_with_session", _fake_with_session)
    import asyncio

    result = asyncio.run(
        external_mcp.external_mcp_call.ainvoke(
            {"name": "alpha", "tool_name": "echo", "arguments_json": "{}"}
        )
    )
    assert result["success"] is True
