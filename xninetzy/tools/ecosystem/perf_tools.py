from __future__ import annotations

import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from langchain_core.tools import tool

from xninetzy.core.config import expand_path, get_settings
from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.os.insight import postgres_review as pg
from xninetzy.os.insight import redis_review as rd
from xninetzy.os.perf import k6_run, k6_script, stats
from xninetzy.os.perf.watchdog import DEFAULT_FLOOR_BYTES, read_mem_available
from xninetzy.os.security import findings_store
from xninetzy.tools.ecosystem.security_tools import (
    _LAB_LOOPBACK_HOSTS,
    _check_scope,
    _lab_hosts,
    _matches_scope,
    _normalize_target,
    _reserve_lab_budget,
)

_EXECUTOR = subprocess.run
_POPEN = subprocess.Popen
_SAMPLER = read_mem_available
_STATS_SAMPLER = None
_WATCHDOG_INTERVAL = 2.0
_REDIS_CONNECT = socket.create_connection
_PSQL_EXECUTOR = subprocess.run
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,63}$")
_RUN_ID = re.compile(r"^run-[A-Za-z0-9\-]{1,64}$")
_DURATION = re.compile(r"^(\d+)(s|m|h)$")
_DURATION_SECONDS = {"s": 1, "m": 60, "h": 3600}
MAX_DURATION_SECONDS = 4 * 3600
PROFILE_MAX_SECONDS = 60
_PROFILE_FILE = "/tmp/xn-prof.raw"


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _error(message: str, **extra: Any) -> str:
    return _dump({"error": message, **extra})


def _perf_root() -> Path:
    return Path(expand_path(get_settings().UNTRACKED_OUTPUT_DIR)) / "perf"


def _load_run(run_id: str) -> dict[str, Any] | None:
    if not _RUN_ID.match(run_id):
        return None
    path = _perf_root() / "runs" / f"{run_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _lab_scope(scope_token: str, sender_id: str, need_active: bool) -> tuple[dict[str, Any] | None, str | None]:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return None, _error(reason, scope_token=scope_token)
    if record.get("kind") != "owner_lab":
        return None, _error("tool ini butuh scope owner_lab", scope_token=scope_token)
    if need_active and (record.get("lab") or {}).get("profile") != "active":
        return None, _error("tool ini butuh scope owner_lab dengan profile active", scope_token=scope_token)
    return record, None


def _lab_host_allowed(record: dict[str, Any], host: str) -> bool:
    if host not in _LAB_LOOPBACK_HOSTS:
        return False
    return any((urlparse(t).hostname or "") == host for t in _lab_hosts(record))


@tool(description="Tulis skeleton skrip k6 dari daftar operasi (GraphQL atau REST) atau OpenAPI: tag per operasi, think time, jadwal ramp/hold/down, threshold SLO (default p95<500ms, p99<1.5s, error<1%).")
def perf_plan(
    name: str,
    base_url: str,
    operations: list[dict[str, Any]] | None = None,
    openapi_source: str = "",
    slo: dict[str, float] | None = None,
    vus: int = 100,
    ramp: str = "30s",
    hold: str = "2m",
    down: str = "30s",
    think_min: float = 0.5,
    think_max: float = 1.5,
) -> str:
    if not _NAME.match(name):
        return _error("name tidak valid")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return _error("base_url harus http(s)")
    ops = operations or []
    if not ops and openapi_source.strip():
        try:
            spec = yaml.safe_load(openapi_source)
        except yaml.YAMLError:
            return _error("openapi_source tidak dapat di-parse")
        ops = k6_script.derive_operations_from_openapi(spec if isinstance(spec, dict) else {})
    try:
        script = k6_script.render_k6_script(base_url, ops, slo, vus, ramp, hold, down, think_min, think_max)
    except (k6_script.PlanError, KeyError, TypeError, ValueError) as exc:
        return _error(f"rencana tidak valid: {exc}")
    target = _perf_root() / "scripts"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{name}.js"
    path.write_text(script, encoding="utf-8")
    return _dump({"script_path": str(path), "operations": len(ops), "vus": vus, "slo": {**k6_script.DEFAULT_SLO, **(slo or {})}, "bytes": len(script)})


