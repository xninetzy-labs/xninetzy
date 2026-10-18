from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MAX_LOCKFILES = 200
MAX_LOCKFILE_BYTES = 20 * 1024 * 1024

_PRUNED_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
    ".next", ".dart_tool", "target", "vendor",
})


@dataclass(frozen=True)
class Package:
    name: str
    version: str
    ecosystem: str
    lockfile: str
    dev: bool | None = None


def _read(path: Path) -> str:
    if path.stat().st_size > MAX_LOCKFILE_BYTES:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _package_lock(path: Path, rel: str) -> list[Package]:
    data = json.loads(_read(path) or "{}")
    found: list[Package] = []
    packages = data.get("packages")
    if isinstance(packages, dict):
        for key, meta in packages.items():
            if not key or not isinstance(meta, dict):
                continue
            name = meta.get("name") or key.rsplit("node_modules/", 1)[-1]
            version = meta.get("version")
            if name and version:
                found.append(Package(name, str(version), "npm", rel, bool(meta.get("dev"))))
        return found
    def walk(deps: dict) -> None:
        for name, meta in deps.items():
            if isinstance(meta, dict) and meta.get("version"):
                found.append(Package(name, str(meta["version"]), "npm", rel, bool(meta.get("dev"))))
                if isinstance(meta.get("dependencies"), dict):
                    walk(meta["dependencies"])
    if isinstance(data.get("dependencies"), dict):
        walk(data["dependencies"])
    return found


_JSONC_LINE_COMMENT = re.compile(r"^\s*//.*$", re.MULTILINE)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
_BUN_SPEC = re.compile(r"^(@?[^@]+)@(.+)$")


def _bun_lock(path: Path, rel: str) -> list[Package]:
    text = _TRAILING_COMMA.sub(r"\1", _JSONC_LINE_COMMENT.sub("", _read(path)))
    data = json.loads(text or "{}")
    found: list[Package] = []
    for entry in (data.get("packages") or {}).values():
        if not isinstance(entry, list) or not entry or not isinstance(entry[0], str):
            continue
        match = _BUN_SPEC.match(entry[0])
        if not match:
            continue
        version = match.group(2)
        if version.startswith(("workspace:", "file:", "link:", "github:", "git")):
            continue
        found.append(Package(match.group(1), version, "npm", rel))
    return found


_PNPM_KEY = re.compile(r"""^  ['"]?/?((?:@[^/@\s'"]+/)?[^/@\s'"]+)[@/](\d[^(:'"\s]*)""")


def _pnpm_lock(path: Path, rel: str) -> list[Package]:
    found: list[Package] = []
    in_packages = False
    for line in _read(path).splitlines():
        if line and not line.startswith(" "):
            in_packages = line.startswith("packages:")
            continue
        if not in_packages:
            continue
        match = _PNPM_KEY.match(line)
        if match:
            found.append(Package(match.group(1), match.group(2), "npm", rel))
    return found


_YARN_VERSION = re.compile(r'^\s+version:?\s+"?([^"\s]+)"?\s*$')


def _yarn_name(header: str) -> str:
    spec = header.rstrip(":").split(",")[0].strip().strip('"')
    at = spec.rfind("@")
    return spec[:at] if at > 0 else spec


def _yarn_lock(path: Path, rel: str) -> list[Package]:
    found: list[Package] = []
    current = ""
    for line in _read(path).splitlines():
        if not line or line.startswith("#"):
            continue
        if not line.startswith(" ") and line.rstrip().endswith(":"):
            current = _yarn_name(line)
            continue
        match = _YARN_VERSION.match(line)
        if current and match:
            found.append(Package(current, match.group(1), "npm", rel))
            current = ""
    return found


def _toml_packages(path: Path, rel: str, ecosystem: str) -> list[Package]:
    data = tomllib.loads(_read(path) or "")
    found: list[Package] = []
    for entry in data.get("package", []):
        name, version = entry.get("name"), entry.get("version")
        if name and version:
            dev = None
            if "category" in entry:
                dev = entry["category"] == "dev"
            found.append(Package(str(name), str(version), ecosystem, rel, dev))
    return found


def _uv_lock(path: Path, rel: str) -> list[Package]:
    return _toml_packages(path, rel, "pypi")


