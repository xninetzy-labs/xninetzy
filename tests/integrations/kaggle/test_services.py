from __future__ import annotations

from typing import Any

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.auth_adapter import (
    kaggle_auth_required_error,
    resolve_kaggle_auth,
)
from xninetzy.tools.ecosystem import kaggle_tools


def test_capabilities_reports_auth_state() -> None:
    snap = kaggle_services.capabilities(owner="test-owner-no-credentials", account="default")
    assert snap["provider"] == "kaggle"
    assert snap["owner"] == "test-owner-no-credentials"
    assert "auth" in snap
    assert snap["operations"] == ["search", "get", "validate", "register"]
    assert snap["output_max_bytes"] == 32_768


def test_search_returns_auth_required_when_no_creds(monkeypatch: Any) -> None:
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    snap = kaggle_services.capabilities(owner="test-owner-no-credentials", account="default")
    assert snap["env_credentials_configured"] is False
    result = kaggle_services.search(query="titanic", owner="test-owner-no-credentials", account="default")
    assert result.status == "auth_required"
    assert result.payload is None


def test_search_returns_cached_result(monkeypatch: Any) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "demo")
    monkeypatch.setenv("KAGGLE_KEY", "demo-key")
    kaggle_services.reset_cache()
    a = kaggle_services.search(query="titanic", owner="test-owner-cache", account="default")
    b = kaggle_services.search(query="titanic", owner="test-owner-cache", account="default")
    assert a.status == b.status
    assert a.payload == b.payload
    assert a.cache_hit is False
    assert b.cache_hit is True


def test_get_returns_auth_required_without_creds() -> None:
    result = kaggle_services.get(dataset_ref="user/dataset", owner="test-owner-no-credentials", account="default")
    assert result.status == "auth_required"


def test_get_returns_minimal_metadata_with_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "demo")
    monkeypatch.setenv("KAGGLE_KEY", "demo-key")
    result = kaggle_services.get(dataset_ref="user/dataset", owner="test-owner-with-env", account="default")
    assert result.status == "ok"
    assert result.payload is not None
    assert result.payload["dataset_ref"] == "user/dataset"
    assert result.payload["exists"] is False


def test_validate_is_auth_agnostic() -> None:
    result = kaggle_services.validate(dataset_ref="user/dataset", owner="test-owner-no-credentials")
    assert result.status == "ok"
    assert result.payload is not None
    assert result.payload["checks_passed"] is True


def test_register_persists_capability_pointer() -> None:
    result = kaggle_services.register(
        dataset_ref="user/dataset",
        capability="download",
        owner="test-owner-no-credentials",
    )
    assert result.status == "ok"
    assert result.payload is not None
    assert result.payload["capability"] == "download"
    assert "registered_at" in result.payload


def test_tool_kaggle_capabilities_returns_envelope() -> None:
    import json

    out = kaggle_tools.kaggle_capabilities(
        sender_id="test-owner-caps-tool",
        chat_id="test-owner-caps-tool",
    )
    if isinstance(out, str):
        parsed = json.loads(out)
    else:
        parsed = out
    assert parsed.get("ok") is True
    summary = parsed.get("summary", {})
    assert summary.get("provider") == "kaggle"


def test_tool_kaggle_auth_required_error_shape() -> None:
    err = kaggle_auth_required_error()
    assert err["error_code"] == "KAGGLE_AUTH_REQUIRED"
    assert err["retryable"] is False
    assert "auth_session_create" in " ".join(err["next_steps"])


def test_resolve_kaggle_auth_returns_safe_struct_when_missing() -> None:
    ctx = resolve_kaggle_auth(owner="test-owner-no-credentials", account="default")
    assert ctx.authenticated is False
    assert ctx.bearer_token is None
    safe = ctx.to_safe_dict()
    assert safe["authenticated"] is False
    assert safe["has_bearer"] is False
    assert "bearer_token" not in safe
