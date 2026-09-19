from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


LAYOUT_FILE_README: str = "README"
LAYOUT_FILE_MANIFEST_PYTHON: str = "pyproject"
LAYOUT_FILE_MANIFEST_NPM: str = "package_json"
LAYOUT_FILE_MANIFEST_DOCKER: str = "dockerfile"
LAYOUT_FILE_CAPABILITIES: str = "capabilities"

README_CANDIDATES: tuple[str, ...] = (
    "README.md",
    "README.rst",
    "README.txt",
    "README",
    "readme.md",
)

PYPROJECT_CANDIDATES: tuple[str, ...] = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
)

NPM_CANDIDATES: tuple[str, ...] = (
    "package.json",
)

DOCKER_CANDIDATES: tuple[str, ...] = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
)

CAPABILITY_FILE_CANDIDATES: tuple[str, ...] = (
    "mcp_capabilities.json",
    "capabilities.json",
    "tool_manifest.json",
)


@dataclass(frozen=True, slots=True)
class RepoLayout:
    root: Path
    readme_paths: tuple[Path, ...] = field(default_factory=tuple)
    pyproject_paths: tuple[Path, ...] = field(default_factory=tuple)
    npm_paths: tuple[Path, ...] = field(default_factory=tuple)
    docker_paths: tuple[Path, ...] = field(default_factory=tuple)
    capability_paths: tuple[Path, ...] = field(default_factory=tuple)
    entry_script_paths: tuple[Path, ...] = field(default_factory=tuple)
    file_count: int = 0
    total_bytes: int = 0

    def has(self, kind: str) -> bool:
        if kind == LAYOUT_FILE_README:
            return bool(self.readme_paths)
        if kind == LAYOUT_FILE_MANIFEST_PYTHON:
            return bool(self.pyproject_paths)
        if kind == LAYOUT_FILE_MANIFEST_NPM:
            return bool(self.npm_paths)
        if kind == LAYOUT_FILE_MANIFEST_DOCKER:
            return bool(self.docker_paths)
        if kind == LAYOUT_FILE_CAPABILITIES:
            return bool(self.capability_paths)
        return False


def _candidate_paths(root: Path, names: tuple[str, ...]) -> tuple[Path, ...]:
    found: list[Path] = []
    for name in names:
        target = root / name
        if target.is_file():
            found.append(target)
    return tuple(found)


def _entry_script_paths(root: Path) -> tuple[Path, ...]:
    candidates = (
        "server.py",
        "main.py",
        "mcp_server.py",
        "index.js",
        "server.js",
        "main.js",
        "bin/server.js",
        "dist/index.js",
    )
    found: list[Path] = []
    for rel in candidates:
        path = root / rel
        if path.is_file():
            found.append(path)
    return tuple(found)


def collect_layout(root: Path) -> RepoLayout:
    resolved = root.expanduser().resolve(strict=False)
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"layout root not a directory: {resolved}")
    file_count = 0
    total_bytes = 0
    for path in resolved.rglob("*"):
        if path.is_file():
            file_count += 1
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass
    return RepoLayout(
        root=resolved,
        readme_paths=_candidate_paths(resolved, README_CANDIDATES),
        pyproject_paths=_candidate_paths(resolved, PYPROJECT_CANDIDATES),
        npm_paths=_candidate_paths(resolved, NPM_CANDIDATES),
        docker_paths=_candidate_paths(resolved, DOCKER_CANDIDATES),
        capability_paths=_candidate_paths(resolved, CAPABILITY_FILE_CANDIDATES),
        entry_script_paths=_entry_script_paths(resolved),
        file_count=file_count,
        total_bytes=total_bytes,
    )
