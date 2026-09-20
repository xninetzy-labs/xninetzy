from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_supervisor(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "--directory",
            str(REPO_ROOT),
            "python",
            "-m",
            "xninetzy.cli.supervisor",
            *args,
        ],
        capture_output=True,
        text=True,
    )


def test_release_check_emits_pass_lines() -> None:
    proc = _run_supervisor("release-check")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "tool_registry" in proc.stdout
    assert "tools classified" in proc.stdout
    assert "secret_redaction" in proc.stdout
    assert "safe_fetch" in proc.stdout
    assert "transport_config" in proc.stdout
    assert "sdk_pin" in proc.stdout
    assert "canonical_final_tools" in proc.stdout
    assert "overall: PASS" in proc.stdout


def test_release_check_exit_nonzero_on_audit_failure(monkeypatch) -> None:
    from xninetzy.cli import supervisor as sup

    monkeypatch.setattr(
        sup,
        "_audit_payload",
        lambda: ({}, ["simulated audit failure"]),
    )
    rc = sup.main(["release-check"])
    assert rc == 2


def test_init_creates_configured_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("GENERATED_DOCUMENTS_DIR", str(tmp_path / "docs"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("HEBAT_DATA_DIR", str(tmp_path / "hebat"))
    from xninetzy.core import config as cfg

    cfg.get_settings.cache_clear()
    rc = cfg.get_settings.cache_clear() or 0
    from xninetzy.cli import supervisor as sup

    rc = sup.main(["init"])
    assert rc == 0
    assert (tmp_path / "data").exists()
    assert (tmp_path / "out").exists()
    assert (tmp_path / "docs").exists()
    assert (tmp_path / "vault").exists()


def test_start_dry_run_does_not_exec_server() -> None:
    proc = _run_supervisor("start", "--dry-run")
    assert proc.returncode == 0, proc.stderr
    assert "dry-run" in proc.stderr
    assert "xninetzy.interfaces.mcp_server" in proc.stderr


def test_start_rejects_invalid_transport(monkeypatch) -> None:
    monkeypatch.setenv("XNINETZY_MCP_TRANSPORT", "bogus")
    from xninetzy.cli import supervisor as sup

    rc = sup.main(["start", "--dry-run"])
    assert rc == 2


def test_orchestrator_passthrough_help() -> None:
    proc = _run_supervisor("orchestrator", "--help")
    assert proc.returncode == 0
    assert "orchestrator" in proc.stdout


def test_supervisor_module_importable() -> None:
    import xninetzy.cli.supervisor as sup  # noqa: F401
    assert hasattr(sup, "main")
