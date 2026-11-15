from __future__ import annotations

import json
import tomllib

import pytest

from scripts.connect_mcp_clients import candidate, install, plan


def test_json_update_preserves_unrelated_config_and_permissions(tmp_path):
    path = tmp_path / "settings.json"
    original = {"model": "owner-model", "mcpServers": {
        "other": {"env": {"TOKEN": "synthetic-private"}},
        "xninetzy": {"command": "old", "trust": False, "env": {"CUSTOM": "keep"}},
    }}
    path.write_text(json.dumps(original))
    result = candidate(path, "gemini", tmp_path, tmp_path / "owner.sqlite3")
    parsed = json.loads(result)
    assert parsed["model"] == original["model"]
    assert parsed["mcpServers"]["other"] == original["mcpServers"]["other"]
    entry = parsed["mcpServers"]["xninetzy"]
    assert entry["trust"] is False
    assert entry["env"]["CUSTOM"] == "keep"
    assert entry["args"] == ["-m", "xninetzy.interfaces.mcp_server"]


def test_codex_update_preserves_nested_tool_policy(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('model="owner-model"\n[mcp_servers.xninetzy]\ncommand="old"\n'
                    '[mcp_servers.xninetzy.tools.hebat_upload_submission]\napproval_policy="ask"\n'
                    '[mcp_servers.other]\ncommand="other"\n')
    parsed = tomllib.loads(candidate(path, "codex", tmp_path, tmp_path / "owner.sqlite3"))
    assert parsed["model"] == "owner-model"
    assert parsed["mcp_servers"]["other"] == {"command": "other"}
    assert parsed["mcp_servers"]["xninetzy"]["tools"]["hebat_upload_submission"] == {
        "approval_policy": "ask",
    }


@pytest.mark.parametrize("header", [
    "mcp_servers.xninetzy", '"mcp_servers"."xninetzy"', "'mcp_servers'.'xninetzy'",
])
def test_codex_plan_is_idempotent_after_rendered_install(tmp_path, header):
    path = tmp_path / "config.toml"
    path.write_text(f'model="owner-model"\n[{header}]\ncommand="old"\n'
                    '[mcp_servers.other]\ncommand="keep"\n')
    store = tmp_path / "owner.sqlite3"
    first = candidate(path, "codex", tmp_path, store)
    path.write_text(first)
    report, second = plan(path, "codex", tmp_path, store)

    assert report["changed"] is False
    assert first == second == path.read_text()
    assert tomllib.loads(second)["mcp_servers"]["other"] == {"command": "keep"}


def test_vscode_uses_servers_key(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text('{"servers": {"other": {"command": "keep"}}}')
    parsed = json.loads(candidate(path, "vscode", tmp_path, tmp_path / "owner.sqlite3"))
    assert parsed["servers"]["xninetzy"]["type"] == "stdio"
    assert "mcpServers" not in parsed


@pytest.mark.parametrize("client", ["opencode", "opencode-jsonc"])
def test_opencode_v2_migrates_only_xninetzy_into_servers(tmp_path, client):
    path = tmp_path / "config.json"
    original = {"model": "owner-model", "mcp": {
        "timeout": 12345,
        "other_legacy": {"type": "local", "command": ["keep-legacy"]},
        "xninetzy": {"type": "local", "command": ["old"], "enabled": False},
        "servers": {"other": {"type": "local", "command": ["keep-current"]}},
    }}
    path.write_text(json.dumps(original))
    text = candidate(path, client, tmp_path, tmp_path / "owner.sqlite3")
    parsed = json.loads(text)
    assert "xninetzy" not in parsed["mcp"]
    assert parsed["mcp"]["timeout"] == 12345
    assert parsed["mcp"]["other_legacy"] == original["mcp"]["other_legacy"]
    assert parsed["mcp"]["servers"]["other"] == original["mcp"]["servers"]["other"]
    entry = parsed["mcp"]["servers"]["xninetzy"]
    assert entry["disabled"] is True
    assert "enabled" not in entry
    assert entry["command"] == [str(tmp_path / ".venv/bin/python"), "-m", "xninetzy.interfaces.mcp_server"]
    assert path.read_text() == json.dumps(original)
    path.write_text(text)
    assert plan(path, client, tmp_path, tmp_path / "owner.sqlite3")[0]["changed"] is False


def test_opencode_conflicting_legacy_and_current_entries_are_rejected(tmp_path):
    path = tmp_path / "config.json"
    original = {"mcp": {"xninetzy": {"enabled": False}, "servers": {"xninetzy": {"enabled": True}}}}
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="Conflicting"):
        candidate(path, "opencode", tmp_path, tmp_path / "owner.sqlite3")
    assert json.loads(path.read_text()) == original


def test_opencode_conflicting_enable_flags_are_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"mcp":{"servers":{"xninetzy":{"enabled":false,"disabled":false}}}}')
    with pytest.raises(ValueError, match="Conflicting"):
        candidate(path, "opencode", tmp_path, tmp_path / "owner.sqlite3")


def test_read_only_plan_does_not_expose_unrelated_secrets(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"mcpServers":{"other":{"token":"private-sentinel"}}}')
    before = path.read_bytes()
    report, _ = plan(path, "claude", tmp_path, tmp_path / "owner.sqlite3")
    assert "private-sentinel" not in json.dumps(report)
    assert path.read_bytes() == before


def test_atomic_install_preserves_backup_and_detects_race(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"mcpServers":{}}')
    path.chmod(0o640)
    report, text = plan(path, "claude", tmp_path, tmp_path / "owner.sqlite3")
    backup = install(path, report["before_sha256"], text)
    assert json.loads(backup.read_text()) == {"mcpServers": {}}
    assert backup.stat().st_mode & 0o777 == 0o600
    assert path.stat().st_mode & 0o777 == 0o640
    with pytest.raises(ValueError, match="changed"):
        install(path, report["before_sha256"], text)


def test_symlink_and_invalid_json_are_rejected(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("not json")
    link = tmp_path / "link.json"
    link.symlink_to(source)
    with pytest.raises(ValueError, match="symlink"):
        candidate(link, "claude", tmp_path, tmp_path / "owner.sqlite3")
    with pytest.raises(ValueError):
        candidate(source, "claude", tmp_path, tmp_path / "owner.sqlite3")


def test_duplicate_json_keys_do_not_silently_erase_owner_settings(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"mcpServers":{}, "mcpServers":{"other":{"command":"keep"}}}')
    with pytest.raises(ValueError, match="Duplicate"):
        candidate(path, "gemini", tmp_path, tmp_path / "owner.sqlite3")


def test_disabled_local_server_remains_disabled_and_cwd_is_corrected(tmp_path):
    path = tmp_path / "config.jsonc"
    path.write_text('{"mcp":{"xninetzy":{"enabled":false,"cwd":"obsolete","timeout":90000}}}')
    entry = json.loads(candidate(path, "kilo", tmp_path, tmp_path / "owner.sqlite3"))["mcp"]["xninetzy"]
    assert entry["enabled"] is False
    assert entry["cwd"] == str(tmp_path)
    assert entry["timeout"] == 90000
    assert "environment" in entry and "env" not in entry


def test_remote_transport_is_not_silently_replaced(tmp_path):
    path = tmp_path / "config.json"
    original = '{"mcpServers":{"xninetzy":{"url":"https://example.invalid/mcp"}}}'
    path.write_text(original)
    with pytest.raises(ValueError, match="Remote"):
        candidate(path, "claude", tmp_path, tmp_path / "owner.sqlite3")
    assert path.read_text() == original
