from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import parsers
from xninetzy.ecosystem.scanners.hit import ScanHit
from xninetzy.ecosystem.scanners.runner import RunSpec

SEMGREP_RULESETS: dict[str, tuple[str, ...]] = {
    ".ts": ("p/typescript", "p/javascript"),
    ".tsx": ("p/typescript", "p/react"),
    ".js": ("p/javascript",),
    ".jsx": ("p/react",),
    ".py": ("p/python",),
    ".go": ("p/golang",),
    ".java": ("p/java",),
    ".rb": ("p/ruby",),
    ".php": ("p/php",),
    "Dockerfile": ("p/dockerfile",),
    "nginx.conf": ("p/nginx",),
    ".yml": ("p/docker-compose",),
    ".yaml": ("p/docker-compose",),
}
_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next"}
MAX_SCAN_ENTRIES = 20000


@dataclass(slots=True)
class Adapter:
    tool: str
    spec: RunSpec
    parse: Callable[[str], list[ScanHit]]
    output_file: str


def detect_semgrep_rulesets(root: Path) -> list[str]:
    found: set[str] = set()
    seen = 0
    for path in root.rglob("*"):
        seen += 1
        if seen > MAX_SCAN_ENTRIES:
            break
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        for key in (path.name, path.suffix.lower()):
            if key in SEMGREP_RULESETS:
                found.update(SEMGREP_RULESETS[key])
    if path_has_dockerfile(root):
        found.add("p/dockerfile")
    return sorted(found) or ["p/security-audit"]


def path_has_dockerfile(root: Path) -> bool:
    return any(root.rglob("Dockerfile*"))


def gitleaks(lock: dict[str, Any], source: Path, mode: str = "dir", timeout: int = 600) -> Adapter:
    if mode not in {"dir", "git"}:
        raise ValueError("mode gitleaks harus dir atau git")
    spec = RunSpec(
        tool="gitleaks",
        image=lock_mod.image_for(lock, "gitleaks"),
        args=[mode, "/src", "--redact", "--no-banner", "--exit-code", "0",
              "--report-format", "json", "--report-path", "/out/gitleaks.json"],
        source=source,
        network="none",
        timeout=timeout,
        ok_codes=frozenset({0, 1}),
    )
    return Adapter("gitleaks", spec, parsers.parse_gitleaks, "gitleaks.json")


def trivy(lock: dict[str, Any], source: Path, mode: str = "fs", cache_dir: Path | None = None, timeout: int = 900) -> Adapter:
    if mode not in {"fs", "config"}:
        raise ValueError("mode trivy harus fs atau config")
    scanners = ["--scanners", "vuln,secret,misconfig"] if mode == "fs" else []
    spec = RunSpec(
        tool="trivy",
        image=lock_mod.image_for(lock, "trivy"),
        args=[mode, "--quiet", "--cache-dir", "/cache", "--format", "json", "--output", "/out/trivy.json", *scanners, "/src"],
        source=source,
        network="bridge",
        timeout=timeout,
        cache_dir=cache_dir,
        ok_codes=frozenset({0}),
    )
    return Adapter("trivy", spec, parsers.parse_trivy, "trivy.json")


def osv(lock: dict[str, Any], source: Path, timeout: int = 600) -> Adapter:
    spec = RunSpec(
        tool="osv-scanner",
        image=lock_mod.image_for(lock, "osv-scanner"),
        args=["scan", "source", "-r", "--format", "json", "/src"],
        source=source,
        network="bridge",
        timeout=timeout,
        ok_codes=frozenset({0, 1}),
        capture_stdout_to="osv.json",
    )
    return Adapter("osv-scanner", spec, parsers.parse_osv, "osv.json")


def semgrep(lock: dict[str, Any], source: Path, rulesets: list[str] | None = None, timeout: int = 900) -> Adapter:
    chosen = rulesets or detect_semgrep_rulesets(source)
    config_args: list[str] = []
    for ruleset in chosen:
        config_args.extend(["--config", ruleset])
    spec = RunSpec(
        tool="semgrep",
        image=lock_mod.image_for(lock, "semgrep"),
        args=["semgrep", "scan", *config_args, "--json", "--metrics=off", "--quiet", "/src"],
        source=source,
        network="bridge",
        timeout=timeout,
        ok_codes=frozenset({0, 1}),
        capture_stdout_to="semgrep.json",
        env={"SEMGREP_SEND_METRICS": "off"},
    )
    return Adapter("semgrep", spec, parsers.parse_semgrep, "semgrep.json")


def zap(lock: dict[str, Any], target_url: str, mode: str, network: str, schema_path: str = "", timeout: int = 1800) -> Adapter:
    if mode == "baseline":
        args = ["zap-baseline.py", "-t", target_url, "-J", "zap.json", "-I"]
    elif mode == "api":
        if not schema_path:
            raise ValueError("mode api butuh schema")
        args = ["zap-api-scan.py", "-t", schema_path, "-f", "openapi", "-J", "zap.json", "-I"]
    else:
        raise ValueError("mode zap harus baseline atau api")
    spec = RunSpec(
        tool="zap",
        image=lock_mod.image_for(lock, "zap"),
        args=args,
        out_mount="/zap/wrk",
        network=network,
        timeout=timeout,
        ok_codes=frozenset({0, 1, 2}),
        tmpfs=["/home/zap:rw,exec,size=512m"],
        env={"HOME": "/home/zap"},
    )
    return Adapter("zap", spec, parsers.parse_zap, "zap.json")


def schemathesis(lock: dict[str, Any], schema_url: str, base_url: str, network: str, max_examples: int = 25, timeout: int = 900) -> Adapter:
    bounded = max(1, min(int(max_examples), 200))
    spec = RunSpec(
        tool="schemathesis",
        image=lock_mod.image_for(lock, "schemathesis"),
        args=["run", schema_url, "--base-url", base_url, "--hypothesis-max-examples", str(bounded),
              "--workers", "1", "--request-timeout", "10000", "--junit-xml", "/out/schemathesis.xml"],
        network=network,
        timeout=timeout,
        ok_codes=frozenset({0, 1}),
    )
    return Adapter("schemathesis", spec, parsers.parse_schemathesis_junit, "schemathesis.xml")


def syft(lock: dict[str, Any], source: Path, timeout: int = 600) -> RunSpec:
    return RunSpec(
        tool="syft",
        image=lock_mod.image_for(lock, "syft"),
        args=["scan", "dir:/src", "-o", "cyclonedx-json", "-q"],
        source=source,
        network="none",
        timeout=timeout,
        capture_stdout_to="sbom.cdx.json",
        env={"SYFT_CHECK_FOR_APP_UPDATE": "false"},
    )


def grype(lock: dict[str, Any], timeout: int = 600, cache_dir: Path | None = None) -> Adapter:
    spec = RunSpec(
        tool="grype",
        image=lock_mod.image_for(lock, "grype"),
        args=["sbom:/out/sbom.cdx.json", "-o", "json", "-q"],
        network="bridge",
        timeout=timeout,
        cache_dir=cache_dir,
        ok_codes=frozenset({0, 1}),
        capture_stdout_to="grype.json",
        env={"GRYPE_DB_CACHE_DIR": "/cache", "GRYPE_CHECK_FOR_APP_UPDATE": "false"},
    )
    return Adapter("grype", spec, parsers.parse_grype, "grype.json")
