from __future__ import annotations

import argparse
import getpass
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from app.xninetzy.core.coding_agents import (
    build_mcp_preflight_command,
    subprocess_environment,
)
from app.xninetzy.core.config import Settings

from app.xninetzy.interfaces.config_cli import (
    ConfigurationError,
    EnvConfiguration,
    _emit,
)


_PROVIDER_FIELDS: dict[str, tuple[str, str | None]] = {
    "flaz": ("FLAZ_MODEL", "FLAZ_API_KEY"),
    "openai": ("OPENAI_MODEL", "OPENAI_API_KEY"),
    "anthropic": ("ANTHROPIC_MODEL", "ANTHROPIC_API_KEY"),
    "openrouter": ("OPENROUTER_MODEL", "OPENROUTER_API_KEY"),
    "ollama": ("OLLAMA_MODEL", None),
    "generic-openai": ("GENERIC_OPENAI_MODEL", "GENERIC_OPENAI_API_KEY"),
}


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    status: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
        }


def _add_env_file_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Set up and diagnose Xninetzy.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Configure one chat provider safely.")
    _add_env_file_option(setup)
    setup.add_argument("--provider", choices=sorted(_PROVIDER_FIELDS))
    setup.add_argument("--model")
    setup.add_argument("--deployment", choices=("native", "docker"), default="native")
    setup.add_argument("--api-key-stdin", action="store_true")
    setup.add_argument("--no-prompt", action="store_true")
    setup.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Run non-destructive installation checks.")
    _add_env_file_option(doctor)
    doctor.add_argument("--docker", action="store_true")
    doctor.add_argument("--services", action="store_true")
    doctor.add_argument("--mcp", action="store_true")
    doctor.add_argument("--json", action="store_true")
    return parser


def run_setup(
    config: EnvConfiguration,
    *,
    provider: str | None,
    model: str | None,
    api_key: str | None,
    prompt: bool,
    deployment: str = "native",
) -> dict[str, Any]:
    values = config.values()
    selected_provider = provider or values.get("LLM_DEFAULT_PROVIDER", "flaz")
    if prompt and provider is None:
        selected_provider = input(f"Provider [{selected_provider}]: ").strip() or selected_provider
    if selected_provider not in _PROVIDER_FIELDS:
        raise ConfigurationError(f"Unsupported provider: {selected_provider}")

    model_key, key_name = _PROVIDER_FIELDS[selected_provider]
    selected_model = model or values.get(model_key, "")
    if prompt and not selected_model:
        selected_model = input(f"{model_key}: ").strip()
    if not selected_model:
        raise ConfigurationError(f"{model_key} is required for {selected_provider}")

    configured_keys = ["LLM_DEFAULT_PROVIDER", "LLM_ENABLED_PROVIDERS", model_key]
    config.set("LLM_DEFAULT_PROVIDER", selected_provider)
    config.set("LLM_ENABLED_PROVIDERS", selected_provider)
    config.set(model_key, selected_model)

    secret_required: list[str] = []
    if key_name:
        selected_key = api_key
        if selected_key is None and prompt:
            selected_key = getpass.getpass(f"{key_name}: ")
        if selected_key:
            config.set(key_name, selected_key)
            configured_keys.append(key_name)
        else:
            secret_required.append(key_name)

    configured_keys.extend(_apply_deployment_profile(config, deployment))

    return {
        "provider": selected_provider,
        "deployment": deployment,
        "configured_keys": configured_keys,
        "secret_required": secret_required,
        "env_file": str(config.env_path),
        "next_steps": [
            "Run 'xninetzy doctor'.",
            _deployment_start_command(deployment),
        ],
    }

def _apply_deployment_profile(
    config: EnvConfiguration,
    deployment: str,
) -> list[str]:
    if deployment not in {"native", "docker"}:
        raise ConfigurationError(f"Unsupported deployment: {deployment}")

    profile = {
        "XNINETZY_AI_URL": "http://127.0.0.1:8000",
        "MCP_RUNTIME_MODE": "host" if deployment == "native" else "auto",
    }
    for key, value in profile.items():
        config.set(key, value)
    return list(profile)


def _deployment_start_command(deployment: str) -> str:
    if deployment == "docker":
        return "Start Docker with 'docker compose up --build -d ai wa-enggine'."
    return (
        "Start the AI service with "
        "'cd services/ai && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000'."
    )


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docker-compose.yml").exists():
            return parent
    return Path.cwd()


def _cli_target_check(values: dict[str, str]) -> DoctorCheck:
    base_url = values.get("XNINETZY_AI_URL", "http://127.0.0.1:8000").rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return DoctorCheck(
            name="cli-target",
            status="fail",
            message="XNINETZY_AI_URL must be an absolute HTTP(S) URL.",
        )
    if parsed.hostname == "ai":
        return DoctorCheck(
            name="cli-target",
            status="warn",
            message=(
                "XNINETZY_AI_URL uses the Docker-only 'ai' hostname. "
                "Use http://127.0.0.1:8000 for the host CLI."
            ),
        )
    return DoctorCheck(
        name="cli-target",
        status="pass",
        message=f"Host CLI target is {base_url}.",
    )


