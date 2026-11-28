from __future__ import annotations

import json

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.auth_adapter import (
    kaggle_auth_required_error,
    resolve_kaggle_auth,
)
from xninetzy.tools.ecosystem import kaggle_tools

OWNER = "test-owner"


def seed_olist(fake) -> None:
    fake.datasets["olistbr/brazilian-ecommerce"] = {
        "title": "Olist",
        "total_bytes": 1_000,
        "last_updated": "2021-10-01",
    }
    fake.files["olistbr/brazilian-ecommerce"] = [{"name": "orders.csv", "total_bytes": 500}]


def test_capabilities_reports_auth_state_and_full_operation_list(no_credentials, kaggle_workspace) -> None:
    snap = kaggle_services.capabilities(owner="test-owner-no-credentials", account="default")
    assert snap["provider"] == "kaggle"
    assert snap["owner"] == "test-owner-no-credentials"
    assert snap["auth"]["authenticated"] is False
    assert snap["credential_source"] == "none"
    assert snap["operations"] == kaggle_services.OPERATIONS
    assert {"download", "kernel_push", "kernel_status", "kernel_output", "pipeline_tick"} <= set(snap["operations"])
    assert snap["output_max_bytes"] == 32_768


def test_cli_access_token_counts_as_authenticated_without_leaking_it(credentials) -> None:
    ctx = resolve_kaggle_auth(owner="test-owner-cli", account="default")
    assert ctx.authenticated is True
    assert ctx.source == "cli_access_token"
    safe = ctx.to_safe_dict()
    assert safe["has_bearer"] is False
    assert "not-a-real-token" not in json.dumps(safe)


def test_env_credentials_are_detected(no_credentials, monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_USERNAME", "demo")
    monkeypatch.setenv("KAGGLE_KEY", "demo-key")
    assert resolve_kaggle_auth(owner="test-owner-env").source == "env_credentials"


def test_empty_credential_file_is_not_authentication(tmp_path, monkeypatch) -> None:
    config = tmp_path / "cfg"
    config.mkdir()
    (config / "access_token").write_text("")
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(config))
    for name in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    assert resolve_kaggle_auth(owner="test-owner-empty").authenticated is False


def test_resolve_kaggle_auth_returns_safe_struct_when_missing(no_credentials) -> None:
    ctx = resolve_kaggle_auth(owner="test-owner-no-credentials", account="default")
    assert ctx.authenticated is False
    assert ctx.bearer_token is None
    safe = ctx.to_safe_dict()
    assert safe["authenticated"] is False
    assert safe["has_bearer"] is False
    assert "bearer_token" not in safe


def test_search_returns_auth_required_when_no_creds(no_credentials, kaggle_workspace) -> None:
    result = kaggle_services.search(query="titanic", owner="test-owner-no-credentials", account="default")
    assert result.status == "auth_required"
    assert result.payload is None


def test_search_returns_real_matches_and_caches(fake_backend) -> None:
    seed_olist(fake_backend)
    a = kaggle_services.search(query="olist", owner=OWNER, limit=5)
    b = kaggle_services.search(query="olist", owner=OWNER, limit=5)
    assert a.status == "ok"
    assert [m["ref"] for m in a.payload["matches"]] == ["olistbr/brazilian-ecommerce"]
    assert a.cache_hit is False
    assert b.cache_hit is True
    assert fake_backend.names().count("dataset_list") == 1


def test_search_with_no_results_is_ok_and_empty(fake_backend) -> None:
    result = kaggle_services.search(query="nothing-matches", owner=OWNER)
    assert result.status == "ok"
    assert result.payload["matches"] == []


def test_get_returns_metadata_and_files(fake_backend) -> None:
    seed_olist(fake_backend)
    result = kaggle_services.get(dataset_ref="olistbr/brazilian-ecommerce", owner=OWNER)
    assert result.status == "ok"
    assert result.payload["accessible"] is True
    assert result.payload["title"] == "Olist"
    assert result.payload["size_bytes"] == 1_000
    assert result.payload["files"] == [{"name": "orders.csv", "total_bytes": 500}]


def test_get_reports_inaccessible_instead_of_claiming_nonexistence(fake_backend) -> None:
    result = kaggle_services.get(dataset_ref="nobody/missing-data", owner=OWNER)
    assert result.status == "not_accessible"
    assert result.payload["accessible"] is False
    assert result.payload["error"]["status_code"] == 403


def test_get_rejects_malformed_reference_without_calling_kaggle(fake_backend) -> None:
    result = kaggle_services.get(dataset_ref="not a ref", owner=OWNER)
    assert result.status == "invalid_input"
    assert fake_backend.calls == []


def test_get_requires_authentication(no_credentials, kaggle_workspace) -> None:
    result = kaggle_services.get(dataset_ref="user/dataset", owner="test-owner-no-credentials", account="default")
    assert result.status == "auth_required"


