from __future__ import annotations

from xninetzy.context.intake.classify import (
    REPO_KIND_CLI_TOOL,
    REPO_KIND_DOCKER,
    REPO_KIND_LIBRARY,
    REPO_KIND_MCP_SERVER,
    REPO_KIND_NPM_PACKAGE,
    REPO_KIND_PYTHON_PACKAGE,
    REPO_KIND_REST_API,
    classify_layout,
    detect_docker_indicator,
    detect_mcp_server,
    detect_npm_package,
    detect_python_package,
    detect_rest_api,
)
from xninetzy.context.intake.layout import collect_layout


def _seed(repo, *, readme=None, pyproject=None, package_json=None, dockerfile=None, capabilities=None, entry=None):
    root = repo
    if readme is not None:
        (root / "README.md").write_text(readme, encoding="utf-8")
    if pyproject is not None:
        (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    if package_json is not None:
        (root / "package.json").write_text(package_json, encoding="utf-8")
    if dockerfile is not None:
        (root / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    if capabilities is not None:
        (root / "mcp_capabilities.json").write_text(capabilities, encoding="utf-8")
    if entry is not None:
        (root / entry).write_text("print('hello')\n", encoding="utf-8")
    return collect_layout(root)


def test_detect_python_package_with_pyproject(tmp_path):
    layout = _seed(tmp_path, pyproject="[project]\nname='x'")
    evidence = detect_python_package(layout)
    assert evidence is not None
    assert evidence.signal == "pyproject"


def test_detect_python_package_with_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text("setup(name='x')", encoding="utf-8")
    layout = collect_layout(tmp_path)
    evidence = detect_python_package(layout)
    assert evidence is not None
    assert evidence.signal == "setup_py"


def test_detect_python_package_returns_none_when_absent(tmp_path):
    layout = _seed(tmp_path, readme="# nothing")
    assert detect_python_package(layout) is None


def test_detect_npm_package(tmp_path):
    layout = _seed(tmp_path, package_json='{"name": "x", "bin": "x.js"}')
    evidence = detect_npm_package(layout)
    assert evidence is not None
    assert "bin=x.js" in evidence.detail


def test_detect_npm_package_invalid_json_returns_none(tmp_path):
    (tmp_path / "package.json").write_text("not json", encoding="utf-8")
    layout = collect_layout(tmp_path)
    assert detect_npm_package(layout) is None


def test_detect_mcp_server_from_readme(tmp_path):
    layout = _seed(tmp_path, readme="Uses fastmcp and modelcontextprotocol")
    evidence = detect_mcp_server(layout)
    assert evidence is not None


def test_detect_mcp_server_from_capabilities_manifest(tmp_path):
    layout = _seed(tmp_path, capabilities='{"tools": ["foo", "bar"]}')
    evidence = detect_mcp_server(layout)
    assert evidence is not None


def test_detect_mcp_server_returns_none_for_plain_library(tmp_path):
    layout = _seed(tmp_path, readme="Just a library", pyproject="[project]\nname='x'")
    assert detect_mcp_server(layout) is None


def test_detect_rest_api_from_pyproject_fastapi(tmp_path):
    layout = _seed(tmp_path, pyproject="[project]\nname='x'\ndependencies=['fastapi']")
    evidence = detect_rest_api(layout)
    assert evidence is not None
    assert "fastapi" in evidence.detail


def test_detect_docker_indicator(tmp_path):
    layout = _seed(tmp_path, dockerfile="FROM python:3.11")
    evidence = detect_docker_indicator(layout)
    assert evidence is not None
    assert evidence.signal == "dockerfile"


def test_classify_layout_mcp_server(tmp_path):
    layout = _seed(
        tmp_path,
        readme="Built on fastmcp",
        pyproject="[project]\nname='x'",
        capabilities='{"tools": ["do_thing"]}',
    )
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_MCP_SERVER
    assert result.suggested_transport == "stdio"
    assert "do_thing" in result.suggested_capabilities


def test_classify_layout_rest_api(tmp_path):
    layout = _seed(
        tmp_path,
        readme="REST API",
        pyproject="[project]\nname='x'\ndependencies=['fastapi']",
    )
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_REST_API
    assert result.suggested_transport == "http"


def test_classify_layout_docker_service(tmp_path):
    layout = _seed(tmp_path, dockerfile="FROM python:3.11", pyproject="[project]\nname='x'")
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_DOCKER


def test_classify_layout_cli_tool_with_entry(tmp_path):
    layout = _seed(tmp_path, pyproject="[project]\nname='x'", entry="main.py")
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_CLI_TOOL


def test_classify_layout_python_package_without_entry(tmp_path):
    layout = _seed(tmp_path, pyproject="[project]\nname='x'")
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_PYTHON_PACKAGE


def test_classify_layout_npm_package(tmp_path):
    layout = _seed(tmp_path, package_json='{"name": "x", "bin": "x.js"}')
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_NPM_PACKAGE


def test_classify_layout_library_only_with_readme(tmp_path):
    layout = _seed(tmp_path, readme="Just docs")
    result = classify_layout(layout)
    assert result.kind == REPO_KIND_LIBRARY


def test_classify_layout_collects_evidence_signals(tmp_path):
    layout = _seed(
        tmp_path,
        readme="REST API built on fastmcp",
        pyproject="[project]\nname='x'",
        dockerfile="FROM python:3.11",
    )
    result = classify_layout(layout)
    signals = {ev.signal for ev in result.evidence}
    assert "mcp_server" in signals
    assert "dockerfile" in signals
