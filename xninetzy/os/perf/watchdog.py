from __future__ import annotations

import subprocess
import threading
from typing import Callable

MIN_FLOOR_BYTES = 512 * 1024 * 1024
DEFAULT_FLOOR_BYTES = int(1.5 * 1024 * 1024 * 1024)
DEFAULT_INTERVAL_SECONDS = 2.0


def read_mem_available(path: str = "/proc/meminfo") -> int:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("MemAvailable tidak ditemukan")


def effective_floor(requested: int | None) -> int:
    return max(int(requested or DEFAULT_FLOOR_BYTES), MIN_FLOOR_BYTES)


def parse_docker_stats(text: str) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for line in text.splitlines():
        parts = line.strip().split(",")
        if len(parts) < 3:
            continue
        name, cpu, mem = parts[0], parts[1].rstrip("%"), parts[2]
        try:
            cpu_value = float(cpu)
        except ValueError:
            continue
        rows.append({"name": name, "cpu_pct": cpu_value, "mem_mb": _mem_mb(mem)})
    return rows


def _mem_mb(usage: str) -> float:
    used = usage.split("/", 1)[0].strip()
    number = "".join(ch for ch in used if ch.isdigit() or ch == ".")
    unit = used[len(number):].strip().lower()
    scale = {"b": 1 / 1024 ** 2, "kib": 1 / 1024, "kb": 1 / 1000, "mib": 1.0, "mb": 1.0, "gib": 1024.0, "gb": 1000.0}.get(unit, 1.0)
    try:
        return round(float(number) * scale, 2)
    except ValueError:
        return 0.0


def docker_stats_sampler(names: list[str], executor: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> Callable[[], list[dict[str, float | str]]]:
    def sample() -> list[dict[str, float | str]]:
        proc = executor(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}", *names],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return parse_docker_stats(proc.stdout or "") if proc.returncode == 0 else []
    return sample


class Watchdog:
    def __init__(
        self,
        floor_bytes: int | None,
        stop: Callable[[], None],
        interval: float = DEFAULT_INTERVAL_SECONDS,
        sampler: Callable[[], int] = read_mem_available,
        stats_sampler: Callable[[], list[dict[str, float | str]]] | None = None,
    ) -> None:
        self.floor = effective_floor(floor_bytes)
        self.interval = interval
        self._stop_action = stop
        self._sampler = sampler
        self._stats_sampler = stats_sampler
        self._halt = threading.Event()
        self._thread: threading.Thread | None = None
        self.triggered = False
        self.reason = ""
        self.min_available = 0
        self.samples = 0
        self.stats: list[dict[str, float | str]] = []

    def _loop(self) -> None:
        tick = 0
        while not self._halt.is_set():
            try:
                available = self._sampler()
            except (OSError, RuntimeError) as exc:
                self.triggered = True
                self.reason = f"sampler gagal: {type(exc).__name__}"
                self._stop_action()
                return
            self.samples += 1
            self.min_available = available if self.samples == 1 else min(self.min_available, available)
            if available < self.floor:
                self.triggered = True
                self.reason = f"MemAvailable {available // 1024 ** 2} MiB di bawah floor {self.floor // 1024 ** 2} MiB"
                self._stop_action()
                return
            if self._stats_sampler is not None:
                try:
                    for row in self._stats_sampler():
                        self.stats.append({"t": tick, **row})
                except (OSError, subprocess.SubprocessError):
                    pass
            tick += 1
            self._halt.wait(self.interval)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def finish(self) -> None:
        self._halt.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def report(self) -> dict[str, object]:
        return {
            "triggered": self.triggered,
            "reason": self.reason,
            "floor_mib": self.floor // 1024 ** 2,
            "min_available_mib": self.min_available // 1024 ** 2,
            "samples": self.samples,
        }
