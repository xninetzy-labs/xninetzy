from __future__ import annotations

from types import SimpleNamespace

from app.xninetzy.interfaces import external_mcp


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
