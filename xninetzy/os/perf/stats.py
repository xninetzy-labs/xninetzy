from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

_TAGGED = re.compile(r"^(?P<metric>[a-z_]+)\{op:(?P<op>[^}]+)\}$")
_CATEGORIES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("generator", re.compile(r"k6|loadgen|locust|vegeta", re.IGNORECASE)),
    ("database", re.compile(r"postgres|pgbouncer|mysql|mariadb|mongo|(?:^|[-_])db(?:$|[-_])", re.IGNORECASE)),
    ("cache", re.compile(r"redis|memcache|valkey", re.IGNORECASE)),
    ("proxy", re.compile(r"nginx|traefik|caddy|haproxy", re.IGNORECASE)),
    ("api", re.compile(r"api|server|app|backend|web|service", re.IGNORECASE)),
)
_BOTTLENECK_LABEL = {
    "api": "API CPU",
    "database": "DB CPU",
    "generator": "generator CPU on the same host",
    "cache": "Redis CPU",
    "proxy": "proxy CPU",
    "other": "other containers CPU",
}
SATURATION_GAIN = 0.10


def _trend(metric: dict[str, Any]) -> dict[str, float]:
    return {
        "avg": float(metric.get("avg", 0.0)),
        "p50": float(metric.get("med", 0.0)),
        "p90": float(metric.get("p(90)", 0.0)),
        "p95": float(metric.get("p(95)", 0.0)),
        "p99": float(metric.get("p(99)", 0.0)),
        "max": float(metric.get("max", 0.0)),
    }


def _failed_rate(metric: dict[str, Any]) -> float:
    if "value" in metric:
        return float(metric["value"])
    if "rate" in metric:
        return float(metric["rate"])
    passes, fails = metric.get("passes"), metric.get("fails")
    if passes is not None and fails is not None and (passes + fails) > 0:
        return float(passes) / float(passes + fails)
    return 0.0


def parse_k6_summary(data: dict[str, Any]) -> dict[str, Any]:
    metrics = data.get("metrics") or {}
    reqs = metrics.get("http_reqs") or {}
    overall = {
        "requests": int(reqs.get("count", 0)),
        "rps": float(reqs.get("rate", 0.0)),
        "error_rate": _failed_rate(metrics.get("http_req_failed") or {}),
        **_trend(metrics.get("http_req_duration") or {}),
    }
    operations: dict[str, dict[str, float]] = defaultdict(dict)
    for key, metric in metrics.items():
        match = _TAGGED.match(key)
        if not match:
            continue
        op, name = match.group("op"), match.group("metric")
        if name == "http_req_duration":
            operations[op].update(_trend(metric))
        elif name == "http_reqs":
            operations[op]["requests"] = int(metric.get("count", 0))
            operations[op]["rps"] = float(metric.get("rate", 0.0))
        elif name == "http_req_failed":
            operations[op]["error_rate"] = _failed_rate(metric)
    return {"overall": overall, "operations": {k: dict(v) for k, v in sorted(operations.items())}}


def _delta(a: float, b: float) -> dict[str, float | None]:
    change = b - a
    return {"a": round(a, 4), "b": round(b, 4), "delta": round(change, 4), "delta_pct": round(change / a * 100, 2) if a else None}


def compare_summaries(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    metrics = ("rps", "p50", "p95", "p99", "error_rate")
    overall = {m: _delta(float(a["overall"].get(m, 0.0)), float(b["overall"].get(m, 0.0))) for m in metrics}
    names = sorted(set(a["operations"]) | set(b["operations"]))
    operations = {
        name: {m: _delta(float(a["operations"].get(name, {}).get(m, 0.0)), float(b["operations"].get(name, {}).get(m, 0.0))) for m in metrics}
        for name in names
    }
    return {"overall": overall, "operations": operations, "only_in_a": sorted(set(a["operations"]) - set(b["operations"])),
            "only_in_b": sorted(set(b["operations"]) - set(a["operations"]))}


def categorize(container: str) -> str:
    for category, pattern in _CATEGORIES:
        if pattern.search(container):
            return category
    return "other"


def average_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["name"])].append(row)
    return {
        name: {
            "cpu_pct": round(sum(float(r["cpu_pct"]) for r in items) / len(items), 2),
            "mem_mb": round(sum(float(r["mem_mb"]) for r in items) / len(items), 2),
            "samples": len(items),
        }
        for name, items in sorted(grouped.items())
    }


