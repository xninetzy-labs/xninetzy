from __future__ import annotations

from fastapi.testclient import TestClient

from app.xninetzy.interfaces import host_agent_bridge


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
