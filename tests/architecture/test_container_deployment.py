from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_container_starts_existing_stdio_module_without_http_listener():
    dockerfile = (ROOT / "Dockerfile").read_text()
    match = re.search(r"(?m)^CMD (\[.*\])$", dockerfile)
    assert match is not None
    command = json.loads(match.group(1))
    assert command == ["python", "-m", "xninetzy.interfaces.mcp_server"]
    assert (ROOT / "xninetzy/interfaces/mcp_server.py").is_file()
    assert "xninetzy.main:app" not in dockerfile
    assert not re.search(r"(?m)^EXPOSE ", dockerfile)


def test_minimal_image_does_not_install_browser_or_build_before_source():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "playwright install" not in dockerfile
    assert "--all-extras" not in dockerfile
    assert dockerfile.index("COPY xninetzy") < dockerfile.index("uv sync --frozen")
    assert "--no-dev --no-editable" in dockerfile
    assert re.search(r"(?m)^USER [^r].+", dockerfile)


def test_image_rebuilds_own_package_and_verifies_installed_source():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "--reinstall-package xninetzy-mcp" in dockerfile
    assert "python -I scripts/check_installed_package.py --source /app/xninetzy" in dockerfile


def test_compose_uses_unprivileged_per_client_stdio_without_rest_healthcheck():
    obj = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    service = obj["services"]["xninetzy"]
    assert service["stdin_open"] is True
    assert service["tty"] is False
    assert not service.get("ports")
    assert "healthcheck" not in service
    assert service["restart"] == "no"
    assert service["environment"]["XNINETZY_MCP_TRANSPORT"] == "stdio"
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert not service.get("privileged")
    assert not any("docker.sock" in str(value) for value in service.get("volumes", []))


def test_graph_is_optional_and_existing_graph_volume_names_are_preserved():
    obj = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    assert obj["services"]["neo4j"]["profiles"] == ["graph"]
    assert not obj["services"]["xninetzy"].get("depends_on")
    assert "neo4j-data" in obj["volumes"] and "neo4j-logs" in obj["volumes"]


def test_docker_build_context_is_allowlisted_and_excludes_private_state():
    lines = (ROOT / ".dockerignore").read_text().splitlines()
    assert lines[0] == "**"
    assert "!xninetzy/**" in lines
    for forbidden in (".env", ".secrets", "data", ".git", "**/*.sqlite3"):
        assert forbidden in lines
    assert "!data/**" not in lines
