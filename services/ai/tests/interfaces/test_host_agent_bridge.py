from __future__ import annotations

from fastapi.testclient import TestClient

from app.xninetzy.interfaces import host_agent_bridge
from app.xninetzy.core.coding_agents import CodingAgentResult


def test_host_bridge_requires_bearer_token(monkeypatch) -> None:
    settings = host_agent_bridge.get_settings().model_copy(
        update={"CODING_AGENT_HOST_BRIDGE_TOKEN": "bridge-token"}
    )
    monkeypatch.setattr(host_agent_bridge, "get_settings", lambda: settings)

    response = TestClient(host_agent_bridge.app).get("/health")
    assert response.status_code == 200

    unauthorized = TestClient(host_agent_bridge.app).post(
        "/v1/run",
        json={
            "runtime": "opencode",
            "task": "status",
            "workspace": ".",
            "user_id": "owner",
            "chat_id": "chat",
        },
    )
    assert unauthorized.status_code == 401


def test_host_bridge_rejects_unsupported_runtime(monkeypatch) -> None:
    settings = host_agent_bridge.get_settings().model_copy(
        update={
            "CODING_AGENT_HOST_BRIDGE_TOKEN": "bridge-token",
            "CODING_AGENT_ENABLED": True,
        }
    )
    monkeypatch.setattr(host_agent_bridge, "get_settings", lambda: settings)

    response = TestClient(host_agent_bridge.app).post(
        "/v1/run",
        headers={"Authorization": "Bearer bridge-token"},
        json={
            "runtime": "internal",
            "task": "status",
            "workspace": ".",
            "user_id": "owner",
            "chat_id": "chat",
        },
    )
    assert response.status_code == 400


def test_host_bridge_accepts_catalog_runtime(monkeypatch) -> None:
    settings = host_agent_bridge.get_settings().model_copy(
        update={
            "CODING_AGENT_HOST_BRIDGE_TOKEN": "bridge-token",
            "CODING_AGENT_ENABLED": True,
        }
    )
    monkeypatch.setattr(host_agent_bridge, "get_settings", lambda: settings)
    monkeypatch.setattr(host_agent_bridge, "validate_runtime", lambda *_: object())

    async def run_local(*args, **kwargs):
        return CodingAgentResult(
            run_id="run-1",
            runtime="gemini",
            status="completed",
            output="done",
        )

    monkeypatch.setattr(host_agent_bridge, "_run_local_coding_agent", run_local)

    response = TestClient(host_agent_bridge.app).post(
        "/v1/run",
        headers={"Authorization": "Bearer bridge-token"},
        json={
            "runtime": "gemini",
            "task": "status",
            "workspace": ".",
            "user_id": "owner",
            "chat_id": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json()["runtime"] == "gemini"