def test_validate_passes_for_accessible_dataset_within_limit(fake_backend) -> None:
    seed_olist(fake_backend)
    result = kaggle_services.validate(dataset_ref="olistbr/brazilian-ecommerce", owner=OWNER)
    assert result.status == "ok"
    assert result.payload["checks_passed"] is True
    assert {c["name"] for c in result.payload["checks"]} == {"accessible", "has_files", "size_within_limit"}


def test_validate_fails_for_inaccessible_dataset(fake_backend) -> None:
    result = kaggle_services.validate(dataset_ref="nobody/missing-data", owner=OWNER)
    assert result.status == "ok"
    assert result.payload["checks_passed"] is False


def test_validate_fails_when_dataset_exceeds_max_bytes(fake_backend) -> None:
    seed_olist(fake_backend)
    result = kaggle_services.validate(dataset_ref="olistbr/brazilian-ecommerce", owner=OWNER, max_bytes=10)
    assert result.payload["checks_passed"] is False
    failed = [c["name"] for c in result.payload["checks"] if not c["passed"]]
    assert failed == ["size_within_limit"]


def test_register_persists_capability_pointer(kaggle_workspace, no_credentials) -> None:
    first = kaggle_services.register(dataset_ref="user/dataset", capability="download", owner=OWNER)
    second = kaggle_services.register(dataset_ref="user/dataset", capability="profile", owner=OWNER)
    assert first.status == "ok"
    assert first.payload["capability"] == "download"
    assert "registered_at" in first.payload
    assert second.payload["capabilities"] == ["download", "profile"]
    stored = json.loads((kaggle_workspace / "registry" / "datasets.json").read_text())
    assert sorted(stored["user/dataset"]["capabilities"]) == ["download", "profile"]


def test_register_rejects_bad_capability(kaggle_workspace, no_credentials) -> None:
    result = kaggle_services.register(dataset_ref="user/dataset", capability="Bad Name!", owner=OWNER)
    assert result.status == "invalid_input"


def test_download_writes_inside_workspace_and_reports_files(fake_backend, kaggle_workspace) -> None:
    seed_olist(fake_backend)
    result = kaggle_services.download(dataset_ref="olistbr/brazilian-ecommerce", owner=OWNER)
    assert result.status == "ok"
    target = kaggle_workspace.resolve() / "datasets" / "olistbr" / "brazilian-ecommerce"
    assert result.payload["path"] == str(target)
    assert (target / "data.csv").is_file()
    assert result.payload["file_count"] == 1


def test_download_refuses_oversized_dataset_before_transferring(fake_backend) -> None:
    seed_olist(fake_backend)
    result = kaggle_services.download(dataset_ref="olistbr/brazilian-ecommerce", owner=OWNER, max_bytes=10)
    assert result.status == "rejected"
    assert result.payload["error"]["error_code"] == "KAGGLE_DATASET_TOO_LARGE"
    assert "dataset_download" not in fake_backend.names()


def test_auth_status_verify_reports_username(fake_backend) -> None:
    snap = kaggle_services.auth_status(owner=OWNER, verify=True)
    assert snap["verified"] is True
    assert snap["username"] == "tester"


def test_capabilities_include_quota_reads_gpu_budget(fake_backend) -> None:
    fake_backend.quota_remaining = 5_000
    snap = kaggle_services.capabilities(owner=OWNER, include_quota=True)
    assert snap["quota"]["gpu"]["remaining_seconds"] == 5_000


def test_tool_kaggle_capabilities_returns_envelope(no_credentials, kaggle_workspace) -> None:
    out = kaggle_tools.kaggle_capabilities(sender_id="test-owner-caps-tool", chat_id="test-owner-caps-tool")
    parsed = json.loads(out)
    assert parsed.get("ok") is True
    assert parsed["summary"]["provider"] == "kaggle"


def test_tool_dataset_search_wraps_service_payload(fake_backend) -> None:
    seed_olist(fake_backend)
    parsed = json.loads(kaggle_tools.kaggle_dataset_search(query="olist", sender_id=OWNER))
    assert parsed["summary"]["status"] == "ok"
    assert parsed["summary"]["payload"]["matches"][0]["ref"] == "olistbr/brazilian-ecommerce"


def test_tool_reports_auth_required_error_shape(no_credentials, kaggle_workspace) -> None:
    parsed = json.loads(kaggle_tools.kaggle_dataset_search(query="x", sender_id="test-owner-none"))
    assert parsed["summary"]["status"] == "auth_required"
    assert parsed["summary"]["error"]["error_code"] == "KAGGLE_AUTH_REQUIRED"


def test_tool_kaggle_auth_required_error_shape() -> None:
    err = kaggle_auth_required_error()
    assert err["error_code"] == "KAGGLE_AUTH_REQUIRED"
    assert err["retryable"] is False
    assert "kaggle_auth_status" in err["next_steps"]
