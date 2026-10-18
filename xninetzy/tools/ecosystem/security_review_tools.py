from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml
from langchain_core.tools import tool

from xninetzy.core.config import expand_path, get_settings
from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.ecosystem.scanners.runner import RunSpec
from xninetzy.os.perf import scaling
from xninetzy.os.security import authz, findings_store, infra_review
from xninetzy.tools.ecosystem.security_tools import (
    _check_scope,
    _file_scope_targets,
    _resolve_repo_root,
    _root_in_file_scope,
)

_EXECUTOR = subprocess.run
MAX_MATRIX_ROWS = 2000
MAX_FILE_BYTES = 2_000_000
MAX_GUARD_PATTERN = 300
_SELF_ALIASES = frozenset({"", "self", "repo", "."})


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _error(message: str, **extra: Any) -> str:
    return _dump({"error": message, **extra})


def _file_scope(scope_token: str, sender_id: str, tool_name: str) -> tuple[list[str] | None, str | None]:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return None, _error(reason, scope_token=scope_token)
    targets = _file_scope_targets(record)
    if not targets:
        return None, _error(f"scope tidak berisi target file:; {tool_name} butuh file-scope", scope_token=scope_token)
    return targets, None


def _scoped_directory(root: str, targets: list[str]) -> tuple[Path | None, str | None]:
    if root.strip() in _SELF_ALIASES:
        path = _resolve_repo_root(root)
    else:
        path = Path(root).expanduser()
        if not path.is_absolute() or not path.is_dir():
            return None, _error("root harus direktori absolut yang ada", root=root)
    if not _root_in_file_scope(path, targets):
        return None, _error("root di luar scope file target", repo_root=str(path.resolve()), allowed=targets)
    return path.resolve(), None


def _scoped_file(path_text: str, targets: list[str]) -> tuple[Path | None, str | None]:
    path = Path(path_text).expanduser()
    if not path.is_absolute() or not path.is_file():
        return None, _error("path harus file absolut yang ada", path=path_text)
    if not _root_in_file_scope(path, targets):
        return None, _error("path di luar scope file target", path=str(path.resolve()), allowed=targets)
    if path.stat().st_size > MAX_FILE_BYTES:
        return None, _error("file terlalu besar", limit=MAX_FILE_BYTES)
    return path.resolve(), None


def _summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in findings:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    return counts


@tool(description="Bangun matriks role x operasi x kepemilikan dari SDL GraphQL atau OpenAPI dan hasilkan skeleton tes (bun atau pytest); menolak bila project tidak mendeklarasikan guard database tes.")
def security_authz_matrix(
    scope_token: str,
    project_root: str,
    schema_path: str = "",
    schema_text: str = "",
    roles: list[str] | None = None,
    operations: list[str] | None = None,
    framework: str = "bun",
    target: str = "test",
    guard_pattern: str = authz.DEFAULT_GUARD_PATTERN,
    sender_id: str = "",
) -> str:
    targets, error = _file_scope(scope_token, sender_id, "security_authz_matrix")
    if error:
        return error
    if target != "test":
        return _error("target harus test; matriks tidak pernah dijalankan terhadap database non-test")
    if framework not in {"bun", "pytest"}:
        return _error("framework harus bun atau pytest")
    if not roles:
        return _error("roles wajib diisi")
    root, error = _scoped_directory(project_root, targets)
    if error:
        return error
    if len(guard_pattern) > MAX_GUARD_PATTERN:
        return _error("guard_pattern terlalu panjang", limit=MAX_GUARD_PATTERN)
    try:
        re.compile(guard_pattern)
    except re.error:
        return _error("guard_pattern bukan regex valid")
    guards = authz.find_test_db_guard(root, guard_pattern)
    if not guards:
        return _error("project tidak mendeklarasikan test database guard", expected_pattern=guard_pattern)
    if schema_path:
        schema_file, error = _scoped_file(schema_path, targets)
        if error:
            return error
        schema_text = schema_file.read_text(encoding="utf-8", errors="replace")
    if not schema_text.strip():
        return _error("schema_path atau schema_text wajib diisi")
    stripped = schema_text.lstrip()
    if stripped.startswith("{") or stripped.startswith("openapi") or stripped.startswith("swagger"):
        try:
            spec = json.loads(schema_text) if stripped.startswith("{") else yaml.safe_load(schema_text)
        except (ValueError, yaml.YAMLError):
            return _error("schema OpenAPI tidak dapat di-parse")
        parsed = authz.parse_openapi(spec if isinstance(spec, dict) else {})
    else:
        parsed = authz.parse_sdl(schema_text)
    if not parsed:
        return _error("tidak ada operasi yang ditemukan di schema")
    rows = authz.build_matrix(parsed, [r.strip() for r in roles if r.strip()], operations)
    if not rows:
        return _error("tidak ada operasi yang cocok dengan filter")
    truncated = len(rows) > MAX_MATRIX_ROWS
    rows = rows[:MAX_MATRIX_ROWS]
    skeleton = authz.render_bun_skeleton(rows) if framework == "bun" else authz.render_pytest_skeleton(rows)
    return _dump({
        "scope_token": scope_token,
        "framework": framework,
        "test_database_guard": guards,
        "operation_count": len({r["operation"] for r in rows}),
        "row_count": len(rows),
        "truncated": truncated,
        "sensitive_operations": sorted({r["operation"] for r in rows if r["sensitive"]}),
        "matrix": rows,
        "skeleton": skeleton,
    })


