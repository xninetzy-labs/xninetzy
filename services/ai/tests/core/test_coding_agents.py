from __future__ import annotations

from pathlib import Path

import pytest

from app.xninetzy.core.coding_agents import (
    build_command,
    resolve_workspace,
    runtime_catalog,
    subprocess_environment,
)
from app.xninetzy.core.config import Settings


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        CODING_AGENT_ENABLED=True,
        CODING_AGENT_ALLOWED="internal,codex,claude-code,opencode",
        CODING_AGENT_ALLOWED_ROOT=str(tmp_path),
        CODING_AGENT_WORKSPACE="repo",
        CODEX_BIN="codex-test",
        CLAUDE_CODE_BIN="claude-test",
        OPENCODE_BIN="opencode-test",
    )


def test_workspace_is_confined_to_allowed_root(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    settings = _settings(tmp_path)

    assert resolve_workspace(settings=settings) == repo.resolve()
    with pytest.raises(ValueError, match="harus berada"):
        resolve_workspace("../outside", settings)


def test_codex_command_uses_workspace_write_sandbox(monkeypatch, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    settings = _settings(tmp_path)
    monkeypatch.setattr(
        "app.xninetzy.core.coding_agents.shutil.which", lambda binary: f"/bin/{binary}"
    )

    command = build_command("codex", "fix tests", repo, settings)

    assert command[:3] == ["codex-test", "exec", "--json"]
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert command[-1] == "fix tests"


def test_claude_and_opencode_never_use_bypass_flags(monkeypatch, tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    settings = _settings(tmp_path)
    monkeypatch.setattr(
        "app.xninetzy.core.coding_agents.shutil.which", lambda binary: f"/bin/{binary}"
    )

    claude = build_command("claude-code", "review", repo, settings)
    opencode = build_command("opencode", "review", repo, settings)

    assert "--dangerously-skip-permissions" not in claude
    assert "--auto" not in opencode
    assert "acceptEdits" in claude


def test_runtime_catalog_reports_installed_binaries(monkeypatch, tmp_path) -> None:
    settings = _settings(tmp_path)
    monkeypatch.setattr(
        "app.xninetzy.core.coding_agents.shutil.which", lambda binary: None
    )

    catalog = runtime_catalog(settings)

    assert catalog["internal"].installed is True
    assert catalog["codex"].installed is False


def test_subprocess_environment_does_not_inherit_service_secrets(
    monkeypatch, tmp_path
) -> None:
    settings = _settings(tmp_path)
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("FLAZ_API_KEY", "must-not-leak")

    environment = subprocess_environment(settings)

    assert environment["PATH"] == "/usr/bin"
    assert "FLAZ_API_KEY" not in environment