@tool(description="Jalankan k6 di Docker terpin (host network, batas memori) di bawah scope owner_lab active dengan watchdog MemAvailable (floor default 1.5 GiB, minimum 512 MiB) dan sampel docker stats; hasil selalu berlabel same-host.")
def perf_run_k6(
    scope_token: str,
    script_path: str,
    base_url: str,
    vus: int,
    duration: str,
    database_name: str,
    allow_demo_db: bool = False,
    mem_limit: str = k6_run.DEFAULT_MEM_LIMIT,
    floor_mib: int = DEFAULT_FLOOR_BYTES // (1024 * 1024),
    replicas: int = 1,
    containers: list[str] | None = None,
    sender_id: str = "",
) -> str:
    record, error = _lab_scope(scope_token, sender_id, True)
    if error:
        return error
    if not _matches_scope(record, base_url):
        return _error("target tidak termasuk scope")
    try:
        canonical, _host, _port = _normalize_target(base_url, _lab_hosts(record))
    except ValueError as exc:
        return _error(str(exc))
    if not database_name.strip():
        return _error("database_name wajib diisi")
    if not database_name.endswith("_test") and not allow_demo_db:
        return _error("database_name harus berakhiran _test; allow_demo_db=true hanya untuk skenario read-only")
    scripts_dir = (_perf_root() / "scripts").resolve()
    script = Path(script_path).expanduser().resolve()
    if not script.is_file() or not script.is_relative_to(scripts_dir):
        return _error("script harus berada di folder perf/scripts hasil perf_plan")
    if not 1 <= int(vus) <= k6_run.MAX_VUS:
        return _error(f"vus harus 1..{k6_run.MAX_VUS}")
    match = _DURATION.match(duration)
    if not match:
        return _error("duration harus berformat 30s, 5m atau 1h")
    seconds = int(match.group(1)) * _DURATION_SECONDS[match.group(2)]
    if not 1 <= seconds <= MAX_DURATION_SECONDS:
        return _error(f"duration harus 1..{MAX_DURATION_SECONDS} detik")
    if not re.fullmatch(r"\d+[mMgG]", mem_limit):
        return _error("mem_limit tidak valid")
    lock = lock_mod.load_lock()
    if runner.docker_binary() is None:
        return _dump({"status": runner.STATUS_MISSING, "detail": "docker tidak ditemukan"})
    present, _info = runner.image_present(lock_mod.image_for(lock, "k6"), _EXECUTOR)
    if not present:
        return _dump({"status": runner.STATUS_MISSING, "detail": f"image {lock_mod.image_for(lock, 'k6')} tidak tersedia lokal; jalankan: docker pull {lock['tools']['k6']['image']}"})
    estimate = int(vus) * seconds
    if not _reserve_lab_budget(scope_token, estimate):
        return _error("lab scope: request budget tidak cukup untuk run ini", estimated_requests=estimate)
    run_id = k6_run.new_run_id()
    name = f"xn-k6-{run_id}"
    spec = k6_run.build_spec(lock, script, canonical, int(vus), duration, mem_limit, name)
    run_dir = _perf_root() / "runs" / run_id
    result = k6_run.execute(
        spec, run_dir, int(floor_mib) * 1024 * 1024, [name, *(containers or [])],
        popen=_POPEN, executor=_EXECUTOR, sampler=_SAMPLER, interval=_WATCHDOG_INTERVAL, stats_sampler=_STATS_SAMPLER,
    )
    record_payload: dict[str, Any] = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope_token": scope_token,
        "base_url": canonical,
        "script": str(script),
        "vus": int(vus),
        "duration": duration,
        "replicas": max(1, int(replicas)),
        "database_name": database_name,
        "same_host": True,
        "label": "same-host",
        **result,
    }
    runs_dir = _perf_root() / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / f"{run_id}.json").write_text(json.dumps(record_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    findings_store.record_run(scope_token, "k6", canonical, str(result.get("status")), 0, {"run_id": run_id, "vus": int(vus)})
    return _dump(record_payload)


@tool(description="Profil sampling: python (py-spy raw di container, butuh scope owner_lab active) atau file .cpuprofile (Bun/Node --cpu-prof) di folder output; mengembalikan frame dengan self-time terbesar.")
def perf_profile(
    scope_token: str,
    runtime: str = "python",
    service: str = "",
    seconds: int = 10,
    profile_path: str = "",
    top: int = 15,
    sender_id: str = "",
) -> str:
    bounded_top = max(1, min(int(top), 50))
    if runtime == "cpuprofile":
        _record, error = _lab_scope(scope_token, sender_id, False)
        if error:
            return error
        path = Path(profile_path).expanduser().resolve()
        root = Path(expand_path(get_settings().UNTRACKED_OUTPUT_DIR)).resolve()
        if not path.is_file() or not path.is_relative_to(root) or path.suffix != ".cpuprofile":
            return _error("profile_path harus file .cpuprofile di dalam folder output")
        try:
            frames = stats.top_self_time_cpuprofile(path.read_text(encoding="utf-8", errors="replace"), bounded_top)
        except (ValueError, KeyError, TypeError):
            return _error("cpuprofile tidak dapat di-parse")
        return _dump({"runtime": "cpuprofile", "top_self_time": frames})
    if runtime != "python":
        return _error("runtime harus python atau cpuprofile")
    _record, error = _lab_scope(scope_token, sender_id, True)
    if error:
        return error
    if not _NAME.match(service):
        return _error("service (nama container) tidak valid")
    if not 1 <= int(seconds) <= PROFILE_MAX_SECONDS:
        return _error(f"seconds harus 1..{PROFILE_MAX_SECONDS}")
    try:
        record_proc = _EXECUTOR(
            ["docker", "exec", service, "py-spy", "record", "-d", str(int(seconds)), "-f", "raw", "-o", _PROFILE_FILE, "--pid", "1"],
            capture_output=True, text=True, timeout=int(seconds) + 30, check=False,
        )
        if record_proc.returncode != 0:
            text = (record_proc.stderr or "").strip()[:300]
            status = "TOOL_MISSING" if "not found" in text.lower() or "executable" in text.lower() else "FAILED"
            return _dump({"status": status, "detail": text, "hint": "py-spy harus terpasang di container dan container butuh cap SYS_PTRACE"})
        raw = _EXECUTOR(["docker", "exec", service, "cat", _PROFILE_FILE], capture_output=True, text=True, timeout=30, check=False)
        _EXECUTOR(["docker", "exec", service, "rm", "-f", _PROFILE_FILE], capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return _dump({"status": "FAILED", "detail": type(exc).__name__})
    return _dump({"runtime": "python", "status": "OK", "top_self_time": stats.top_self_time_pyspy_raw(raw.stdout or "", bounded_top)})


@tool(description="Bandingkan dua run k6: throughput, p50/p95/p99 dan error rate per operasi beserta delta.")
def perf_compare(run_a: str, run_b: str) -> str:
    a, b = _load_run(run_a), _load_run(run_b)
    if a is None or b is None:
        return _error("run tidak ditemukan", missing=[r for r, v in ((run_a, a), (run_b, b)) if v is None])
    if "summary" not in a or "summary" not in b:
        return _error("salah satu run tidak punya summary (run gagal atau dihentikan)")
    return _dump({"run_a": run_a, "run_b": run_b, "same_host": bool(a.get("same_host")) or bool(b.get("same_host")),
                  **stats.compare_summaries(a["summary"], b["summary"])})


@tool(description="Hitung throughput per replika, titik saturasi (kenaikan < 10% atau p95 di atas SLO) dan bottleneck (API, DB, atau generator di host yang sama) dari beberapa run k6.")
def perf_capacity(runs: list[str], replicas: list[int] | None = None, slo_p95_ms: float = 500.0) -> str:
    loaded: list[dict[str, Any]] = []
    for index, run_id in enumerate(runs):
        record = _load_run(run_id)
        if record is None or "summary" not in record:
            return _error("run tidak ditemukan atau tanpa summary", run_id=run_id)
        if replicas is not None:
            if len(replicas) != len(runs):
                return _error("replicas harus sama panjang dengan runs")
            record["replicas"] = int(replicas[index])
        loaded.append(record)
    if not loaded:
        return _error("runs kosong")
    return _dump(stats.capacity_report(loaded, float(slo_p95_ms)))


@tool(description="Review Redis read-only (INFO, CONFIG GET, SCAN sample, TTL, MEMORY USAGE): TTL coverage, kebijakan eviction, pemisahan db, big key, broker Celery bersama.")
def redis_review(scope_token: str, url: str, sample_size: int = rd.DEFAULT_SAMPLE, sender_id: str = "") -> str:
    record, error = _lab_scope(scope_token, sender_id, False)
    if error:
        return error
    try:
        host, port, password, _db = rd.parse_redis_url(url)
    except ValueError as exc:
        return _error(str(exc))
    if not _lab_host_allowed(record, host):
        return _error("host redis harus loopback dan ada di target scope owner_lab", host=host)
    try:
        client = rd.RedisReadOnly(host, port, password, connect=_REDIS_CONNECT)
    except (OSError, rd.RedisError) as exc:
        return _dump({"status": "UNREACHABLE", "detail": type(exc).__name__})
    try:
        report = rd.review(client, sample_size)
    except rd.RedisError as exc:
        return _dump({"status": "FAILED", "detail": str(exc)[:200]})
    finally:
        client.close()
    findings_store.record_run(scope_token, "redis-review", f"{host}:{port}", "OK", len(report["findings"]), {})
    return _dump({"scope_token": scope_token, "target": f"{host}:{port}", "status": "OK", **report})


@tool(description="Review Postgres read-only lewat psql (transaksi read-only, statement_timeout): top 20 query pg_stat_statements, hint index dari seq scan, koneksi per aplikasi, max_connections vs anggaran pool.")
def postgres_review(scope_token: str, dsn: str, pool_budget: int = 0, sender_id: str = "") -> str:
    record, error = _lab_scope(scope_token, sender_id, False)
    if error:
        return error
    try:
        parts = pg.parse_dsn(dsn)
    except ValueError as exc:
        return _error(str(exc))
    if not _lab_host_allowed(record, parts["host"]):
        return _error("host postgres harus loopback dan ada di target scope owner_lab", host=parts["host"])
    try:
        report = pg.review(dsn, int(pool_budget), _PSQL_EXECUTOR)
    except pg.PsqlMissing:
        return _dump({"status": "TOOL_MISSING", "detail": "psql tidak ditemukan"})
    except (pg.PsqlError, ValueError, IndexError) as exc:
        return _dump({"status": "FAILED", "detail": str(exc)[:300]})
    findings_store.record_run(scope_token, "postgres-review", f"{parts['host']}:{parts['port']}", "OK", len(report["findings"]), {})
    return _dump({"scope_token": scope_token, "target": f"{parts['host']}:{parts['port']}", "status": "OK", **report})
