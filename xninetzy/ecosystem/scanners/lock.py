from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xninetzy.ecosystem.scanners import runner

LOCK_FILENAME = "security-tools.lock"
LOCK_VERSION = 1
READY = "READY"
DEGRADED = "DEGRADED"
MISSING = "MISSING"
UNHEALTHY = "UNHEALTHY"

DEFAULT_TOOLS: dict[str, dict[str, Any]] = {
    "gitleaks": {"image": "zricethezav/gitleaks:v8.30.1", "capability": "secrets", "digest": "", "version": "8.30.1", "db_updated": ""},
    "trivy": {"image": "aquasec/trivy:0.74.0", "capability": "vulnerabilities+config+secrets", "digest": "", "version": "0.74.0", "db_updated": ""},
    "osv-scanner": {"image": "ghcr.io/google/osv-scanner:v2.6.0", "capability": "dependencies", "digest": "", "version": "2.6.0", "db_updated": ""},
    "semgrep": {"image": "semgrep/semgrep:1.177.0", "capability": "sast", "digest": "", "version": "1.177.0", "db_updated": ""},
    "zap": {"image": "ghcr.io/zaproxy/zaproxy:2.17.0", "capability": "dast", "digest": "", "version": "2.17.0", "db_updated": ""},
    "schemathesis": {"image": "schemathesis/schemathesis:stable", "capability": "api-fuzz", "digest": "", "version": "stable", "db_updated": ""},
    "syft": {"image": "anchore/syft:latest", "capability": "sbom", "digest": "", "version": "latest", "db_updated": ""},
    "grype": {"image": "anchore/grype:latest", "capability": "sbom-vulnerabilities", "digest": "", "version": "latest", "db_updated": ""},
    "k6": {"image": "grafana/k6:1.3.0", "capability": "load-test", "digest": "", "version": "1.3.0", "db_updated": ""},
    "nginx": {"image": "nginx:1.27-alpine", "capability": "nginx-config-test", "digest": "", "version": "1.27", "db_updated": ""},
}


@dataclass(slots=True)
class ToolHealth:
    tool: str
    capability: str
    status: str
    image: str
    version: str
    digest: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "tool": self.tool,
            "capability": self.capability,
            "status": self.status,
            "image": self.image,
            "version": self.version,
            "digest": self.digest,
            "detail": self.detail,
        }


def default_lock_path() -> Path:
    return Path(__file__).resolve().parents[3] / LOCK_FILENAME


def default_lock() -> dict[str, Any]:
    return {"version": LOCK_VERSION, "tools": json.loads(json.dumps(DEFAULT_TOOLS))}


def load_lock(path: Path | None = None) -> dict[str, Any]:
    target = path or default_lock_path()
    if not target.exists():
        return default_lock()
    data = json.loads(target.read_text(encoding="utf-8"))
    merged = default_lock()
    for name, entry in (data.get("tools") or {}).items():
        merged["tools"][name] = {**merged["tools"].get(name, {}), **entry}
    return merged


def save_lock(lock: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_lock_path()
    target.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def image_for(lock: dict[str, Any], tool: str) -> str:
    entry = lock["tools"][tool]
    return runner.image_reference(entry["image"], entry.get("digest", ""))


def _local_digests(raw: str) -> list[str]:
    try:
        return [d.split("@", 1)[1] for d in json.loads(raw) if "@" in d]
    except (ValueError, TypeError):
        return []


def check_tool(tool: str, entry: dict[str, Any], executor: runner.Executor = subprocess.run) -> ToolHealth:
    image = entry["image"]
    pinned = str(entry.get("digest") or "")
    base = dict(tool=tool, capability=str(entry.get("capability") or ""), image=image, version=str(entry.get("version") or ""), digest=pinned)
    if runner.docker_binary() is None:
        return ToolHealth(status=UNHEALTHY, detail="docker tidak ditemukan", **base)
    try:
        info = executor([runner.docker_binary(), "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return ToolHealth(status=UNHEALTHY, detail=f"docker tidak dapat dijalankan: {type(exc).__name__}", **base)
    if info.returncode != 0:
        return ToolHealth(status=UNHEALTHY, detail="docker daemon tidak dapat dijangkau", **base)
    present, raw = runner.image_present(image, executor)
    if not present:
        return ToolHealth(status=MISSING, detail=f"docker pull {image}", **base)
    local = _local_digests(raw)
    if not pinned:
        return ToolHealth(status=DEGRADED, detail="digest belum dipin di security-tools.lock", **base)
    if local and pinned not in local:
        return ToolHealth(status=DEGRADED, detail="digest lokal berbeda dari lock", **base)
    return ToolHealth(status=READY, detail="ok", **base)


def check_all(lock: dict[str, Any] | None = None, executor: runner.Executor = subprocess.run) -> list[ToolHealth]:
    active = lock or load_lock()
    return [check_tool(name, entry, executor) for name, entry in sorted(active["tools"].items())]


def pin_from_local(lock: dict[str, Any], executor: runner.Executor = subprocess.run) -> dict[str, str]:
    pinned: dict[str, str] = {}
    for name, entry in lock["tools"].items():
        present, raw = runner.image_present(entry["image"], executor)
        if not present:
            continue
        digests = _local_digests(raw)
        if digests:
            entry["digest"] = digests[0]
            pinned[name] = digests[0]
    return pinned