def capacity_report(runs: list[dict[str, Any]], slo_p95_ms: float = 500.0) -> dict[str, Any]:
    if not runs:
        raise ValueError("runs kosong")
    ordered = sorted(runs, key=lambda r: (int(r.get("replicas") or 1), float(r["summary"]["overall"].get("rps", 0.0))))
    per_run: list[dict[str, Any]] = []
    base_per_replica = 0.0
    for index, run in enumerate(ordered):
        overall = run["summary"]["overall"]
        replicas = max(1, int(run.get("replicas") or 1))
        rps = float(overall.get("rps", 0.0))
        per_replica = rps / replicas
        if index == 0:
            base_per_replica = per_replica
        per_run.append({
            "run_id": run.get("run_id", ""),
            "replicas": replicas,
            "vus": run.get("vus"),
            "rps": round(rps, 2),
            "rps_per_replica": round(per_replica, 2),
            "efficiency": round(per_replica / base_per_replica, 2) if base_per_replica else None,
            "p95_ms": round(float(overall.get("p95", 0.0)), 2),
            "error_rate": round(float(overall.get("error_rate", 0.0)), 4),
            "same_host": bool(run.get("same_host", True)),
        })
    saturation: dict[str, Any] = {"reached": False, "at_replicas": None, "reason": ""}
    for previous, current in zip(per_run, per_run[1:]):
        gain = (current["rps"] - previous["rps"]) / previous["rps"] if previous["rps"] else 0.0
        if current["p95_ms"] > slo_p95_ms:
            saturation = {"reached": True, "at_replicas": current["replicas"], "reason": f"p95 {current['p95_ms']} ms above SLO {slo_p95_ms:g} ms"}
            break
        if current["replicas"] > previous["replicas"] and gain < SATURATION_GAIN:
            saturation = {"reached": True, "at_replicas": current["replicas"], "reason": f"throughput gain {gain:.0%} below {SATURATION_GAIN:.0%}"}
            break
    last = ordered[-1]
    cpu_by_category: dict[str, float] = defaultdict(float)
    for name, values in (last.get("stats_avg") or {}).items():
        cpu_by_category[categorize(name)] += float(values.get("cpu_pct", 0.0))
    notes: list[str] = []
    bottleneck = "unknown"
    if cpu_by_category:
        top = max(cpu_by_category, key=lambda c: cpu_by_category[c])
        bottleneck = _BOTTLENECK_LABEL[top]
        generator = cpu_by_category.get("generator", 0.0)
        if generator and generator >= 0.8 * cpu_by_category[top]:
            bottleneck = _BOTTLENECK_LABEL["generator"]
    else:
        notes.append("no docker stats recorded; bottleneck cannot be named")
    if any(r["same_host"] for r in per_run):
        notes.append("same-host: the load generator shares the host with the target; do not use these numbers as capacity claims")
    return {
        "runs": per_run,
        "saturation": saturation,
        "bottleneck": bottleneck,
        "cpu_by_category": {k: round(v, 2) for k, v in sorted(cpu_by_category.items())},
        "notes": notes,
    }


def top_self_time_pyspy_raw(text: str, limit: int = 15) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    total = 0
    for line in text.splitlines():
        stack, _, count = line.rpartition(" ")
        if not stack or not count.isdigit():
            continue
        leaf = stack.split(";")[-1]
        counts[leaf] += int(count)
        total += int(count)
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"frame": frame, "samples": count, "percent": round(count / total * 100, 2) if total else 0.0} for frame, count in ranked]


def top_self_time_cpuprofile(text: str, limit: int = 15) -> list[dict[str, Any]]:
    data = json.loads(text)
    nodes = {node["id"]: node for node in data.get("nodes") or []}
    samples = data.get("samples") or []
    deltas = data.get("timeDeltas") or []
    self_us: dict[int, float] = defaultdict(float)
    for index, node_id in enumerate(samples):
        self_us[node_id] += float(deltas[index]) if index < len(deltas) else 0.0
    by_frame: dict[str, float] = defaultdict(float)
    for node_id, micros in self_us.items():
        frame = (nodes.get(node_id) or {}).get("callFrame") or {}
        name = frame.get("functionName") or "(anonymous)"
        url = frame.get("url") or ""
        line = int(frame.get("lineNumber", -1)) + 1
        by_frame[f"{name} {url}:{line}".strip()] += micros
    total = sum(by_frame.values())
    ranked = sorted(by_frame.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"frame": frame, "self_ms": round(micros / 1000, 2), "percent": round(micros / total * 100, 2) if total else 0.0} for frame, micros in ranked]
