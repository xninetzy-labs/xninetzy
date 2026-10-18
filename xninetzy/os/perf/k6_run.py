from __future__ import annotations

import csv
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.ecosystem.scanners.runner import RunSpec
from xninetzy.os.perf import stats, watchdog

STATUS_OK = "OK"
STATUS_THRESHOLDS = "THRESHOLDS_FAILED"
STATUS_WATCHDOG = "WATCHDOG_STOPPED"
K6_OK_CODES = frozenset({0, 99})
MAX_VUS = 20000
DEFAULT_MEM_LIMIT = "2g"


def new_run_id() -> str:
    return "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]


def build_spec(lock: dict[str, Any], script: Path, base_url: str, vus: int, duration: str, mem_limit: str, name: str) -> RunSpec:
    return RunSpec(
        tool="k6",
        image=lock_mod.image_for(lock, "k6"),
        args=["run", "--vus", str(vus), "--duration", duration, "--summary-export", "/out/summary.json", "--quiet", f"/scripts/{script.name}"],
        network="host",
        memory=mem_limit,
        pids_limit=1024,
        cpus="2.0",
        timeout=7200,
        env={"BASE_URL": base_url},
        extra_mounts=[(str(script.parent), "/scripts", "ro")],
        name=name,
    )


def write_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["t", "name", "cpu_pct", "mem_mb"])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})


def execute(
    spec: RunSpec,
    run_dir: Path,
    floor_bytes: int | None,
    stats_names: list[str],
    popen: Callable[..., Any] = subprocess.Popen,
    executor: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    sampler: Callable[[], int] = watchdog.read_mem_available,
    interval: float = watchdog.DEFAULT_INTERVAL_SECONDS,
    stats_sampler: Callable[[], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if runner.docker_binary() is None:
        return {"status": runner.STATUS_MISSING, "detail": "docker tidak ditemukan"}
    present, _info = runner.image_present(spec.image, executor)
    if not present:
        return {"status": runner.STATUS_MISSING, "detail": f"image {spec.image} tidak tersedia lokal; jalankan: docker pull {spec.image}"}
    run_dir.mkdir(parents=True, exist_ok=True)
    command = runner.build_command(spec, run_dir)

    def kill() -> None:
        executor(["docker", "kill", spec.name], capture_output=True, text=True, timeout=30, check=False)

    dog = watchdog.Watchdog(
        floor_bytes, kill, interval=interval, sampler=sampler,
        stats_sampler=stats_sampler if stats_sampler is not None else watchdog.docker_stats_sampler(stats_names, executor),
    )
    process = popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    dog.start()
    try:
        stdout, stderr = process.communicate(timeout=spec.timeout)
    except subprocess.TimeoutExpired:
        kill()
        process.kill()
        stdout, stderr = process.communicate()
        dog.finish()
        return {"status": runner.STATUS_TIMEOUT, "detail": f"melebihi {spec.timeout}s", "watchdog": dog.report()}
    dog.finish()
    stats_csv = run_dir / "docker-stats.csv"
    write_stats_csv(stats_csv, dog.stats)
    result: dict[str, Any] = {
        "returncode": process.returncode,
        "watchdog": dog.report(),
        "stats_csv": str(stats_csv),
        "stats_avg": stats.average_stats(dog.stats),
        "stderr": (stderr or "")[-2000:],
    }
    if dog.triggered:
        result.update(status=STATUS_WATCHDOG, detail=dog.reason)
        return result
    if process.returncode not in K6_OK_CODES:
        result.update(status=runner.STATUS_FAILED, detail=f"exit {process.returncode}")
        return result
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        result.update(status=runner.STATUS_FAILED, detail="summary.json tidak dibuat")
        return result
    result["summary"] = stats.parse_k6_summary(json.loads(summary_path.read_text(encoding="utf-8")))
    result["summary_path"] = str(summary_path)
    result["status"] = STATUS_THRESHOLDS if process.returncode == 99 else STATUS_OK
    return result