def _mcp_runtime_mode_check(values: dict[str, str]) -> DoctorCheck:
    mode = values.get("MCP_RUNTIME_MODE", "auto").strip().casefold()
    if mode == "container":
        return DoctorCheck(
            name="mcp-runtime-mode",
            status="fail",
            message=(
                "MCP_RUNTIME_MODE=container is reserved for the Docker Compose "
                "service override. Use auto or host in the root .env."
            ),
        )
    if mode not in {"auto", "host"}:
        return DoctorCheck(
            name="mcp-runtime-mode",
            status="fail",
            message="MCP_RUNTIME_MODE must be auto, host, or container.",
        )
    return DoctorCheck(
        name="mcp-runtime-mode",
        status="pass",
        message=f"Host MCP runtime mode is {mode}.",
    )


def _mcp_preflight_check(config: EnvConfiguration) -> DoctorCheck:
    try:
        settings = Settings(_env_file=config.env_path)
    except Exception:
        return DoctorCheck(
            name="xninetzy-mcp",
            status="fail",
            message="Unable to load settings for the MCP preflight.",
        )
    if not settings.CODING_AGENT_ENABLED:
        return DoctorCheck(
            name="xninetzy-mcp",
            status="skip",
            message="Coding runtime is disabled.",
        )
    runtime = settings.CODING_AGENT_DEFAULT.strip().casefold()
    if runtime == "internal":
        return DoctorCheck(
            name="xninetzy-mcp",
            status="pass",
            message="Internal runtime does not require an external MCP preflight.",
        )
    try:
        command = build_mcp_preflight_command(runtime, settings)
    except ValueError as error:
        return DoctorCheck(name="xninetzy-mcp", status="fail", message=str(error))
    try:
        result = subprocess.run(
            command,
            cwd=_repository_root(),
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS,
            env=subprocess_environment(settings),
        )
    except subprocess.TimeoutExpired:
        return DoctorCheck(
            name="xninetzy-mcp",
            status="fail",
            message=(
                "MCP preflight timed out. Check the global Xninetzy MCP "
                "configuration, then retry or increase "
                "CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS."
            ),
        )
    except OSError:
        return DoctorCheck(
            name="xninetzy-mcp",
            status="fail",
            message=(
                "MCP preflight could not start. Check the selected coding "
                "runtime binary and its global MCP configuration."
            ),
        )
    server_name = settings.CODING_AGENT_MCP_SERVER_NAME.strip().casefold() or "xninetzy"
    output = f"{result.stdout}\n{result.stderr}".casefold()
    relevant = "\n".join(line for line in output.splitlines() if server_name in line)
    negative_markers = (
        "not found",
        "failed",
        "pending approval",
        "not connected",
        "disconnected",
        "error",
    )
    connected = result.returncode == 0 and bool(relevant)
    if any(marker in relevant for marker in negative_markers):
        connected = False
    if connected:
        return DoctorCheck(
            name="xninetzy-mcp",
            status="pass",
            message=f"MCP '{server_name}' is available to {runtime}.",
        )
    return DoctorCheck(
        name="xninetzy-mcp",
        status="fail",
        message=(
            f"MCP '{server_name}' is unavailable to {runtime}. "
            "Install the global MCP configuration and retry."
        ),
    )





def run_doctor(
    config: EnvConfiguration,
    *,
    check_docker: bool,
    check_services: bool,
    check_mcp: bool = False,
) -> dict[str, Any]:
    checks: list[DoctorCheck] = []
    validation = config.validate()
    checks.append(
        DoctorCheck(
            name="configuration",
            status="pass" if validation["valid"] else "fail",
            message=(
                "Configuration is valid."
                if validation["valid"]
                else "Configuration contains unknown or invalid values."
            ),
        )
    )
    checks.append(
        _binary_check("uv", required=True)
    )
    checks.append(
        _binary_check("node", required=False)
    )
    checks.extend(_provider_checks(config.values()))
    checks.extend(_coding_runtime_checks(config.values()))
    checks.append(_cli_target_check(config.values()))
    checks.append(_mcp_runtime_mode_check(config.values()))

    if check_docker:
        checks.append(_docker_check(config.env_path))
    else:
        checks.append(
            DoctorCheck(
                name="docker-compose",
                status="skip",
                message="Run with --docker to validate Docker Compose.",
            )
        )

    if check_services:
        checks.append(_service_check(config.values()))
    else:
        checks.append(
            DoctorCheck(
                name="ai-service",
                status="skip",
                message="Run with --services to check the local AI service.",
            )
        )

    if check_mcp:
        checks.append(_mcp_preflight_check(config))
    else:
        checks.append(
            DoctorCheck(
                name="xninetzy-mcp",
                status="skip",
                message="Run with --mcp to validate the selected coding runtime MCP access.",
            )
        )

    failures = [check.name for check in checks if check.status == "fail"]
    warnings = [check.name for check in checks if check.status == "warn"]
    return {
        "ok": not failures,
        "env_file": str(config.env_path),
        "checks": [check.as_dict() for check in checks],
        "failures": failures,
        "warnings": warnings,
    }