@tool(description="Daftar semua jalur kode yang menulis field role/capability/privilege beserta guard tiap jalur; tandai jalur yang lebih lemah dari jalur lain.")
def security_role_paths(scope_token: str, root: str = "self", include_tests: bool = False, sender_id: str = "") -> str:
    targets, error = _file_scope(scope_token, sender_id, "security_role_paths")
    if error:
        return error
    base, error = _scoped_directory(root, targets)
    if error:
        return error
    paths = authz.scan_role_paths(base, include_tests)
    weaker = [p for p in paths if p["status"] in {"weaker", "unguarded"}]
    findings_store.record_run(scope_token, "role-paths", str(base), "OK", len(weaker), {"paths": len(paths)})
    return _dump({
        "scope_token": scope_token,
        "root": str(base),
        "path_count": len(paths),
        "flagged_count": len(weaker),
        "paths": paths,
    })


def _load_compose(path: Path, run_config: bool) -> tuple[dict[str, Any] | None, str]:
    if run_config and runner.docker_binary():
        try:
            proc = _EXECUTOR(
                [runner.docker_binary(), "compose", "-f", str(path), "config", "--no-interpolate", "--format", "json"],
                capture_output=True, text=True, timeout=60, check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return json.loads(proc.stdout), "docker compose config"
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except yaml.YAMLError:
        return None, "yaml"
    return (data if isinstance(data, dict) else None), "yaml"


@tool(description="Review file docker compose: port data store di 0.0.0.0, Redis tanpa requirepass, container root/privileged, mount docker.sock, mem_limit untuk profil load-test.")
def security_compose_review(scope_token: str, path: str, load_test: bool = False, run_config: bool = False, sender_id: str = "") -> str:
    targets, error = _file_scope(scope_token, sender_id, "security_compose_review")
    if error:
        return error
    file, error = _scoped_file(path, targets)
    if error:
        return error
    data, source = _load_compose(file, run_config)
    if data is None:
        return _error("compose tidak dapat di-parse", path=str(file))
    findings = infra_review.review_compose(data, load_test)
    findings_store.record_run(scope_token, "compose-review", str(file), "OK", len(findings), {"source": source})
    return _dump({"scope_token": scope_token, "path": str(file), "parsed_with": source, "finding_count": len(findings),
                  "by_severity": _summary(findings), "findings": findings})


def _nginx_test(file: Path, session: Path) -> dict[str, Any]:
    lock = lock_mod.load_lock()
    spec = RunSpec(
        tool="nginx",
        image=lock_mod.image_for(lock, "nginx"),
        args=["-t", "-c", "/etc/nginx/nginx.conf"],
        entrypoint="nginx",
        network="none",
        timeout=60,
        tmpfs=["/var/cache/nginx:rw,size=16m", "/run:rw,size=4m"],
        extra_mounts=[(str(file), "/etc/nginx/nginx.conf", "ro")],
    )
    result = runner.run(spec, session, executor=_EXECUTOR)
    text = (result.stderr or result.stdout or result.detail).strip()
    return {"status": result.status, "returncode": result.returncode, "output": text[:800]}


@tool(description="Review konfigurasi nginx: server_tokens, header keamanan, penanganan X-Forwarded-For, limit_req, client_max_body_size, resolusi upstream, Connection upgrade, lokasi /docs /openapi.json /metrics publik; run_test menjalankan nginx -t di container terpin.")
def security_nginx_review(scope_token: str, path: str, run_test: bool = False, sender_id: str = "") -> str:
    targets, error = _file_scope(scope_token, sender_id, "security_nginx_review")
    if error:
        return error
    file, error = _scoped_file(path, targets)
    if error:
        return error
    findings = infra_review.review_nginx(file.read_text(encoding="utf-8", errors="replace"))
    payload: dict[str, Any] = {"scope_token": scope_token, "path": str(file), "finding_count": len(findings),
                               "by_severity": _summary(findings), "findings": findings}
    if run_test:
        session = Path(expand_path(get_settings().UNTRACKED_OUTPUT_DIR)) / "security" / scope_token / "nginx-test"
        payload["nginx_test"] = _nginx_test(file, session)
    findings_store.record_run(scope_token, "nginx-review", str(file), "OK", len(findings), {"run_test": run_test})
    return _dump(payload)


@tool(description="Cek risiko menjalankan N replika: event bus in-process, cron tanpa leader election, cache modul, tulis file lokal, state di memori, Celery beat, upstream nginx, dan anggaran koneksi DB (replicas x pool vs max_connections); keluaran berupa checklist dengan file:baris.")
def scaling_review(
    scope_token: str,
    root: str = "self",
    replicas: int = 0,
    pool_size: int = 0,
    max_connections: int = 0,
    other_connections: int = 0,
    include_tests: bool = False,
    sender_id: str = "",
) -> str:
    targets, error = _file_scope(scope_token, sender_id, "scaling_review")
    if error:
        return error
    base, error = _scoped_directory(root, targets)
    if error:
        return error
    result = scaling.scan_repo(base, replicas, pool_size, max_connections, other_connections, include_tests)
    findings_store.record_run(scope_token, "scaling-review", str(base), "OK", len(result["findings"]), {})
    return _dump({"scope_token": scope_token, "root": str(base), "finding_count": len(result["findings"]),
                  "by_severity": _summary(result["findings"]), **result})
