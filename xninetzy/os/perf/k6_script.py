from __future__ import annotations

import json
import re
from typing import Any

_NAME = re.compile(r"^[A-Za-z0-9_.:\-]{1,64}$")
_DURATION = re.compile(r"^\d+(?:ms|s|m|h)$")
_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
DEFAULT_SLO: dict[str, float] = {"p95_ms": 500.0, "p99_ms": 1500.0, "error_rate": 0.01}
MAX_VUS = 20000


class PlanError(ValueError):
    pass


def derive_operations_from_openapi(data: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, methods in sorted((data.get("paths") or {}).items()):
        get = (methods or {}).get("get")
        if get is None or "{" in path:
            continue
        required = [p for p in get.get("parameters") or [] if p.get("required")]
        if required:
            continue
        name = str(get.get("operationId") or "GET_" + re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_") or "root")
        operations.append({"name": name, "method": "GET", "path": path})
    return operations


def validate_operations(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not operations:
        raise PlanError("operations kosong")
    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    for op in operations:
        name = str(op.get("name", ""))
        if not _NAME.match(name):
            raise PlanError(f"nama operasi tidak valid: {name!r}")
        if name in seen:
            raise PlanError(f"nama operasi duplikat: {name}")
        seen.add(name)
        path = str(op.get("path", ""))
        if not path.startswith("/"):
            raise PlanError(f"path harus diawali /: {name}")
        method = str(op.get("method", "POST" if op.get("graphql") else "GET")).upper()
        if method not in _METHODS:
            raise PlanError(f"method tidak didukung: {method}")
        weight = int(op.get("weight", 1))
        if weight < 1:
            raise PlanError(f"weight harus >= 1: {name}")
        entry: dict[str, Any] = {"name": name, "method": method, "path": path, "weight": weight}
        if op.get("graphql"):
            gql = op["graphql"]
            entry["graphql"] = {"query": str(gql["query"]), "variables": gql.get("variables") or {}}
        if op.get("body") is not None:
            entry["body"] = op["body"]
        if op.get("headers"):
            entry["headers"] = {str(k): str(v) for k, v in op["headers"].items()}
        cleaned.append(entry)
    return cleaned


def _check_duration(label: str, value: str) -> str:
    if not _DURATION.match(value):
        raise PlanError(f"{label} tidak valid: {value!r}")
    return value


def render_k6_script(
    base_url: str,
    operations: list[dict[str, Any]],
    slo: dict[str, float] | None = None,
    vus: int = 100,
    ramp: str = "30s",
    hold: str = "2m",
    down: str = "30s",
    think_min: float = 0.5,
    think_max: float = 1.5,
) -> str:
    if not 1 <= int(vus) <= MAX_VUS:
        raise PlanError(f"vus harus 1..{MAX_VUS}")
    if not (0 <= think_min <= think_max <= 60):
        raise PlanError("think time tidak valid")
    ops = validate_operations(operations)
    limits = {**DEFAULT_SLO, **(slo or {})}
    stages = [
        {"duration": _check_duration("ramp", ramp), "target": int(vus)},
        {"duration": _check_duration("hold", hold), "target": int(vus)},
        {"duration": _check_duration("down", down), "target": 0},
    ]
    p95, p99, err = float(limits["p95_ms"]), float(limits["p99_ms"]), float(limits["error_rate"])
    thresholds: dict[str, list[str]] = {
        "http_req_failed": [f"rate<{err}"],
        "http_req_duration": [f"p(95)<{p95:g}", f"p(99)<{p99:g}"],
    }
    for op in ops:
        tag = op["name"]
        thresholds[f"http_req_duration{{op:{tag}}}"] = [f"p(95)<{p95:g}"]
        thresholds[f"http_reqs{{op:{tag}}}"] = ["count>=0"]
        thresholds[f"http_req_failed{{op:{tag}}}"] = [f"rate<{err}"]
    options = {
        "stages": stages,
        "thresholds": thresholds,
        "summaryTrendStats": ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],
    }
    return (
        'import http from "k6/http";\n'
        'import { check, sleep } from "k6";\n\n'
        f"const BASE_URL = __ENV.BASE_URL || {json.dumps(base_url.rstrip('/'))};\n"
        f"const OPERATIONS = {json.dumps(ops, indent=2)};\n"
        f"const THINK_MIN = {think_min:g};\n"
        f"const THINK_MAX = {think_max:g};\n"
        "const TOTAL_WEIGHT = OPERATIONS.reduce((sum, op) => sum + op.weight, 0);\n\n"
        f"export const options = {json.dumps(options, indent=2)};\n\n"
        "function pick() {\n"
        "  let roll = Math.random() * TOTAL_WEIGHT;\n"
        "  for (const op of OPERATIONS) {\n"
        "    roll -= op.weight;\n"
        "    if (roll <= 0) return op;\n"
        "  }\n"
        "  return OPERATIONS[OPERATIONS.length - 1];\n"
        "}\n\n"
        "export default function () {\n"
        "  const op = pick();\n"
        "  const url = `${BASE_URL}${op.path}`;\n"
        "  const headers = Object.assign({}, op.headers || {});\n"
        "  const params = { headers, tags: { op: op.name } };\n"
        "  let res;\n"
        "  if (op.graphql) {\n"
        '    headers["Content-Type"] = "application/json";\n'
        "    res = http.post(url, JSON.stringify(op.graphql), params);\n"
        '  } else if (op.method === "GET") {\n'
        "    res = http.get(url, params);\n"
        "  } else {\n"
        '    if (op.body !== undefined) headers["Content-Type"] = "application/json";\n'
        "    res = http.request(op.method, url, op.body === undefined ? null : JSON.stringify(op.body), params);\n"
        "  }\n"
        '  check(res, { "status is 2xx": (r) => r.status >= 200 && r.status < 300 }, { op: op.name });\n'
        "  sleep(THINK_MIN + Math.random() * (THINK_MAX - THINK_MIN));\n"
        "}\n"
    )