def _binary_check(name: str, required: bool) -> DoctorCheck:
    available = shutil.which(name) is not None
    if available:
        return DoctorCheck(name=name, status="pass", message=f"{name} is available.")
    return DoctorCheck(
        name=name,
        status="fail" if required else "warn",
        message=f"{name} is not available on PATH.",
    )


def _provider_checks(values: dict[str, str]) -> list[DoctorCheck]:
    provider = values.get("LLM_DEFAULT_PROVIDER", "flaz")
    fields = _PROVIDER_FIELDS.get(provider)
    if fields is None:
        return [
            DoctorCheck(
                name="llm-provider",
                status="fail",
                message=f"Unsupported LLM_DEFAULT_PROVIDER: {provider}.",
            )
        ]
    model_key, key_name = fields
    checks = [
        DoctorCheck(
            name="llm-model",
            status="pass" if values.get(model_key) else "warn",
            message=(
                f"{model_key} is configured."
                if values.get(model_key)
                else f"{model_key} is not configured."
            ),
        )
    ]
    if key_name:
        checks.append(
            DoctorCheck(
                name="llm-credential",
                status="pass" if values.get(key_name) else "warn",
                message=(
                    f"{key_name} is configured."
                    if values.get(key_name)
                    else f"{key_name} is not configured."
                ),
            )
        )
    return checks


def _coding_runtime_checks(values: dict[str, str]) -> list[DoctorCheck]:
    if values.get("CODING_AGENT_ENABLED", "false").casefold() != "true":
        return [
            DoctorCheck(
                name="coding-runtime",
                status="skip",
                message="Coding runtime is disabled.",
            )
        ]
    runtime = values.get("CODING_AGENT_DEFAULT", "internal")
    binary_name = {
        "codex": values.get("CODEX_BIN", "codex"),
        "claude-code": values.get("CLAUDE_CODE_BIN", "claude"),
        "opencode": values.get("OPENCODE_BIN", "opencode"),
    }.get(runtime)
    if binary_name is None:
        return [
            DoctorCheck(
                name="coding-runtime",
                status="pass",
                message=f"{runtime} does not require an external CLI binary.",
            )
        ]
    return [
        DoctorCheck(
            name="coding-runtime",
            status="pass" if shutil.which(binary_name) else "fail",
            message=(
                f"{binary_name} is available."
                if shutil.which(binary_name)
                else f"{binary_name} is missing from PATH."
            ),
        )
    ]


def _docker_check(env_path: Path) -> DoctorCheck:
    if shutil.which("docker") is None:
        return DoctorCheck(
            name="docker-compose",
            status="fail",
            message="docker is not available on PATH.",
        )
    try:
        result = subprocess.run(
            ["docker", "compose", "--env-file", str(env_path), "config", "-q"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return DoctorCheck(
            name="docker-compose",
            status="fail",
            message=f"Docker Compose check failed: {error}",
        )
    if result.returncode == 0:
        return DoctorCheck(
            name="docker-compose",
            status="pass",
            message="Docker Compose configuration is valid.",
        )
    message = result.stderr.strip() or result.stdout.strip() or "Docker Compose failed."
    return DoctorCheck(
        name="docker-compose",
        status="fail",
        message=message[:400],
    )


def _service_check(values: dict[str, str]) -> DoctorCheck:
    base_url = values.get("AI_API_URL", "http://127.0.0.1:8000").rstrip("/")
    host = urlparse(base_url).hostname
    if host == "ai":
        return DoctorCheck(
            name="ai-service",
            status="warn",
            message=(
                "AI_API_URL uses the Docker-only 'ai' hostname. Use "
                "http://127.0.0.1:8000 for the host CLI or run the CLI in Docker."
            ),
        )
    try:
        with urlopen(f"{base_url}/health", timeout=3) as response:
            healthy = 200 <= response.status < 300
    except (OSError, URLError) as error:
        return DoctorCheck(
            name="ai-service",
            status="warn",
            message=f"AI service is unavailable: {error}",
        )
    return DoctorCheck(
        name="ai-service",
        status="pass" if healthy else "warn",
        message=(
            "AI service is reachable."
            if healthy
            else f"AI service returned HTTP {response.status}."
        ),
    )


def _read_setup_key(args: argparse.Namespace, prompt: bool) -> str | None:
    if args.api_key_stdin:
        return sys.stdin.read().rstrip("\r\n")
    if prompt:
        return None
    return None


def main() -> None:
    args = build_parser().parse_args()
    config = EnvConfiguration(env_path=args.env_file)
    try:
        if args.command == "setup":
            result = run_setup(
                config,
                provider=args.provider,
                model=args.model,
                api_key=_read_setup_key(args, not args.no_prompt),
                prompt=not args.no_prompt,
                deployment=args.deployment,
            )
            _emit(result, args.json)
            return
        result = run_doctor(
            config,
            check_docker=args.docker,
            check_services=args.services,
            check_mcp=args.mcp,
        )
        _emit(result, args.json)
        if not result["ok"]:
            raise SystemExit(1)
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()