def _poetry_lock(path: Path, rel: str) -> list[Package]:
    return _toml_packages(path, rel, "pypi")


def _cargo_lock(path: Path, rel: str) -> list[Package]:
    return _toml_packages(path, rel, "cargo")


_REQ_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._\-]*)(?:\[[^\]]*\])?\s*(?:==\s*([^\s;#]+))?")


def _requirements(path: Path, rel: str) -> list[Package]:
    found: list[Package] = []
    for raw in _read(path).splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        match = _REQ_PIN.match(line)
        if match:
            found.append(Package(match.group(1), match.group(2) or "unpinned", "pypi", rel))
    return found


_PUBSPEC_NAME = re.compile(r"^  ([A-Za-z0-9_]+):\s*$")
_PUBSPEC_VERSION = re.compile(r'^    version:\s*"?([^"\s]+)"?\s*$')


def _pubspec_lock(path: Path, rel: str) -> list[Package]:
    found: list[Package] = []
    current = ""
    for line in _read(path).splitlines():
        name = _PUBSPEC_NAME.match(line)
        if name:
            current = name.group(1)
            continue
        version = _PUBSPEC_VERSION.match(line)
        if current and version:
            found.append(Package(current, version.group(1), "pub", rel))
            current = ""
    return found


def _go_sum(path: Path, rel: str) -> list[Package]:
    seen: dict[tuple[str, str], Package] = {}
    for line in _read(path).splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[1].endswith("/go.mod"):
            continue
        seen[(parts[0], parts[1])] = Package(parts[0], parts[1], "go", rel)
    return list(seen.values())


def _composer_lock(path: Path, rel: str) -> list[Package]:
    data = json.loads(_read(path) or "{}")
    found: list[Package] = []
    for key, dev in (("packages", False), ("packages-dev", True)):
        for entry in data.get(key) or []:
            if entry.get("name") and entry.get("version"):
                found.append(Package(entry["name"], str(entry["version"]).lstrip("v"), "composer", rel, dev))
    return found


PARSERS: dict[str, Callable[[Path, str], list[Package]]] = {
    "package-lock.json": _package_lock,
    "npm-shrinkwrap.json": _package_lock,
    "bun.lock": _bun_lock,
    "pnpm-lock.yaml": _pnpm_lock,
    "yarn.lock": _yarn_lock,
    "uv.lock": _uv_lock,
    "poetry.lock": _poetry_lock,
    "Cargo.lock": _cargo_lock,
    "pubspec.lock": _pubspec_lock,
    "go.sum": _go_sum,
    "composer.lock": _composer_lock,
}


def _parser_for(name: str) -> Callable[[Path, str], list[Package]] | None:
    if name in PARSERS:
        return PARSERS[name]
    if re.fullmatch(r"requirements[\w.\-]*\.txt", name):
        return _requirements
    return None


def _git_listed(root: Path) -> list[Path] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [root / rel for rel in proc.stdout.decode("utf-8", errors="replace").split("\0") if rel]


def discover(root: Path) -> list[Path]:
    candidates = _git_listed(root)
    if candidates is None:
        candidates = []
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in _PRUNED_DIRS]
            candidates.extend(Path(current) / name for name in files)
    found = [
        path for path in candidates
        if _parser_for(path.name) is not None and path.is_file()
        and not any(part in _PRUNED_DIRS for part in path.relative_to(root).parts[:-1])
    ]
    return sorted(found)[:MAX_LOCKFILES]


def parse_lockfile(path: Path, root: Path) -> list[Package]:
    parser = _parser_for(path.name)
    if parser is None:
        return []
    return parser(path, str(path.relative_to(root)))


def manifest_dependencies(path: Path) -> list[dict[str, str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    entries: list[str] = list((data.get("project") or {}).get("dependencies") or [])
    poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
    entries.extend(f"{name}{'' if isinstance(spec, dict) else '=='+str(spec)}" for name, spec in poetry.items() if name.lower() != "python")
    out: list[dict[str, str]] = []
    for entry in entries:
        name = re.split(r"[<>=!~;\[ ]", entry, maxsplit=1)[0].strip()
        if name:
            out.append({"name": name, "version_hint": entry[:80], "source": "pyproject.toml"})
    return out
