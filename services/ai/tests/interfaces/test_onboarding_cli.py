from __future__ import annotations

import json
import subprocess
import sys

import pytest

from app.xninetzy.interfaces.config_cli import ConfigurationCatalog, EnvConfiguration
from app.xninetzy.interfaces import onboarding_cli
from app.xninetzy.interfaces.onboarding_cli import (
    DoctorCheck,
    run_doctor,
    run_setup,
)


@pytest.fixture
def onboarding_config(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(
        "AI_API_URL=http://127.0.0.1:8000\nXNINETZY_AI_URL=http://127.0.0.1:8000\nFLAZ_API_KEY=\n",
        encoding="utf-8",
    )
    return EnvConfiguration(
        catalog=ConfigurationCatalog.load(example),
        env_path=tmp_path / ".env",
    )


def test_setup_configures_provider_without_returning_secret(onboarding_config):
    result = run_setup(
        onboarding_config,
        provider="flaz",
        model="deepseek-v4-pro",
        api_key="private-value",
        prompt=False,
    )

    values = onboarding_config.values()

    assert values["LLM_DEFAULT_PROVIDER"] == "flaz"
    assert values["LLM_ENABLED_PROVIDERS"] == "flaz"
    assert values["FLAZ_MODEL"] == "deepseek-v4-pro"
    assert values["FLAZ_API_KEY"] == "private-value"
    assert "FLAZ_API_KEY" in result["configured_keys"]
    assert "private-value" not in json.dumps(result)


def test_setup_supports_local_provider_without_api_key(onboarding_config):
    result = run_setup(
        onboarding_config,
        provider="ollama",
        model="qwen2.5:7b",
        api_key=None,
        prompt=False,
    )

    assert onboarding_config.values()["OLLAMA_MODEL"] == "qwen2.5:7b"
    assert result["secret_required"] == []


def test_doctor_is_read_only_and_reports_invalid_configuration(onboarding_config):
    onboarding_config.env_path.write_text(
        "LLM_DEFAULT_PROVIDER=invalid-provider\n",
        encoding="utf-8",
    )

    result = run_doctor(
        onboarding_config,
        check_docker=False,
        check_services=False,
    )

    configuration = next(
        check for check in result["checks"] if check["name"] == "configuration"
    )
    provider = next(
        check for check in result["checks"] if check["name"] == "llm-provider"
    )

    assert result["ok"] is False
    assert configuration["status"] == "pass"
    assert provider["status"] == "fail"


def test_doctor_uses_optional_checks_only_when_requested(onboarding_config, monkeypatch):
    onboarding_config.set("LLM_DEFAULT_PROVIDER", "ollama")
    onboarding_config.set("OLLAMA_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(
        "app.xninetzy.interfaces.onboarding_cli._binary_check",
        lambda name, required: DoctorCheck(name, "pass", "available"),
    )

    result = run_doctor(
        onboarding_config,
        check_docker=False,
        check_services=False,
    )

    statuses = {check["name"]: check["status"] for check in result["checks"]}

    assert result["ok"] is True
    assert statuses["docker-compose"] == "skip"
    assert statuses["ai-service"] == "skip"


def test_docker_check_returns_failure_when_process_times_out(monkeypatch, tmp_path):
    monkeypatch.setattr(onboarding_cli.shutil, "which", lambda name: "/usr/bin/docker")

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("docker", 30)

    monkeypatch.setattr(onboarding_cli.subprocess, "run", raise_timeout)

    result = onboarding_cli._docker_check(tmp_path / ".env")

    assert result.status == "fail"
    assert "failed" in result.message



def test_service_check_explains_docker_only_hostname():
    check = onboarding_cli._service_check({"AI_API_URL": "http://ai:8000"})

    assert check.status == "warn"
    assert "Docker-only" in check.message

def test_module_cli_setup_and_doctor_with_selected_env_file(tmp_path):
    env_path = tmp_path / ".env"
    setup = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.xninetzy.interfaces.onboarding_cli",
            "setup",
            "--provider",
            "ollama",
            "--model",
            "qwen2.5:7b",
            "--no-prompt",
            "--env-file",
            str(env_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    doctor = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.xninetzy.interfaces.onboarding_cli",
            "doctor",
            "--env-file",
            str(env_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert setup.returncode == 0, setup.stderr
    assert doctor.returncode == 0, doctor.stderr
    assert json.loads(setup.stdout)["provider"] == "ollama"
    assert json.loads(doctor.stdout)["ok"] is True

def test_setup_applies_a_host_safe_docker_profile(onboarding_config):
    result = run_setup(
        onboarding_config,
        provider="ollama",
        model="qwen2.5:7b",
        api_key=None,
        prompt=False,
        deployment="docker",
    )

    values = onboarding_config.values()

    assert result["deployment"] == "docker"
    assert values["XNINETZY_AI_URL"] == "http://127.0.0.1:8000"
    assert values["MCP_RUNTIME_MODE"] == "auto"


def test_doctor_skips_mcp_preflight_without_explicit_request(
    onboarding_config,
    monkeypatch,
):
    onboarding_config.set("LLM_DEFAULT_PROVIDER", "ollama")
    onboarding_config.set("OLLAMA_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(
        "app.xninetzy.interfaces.onboarding_cli._binary_check",
        lambda name, required: DoctorCheck(name, "pass", "available"),
    )

    result = run_doctor(
        onboarding_config,
        check_docker=False,
        check_services=False,
    )

    statuses = {check["name"]: check["status"] for check in result["checks"]}

    assert statuses["xninetzy-mcp"] == "skip"


def test_mcp_preflight_uses_shared_runtime_command(onboarding_config, monkeypatch):
    onboarding_config.env_path.write_text(
        "\n".join(
            [
                "CODING_AGENT_ENABLED=true",
                "CODING_AGENT_DEFAULT=opencode",
                "CODING_AGENT_ALLOWED=opencode",
                "OPENCODE_BIN=opencode",
                "CODING_AGENT_MCP_SERVER_NAME=xninetzy",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        onboarding_cli,
        "build_mcp_preflight_command",
        lambda runtime, settings: ["opencode", "mcp", "list"],
    )
    monkeypatch.setattr(onboarding_cli, "subprocess_environment", lambda settings: {})
    monkeypatch.setattr(
        onboarding_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="xninetzy connected",
            stderr="",
        ),
    )

    result = onboarding_cli._mcp_preflight_check(onboarding_config)

    assert result.status == "pass"
