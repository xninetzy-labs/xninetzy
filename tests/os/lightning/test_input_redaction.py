from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from xninetzy.os.lightning.rl import _json, _redact


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    from xninetzy.os.lightning import rl
    from xninetzy.db import sqlite

    settings = SimpleNamespace(
        LIGHTNING_MAX_EVENT_CHARS=4000,
        APP_TIMEZONE="UTC",
        SQLITE_PATH=str(tmp_path / "lightning.sqlite3"),
    )
    monkeypatch.setattr(rl, "get_settings", lambda: settings)
    monkeypatch.setattr(sqlite, "get_settings", lambda: settings)


@pytest.mark.parametrize("key", ["api_key", "password", "access_token", "refresh_token", "Authorization", "storage_state", "session_cookie", "captcha", "client_secret"])
def test_sensitive_input_keys_are_redacted_before_serialization(key):
    payload = {"input": [{key: "synthetic-audit-sentinel"}]}

    assert "synthetic-audit-sentinel" not in _json(payload)


@pytest.mark.parametrize("text", [
    "password=synthetic-audit-sentinel",
    "access_token : synthetic-audit-sentinel",
    'secret = "synthetic audit sentinel"',
    "cookie='synthetic audit sentinel'",
])
def test_credential_assignments_in_text_are_redacted(text):
    result = _redact(text)

    assert "synthetic" not in result
    assert "[redacted]" in result


def test_known_secret_values_use_shared_sanitizer():
    secret = "sk-" + "a" * 30

    assert secret not in _json({"output": (f"failure: {secret}",)})


def test_normal_metadata_and_scalar_types_survive_redaction():
    payload = {
        "token_count": 42,
        "idempotency_key": "audit-replay-key",
        "task": "retrieve sources",
        "success": True,
        "latency_ms": 12.5,
        "optional": None,
        "nested": [{"status": "ok"}],
    }

    assert json.loads(_json(payload)) == payload


def test_recorded_action_persists_redacted_input_and_output():
    from xninetzy.db.sqlite import connect
    from xninetzy.os.lightning.rl import record_action, start_episode

    episode = start_episode(owner_scope="audit-owner", interface="test")
    action = record_action(
        episode_id=episode["episode_id"],
        owner_scope="audit-owner",
        action_type="tool",
        action_name="synthetic_tool",
        input_data={"password": "synthetic-input-sentinel", "token_count": 2},
        output_data={"detail": "secret=synthetic-output-sentinel"},
    )
    with connect() as conn:
        row = conn.execute(
            "SELECT input_json, output_json FROM agent_episode_actions WHERE action_id=?",
            (action["action_id"],),
        ).fetchone()

    assert "synthetic-input-sentinel" not in row["input_json"]
    assert "synthetic-output-sentinel" not in row["output_json"]
    assert json.loads(row["input_json"])["input"]["token_count"] == 2
