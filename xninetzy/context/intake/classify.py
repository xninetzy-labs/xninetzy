from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xninetzy.context.intake.layout import (
    LAYOUT_FILE_CAPABILITIES,
    LAYOUT_FILE_MANIFEST_DOCKER,
    LAYOUT_FILE_MANIFEST_NPM,
    LAYOUT_FILE_MANIFEST_PYTHON,
    LAYOUT_FILE_README,
    RepoLayout,
)


REPO_KIND_MCP_SERVER: str = "mcp_server"
REPO_KIND_PYTHON_PACKAGE: str = "python_package"
REPO_KIND_NPM_PACKAGE: str = "npm_package"
REPO_KIND_REST_API: str = "rest_api"
REPO_KIND_DOCKER: str = "docker_service"
REPO_KIND_CLI_TOOL: str = "cli_tool"
REPO_KIND_LIBRARY: str = "library"
REPO_KIND_UNKNOWN: str = "unknown"


_MCP_TRANSPORT_STDIO: str = "stdio"
_MCP_TRANSPORT_HTTP: str = "http"


class _RepoKindNamespace:
    MCP_SERVER: str = REPO_KIND_MCP_SERVER
    PYTHON_PACKAGE: str = REPO_KIND_PYTHON_PACKAGE
    NPM_PACKAGE: str = REPO_KIND_NPM_PACKAGE
    REST_API: str = REPO_KIND_REST_API
    DOCKER: str = REPO_KIND_DOCKER
    CLI_TOOL: str = REPO_KIND_CLI_TOOL
    LIBRARY: str = REPO_KIND_LIBRARY
    UNKNOWN: str = REPO_KIND_UNKNOWN


RepoKind: _RepoKindNamespace = _RepoKindNamespace()

_MCP_HINTS: tuple[str, ...] = (
    "modelcontextprotocol",
    "fastmcp",
    "@modelcontextprotocol",
    "mcp.server",
    "mcp.server.fastmcp",
    "fastmcp.server",
)

_REST_HINTS: tuple[str, ...] = (
    "fastapi",
    "flask",
    "express",
    "django",
    "gin",
    "actix-web",
    "spring-boot",
)

_CLI_HINTS: tuple[str, ...] = (
    "click",
    "typer",
    "argparse",
    "commander",
)

_DOCKER_HINT: str = "docker"

_PYPROJECT_TOML_RE = re.compile(r"^\[project\]", re.MULTILINE | re.IGNORECASE)
_SETUPTOOLS_RE = re.compile(r"^setup\s*\(", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class ClassificationEvidence:
    signal: str
    detail: str


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    kind: str
    suggested_transport: str | None
    suggested_capabilities: tuple[str, ...]
    evidence: tuple[ClassificationEvidence, ...]
    manifest_paths: tuple[Path, ...]

    @property
    def primary_kind(self) -> str:
        return self.kind


def _read_text(path: Path, *, limit: int = 200_000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) > limit:
        return text[:limit]
    return text


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def detect_mcp_server(layout: RepoLayout) -> ClassificationEvidence | None:
    candidates: list[str] = []
    for path in layout.readme_paths:
        text = _read_text(path)
        lowered = text.lower()
        for hint in _MCP_HINTS:
            if hint.lower() in lowered:
                candidates.append(f"readme:{path.name}:{hint}")
                break
    for path in layout.capability_paths:
        payload = _read_json(path)
        if payload and isinstance(payload.get("tools"), list):
            candidates.append(f"manifest:{path.name}:tools[]")
    for path in layout.pyproject_paths:
        text = _read_text(path)
        lowered = text.lower()
        for hint in ("mcp", "fastmcp", "modelcontextprotocol"):
            if hint in lowered:
                candidates.append(f"pyproject:{path.name}:{hint}")
                break
    for path in layout.entry_script_paths:
        text = _read_text(path)
        lowered = text.lower()
        for hint in ("fastmcp", "modelcontextprotocol"):
            if hint in lowered:
                candidates.append(f"entry:{path.name}:{hint}")
                break
    if not candidates:
        return None
    return ClassificationEvidence(
        signal="mcp_server",
        detail=",".join(sorted(set(candidates))),
    )


def detect_python_package(layout: RepoLayout) -> ClassificationEvidence | None:
    for path in layout.pyproject_paths:
        text = _read_text(path)
        if path.name == "pyproject.toml" and _PYPROJECT_TOML_RE.search(text):
            return ClassificationEvidence(
                signal="pyproject",
                detail=f"path={path.name}:[project]",
            )
        if path.name == "setup.py" and _SETUPTOOLS_RE.search(text):
            return ClassificationEvidence(
                signal="setup_py",
                detail=f"path={path.name}",
            )
        if path.name == "setup.cfg" and "[metadata]" in text:
            return ClassificationEvidence(
                signal="setup_cfg",
                detail=f"path={path.name}",
            )
    return None


def detect_npm_package(layout: RepoLayout) -> ClassificationEvidence | None:
    for path in layout.npm_paths:
        payload = _read_json(path)
        if payload is None:
            continue
        if "name" in payload or "dependencies" in payload or "bin" in payload:
            bin = payload.get("bin")
            detail = f"path={path.name}"
            if isinstance(bin, str):
                detail = f"{detail}:bin={bin}"
            elif isinstance(bin, dict) and bin:
                detail = f"{detail}:bin={next(iter(bin))}"
            return ClassificationEvidence(signal="package_json", detail=detail)
    return None


def detect_docker_indicator(layout: RepoLayout) -> ClassificationEvidence | None:
    if not layout.docker_paths:
        return None
    name = layout.docker_paths[0].name
    return ClassificationEvidence(signal="dockerfile", detail=f"path={name}")


def detect_rest_api(layout: RepoLayout) -> ClassificationEvidence | None:
    candidates: list[str] = []
    for path in layout.pyproject_paths:
        text = _read_text(path)
        lowered = text.lower()
        for hint in _REST_HINTS:
            if hint in lowered:
                candidates.append(f"pyproject:{path.name}:{hint}")
                break
    for path in layout.npm_paths:
        payload = _read_json(path)
        if payload is None:
            continue
        deps = payload.get("dependencies") or {}
        if isinstance(deps, dict):
            for hint in _REST_HINTS:
                if hint in {key.lower() for key in deps}:
                    candidates.append(f"package.json:deps:{hint}")
                    break
    for path in layout.readme_paths:
        text = _read_text(path).lower()
        if "rest api" in text or "openapi" in text:
            candidates.append(f"readme:{path.name}:rest_api")
            break
    if not candidates:
        return None
    return ClassificationEvidence(signal="rest_api", detail=",".join(sorted(set(candidates))))


def _capabilities_from_manifest(layout: RepoLayout) -> tuple[str, ...]:
    for path in layout.capability_paths:
        payload = _read_json(path)
        if payload is None:
            continue
        tools = payload.get("tools")
        if isinstance(tools, list):
            names: list[str] = []
            for item in tools:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict) and isinstance(item.get("name"), str):
                    names.append(str(item["name"]))
            if names:
                return tuple(sorted(set(names)))
        capabilities = payload.get("capabilities")
        if isinstance(capabilities, list):
            return tuple(sorted(str(item) for item in capabilities if isinstance(item, str)))
    return ()


def _manifest_paths(layout: RepoLayout) -> tuple[Path, ...]:
    paths: list[Path] = []
    paths.extend(layout.capability_paths)
    paths.extend(layout.pyproject_paths)
    paths.extend(layout.npm_paths)
    paths.extend(layout.docker_paths)
    return tuple(paths)


def classify_layout(layout: RepoLayout) -> ClassificationResult:
    detected: list[ClassificationEvidence] = []
    mcp_evidence = detect_mcp_server(layout)
    py_evidence = detect_python_package(layout)
    npm_evidence = detect_npm_package(layout)
    docker_evidence = detect_docker_indicator(layout)
    rest_evidence = detect_rest_api(layout)
    if mcp_evidence is not None:
        detected.append(mcp_evidence)
    if py_evidence is not None:
        detected.append(py_evidence)
    if npm_evidence is not None:
        detected.append(npm_evidence)
    if docker_evidence is not None:
        detected.append(docker_evidence)
    if rest_evidence is not None:
        detected.append(rest_evidence)
    transport: str | None = None
    capabilities = _capabilities_from_manifest(layout)
    if mcp_evidence is not None:
        kind = REPO_KIND_MCP_SERVER
        transport = _MCP_TRANSPORT_STDIO
        if not capabilities:
            capabilities = ("tool_execute",)
    elif rest_evidence is not None:
        kind = REPO_KIND_REST_API
        transport = _MCP_TRANSPORT_HTTP
    elif docker_evidence is not None:
        kind = REPO_KIND_DOCKER
        transport = _MCP_TRANSPORT_HTTP
    elif py_evidence is not None:
        if layout.entry_script_paths:
            kind = REPO_KIND_CLI_TOOL
        else:
            kind = REPO_KIND_PYTHON_PACKAGE
    elif npm_evidence is not None:
        kind = REPO_KIND_NPM_PACKAGE
    else:
        kind = REPO_KIND_LIBRARY if layout.readme_paths else REPO_KIND_UNKNOWN
    manifest_paths = _manifest_paths(layout)
    return ClassificationResult(
        kind=kind,
        suggested_transport=transport,
        suggested_capabilities=capabilities,
        evidence=tuple(detected),
        manifest_paths=manifest_paths,
    )


def iter_layout_signals(layout: RepoLayout) -> dict[str, bool]:
    return {
        LAYOUT_FILE_README: layout.has(LAYOUT_FILE_README),
        LAYOUT_FILE_MANIFEST_PYTHON: layout.has(LAYOUT_FILE_MANIFEST_PYTHON),
        LAYOUT_FILE_MANIFEST_NPM: layout.has(LAYOUT_FILE_MANIFEST_NPM),
        LAYOUT_FILE_MANIFEST_DOCKER: layout.has(LAYOUT_FILE_MANIFEST_DOCKER),
        LAYOUT_FILE_CAPABILITIES: layout.has(LAYOUT_FILE_CAPABILITIES),
    }
