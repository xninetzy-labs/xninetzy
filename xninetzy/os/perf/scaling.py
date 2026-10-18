from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from xninetzy.os.security import infra_review
from xninetzy.os.security.authz import _SKIP_DIRS

CHECKS: tuple[tuple[str, str], ...] = (
    ("in-process-bus", "no in-process pub/sub shared across requests"),
    ("unled-scheduler", "scheduled jobs use leader election or a single runner"),
    ("local-cache", "module-level caches invalidate across instances"),
    ("local-files", "no local file writes needed across replicas"),
    ("memory-state", "sessions and rate limits are not held in process memory"),
    ("celery-beat", "exactly one Celery beat process"),
    ("nginx-upstream", "nginx upstream resolution and keepalive"),
    ("db-connection-budget", "replicas x pool fits max_connections"),
)
_SOURCE_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".py"})
_CONFIG_NAMES = re.compile(r"(?:^|/)(?:docker-compose[\w.\-]*|compose[\w.\-]*)\.ya?ml$|(?:^|/)Procfile$|(?:^|/)Dockerfile[\w.\-]*$|\.conf$|supervisord[\w.\-]*\.ini$")
_TEST_MARKERS = ("__tests__", "tests", "test", "fixtures", "__mocks__", "e2e")
_TRANSPORT = re.compile(r"ioredis|\bredis\b|\bnats\b|kafkajs|amqplib|pg-listen|\bLISTEN\b|pubsub|\bpublish\b|\bsubscribe\b", re.IGNORECASE)
_LEADER = re.compile(r"leader|advisory|redlock|\bsetnx\b|pg_try_advisory|acquireLock|tryLock|SET\b.*\bNX\b", re.IGNORECASE)
_INVALIDATION = re.compile(r"invalidate|pubsub|\bsubscribe\b|\bpublish\b|clear_cache|cache_clear", re.IGNORECASE)
_BUS = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*new\s+EventEmitter\s*\(|^\w+\s*=\s*asyncio\.Queue\s*\(")
_INTERVAL = re.compile(r"\bsetInterval\s*\(")
_CRON = re.compile(r"node-cron|cron\.schedule\s*\(|new\s+CronJob\s*\(|@Cron\s*\(|schedule\.every\s*\(|BackgroundScheduler\s*\(|AsyncIOScheduler\s*\(|APScheduler")
_CACHE = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+\w*[cC]ache\w*\s*=\s*new\s+(?:Map|LRUCache|Set)\b|^_?\w*cache\w*\s*(?::[^=]+)?=\s*(?:\{\}|dict\(\))|@(?:functools\.)?(?:lru_cache|cache)\b")
_FILE_WRITE = re.compile(r"\b(?:writeFile|writeFileSync|appendFile|appendFileSync|createWriteStream)\s*\(|\bBun\.write\s*\(|\bopen\([^)]*['\"][wa]b?\+?['\"]")
_MEMORY_STATE = re.compile(r"\b\w*(?:session|rateLimit|ratelimit|bucket|throttle)\w*\s*=\s*new\s+Map\b|\bMemoryStore\b|memory://", re.IGNORECASE)
_CELERY_APP = re.compile(r"\bCelery\s*\(")
_BEAT_SCHEDULE = re.compile(r"beat_schedule|\bcrontab\s*\(")
_BEAT_COMMAND = re.compile(r"celery[^\n]*\bbeat\b|\bbeat\s+-A\b|celery[^\n]*\s-B\b")
_POOL = (
    re.compile(r"\bpool_size\s*[=:]\s*(\d+)"),
    re.compile(r"\bPOOL_(?:SIZE|MAX)\w*\s*[=:]\s*['\"]?(\d+)"),
    re.compile(r"\bpool\s*:\s*\{[^}]*\bmax\s*:\s*(\d+)"),
    re.compile(r"\bmax_connections\s*=\s*(\d+)\b"),
)
MAX_FILES = 3000
MAX_FILE_BYTES = 1_000_000


def _finding(check: str, severity: str, file: str, line: int, message: str, remediation: str) -> dict[str, Any]:
    return {"check": check, "severity": severity, "file": file, "line": line, "message": message, "remediation": remediation}


def _is_test(rel: Path) -> bool:
    if any(part in _TEST_MARKERS for part in rel.parts[:-1]):
        return True
    return bool(re.search(r"(?:^test_|_test\.|\.test\.|\.spec\.)", rel.parts[-1]))


def _walk(root: Path) -> list[Path]:
    files: list[Path] = []
    stack = [root]
    while stack and len(files) < MAX_FILES:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in _SKIP_DIRS:
                    stack.append(entry)
            elif entry.stat().st_size <= MAX_FILE_BYTES:
                files.append(entry)
    return sorted(files)


def _compose_services(text: str) -> dict[str, dict[str, Any]]:
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return {}
    services = data.get("services") if isinstance(data, dict) else None
    return {k: (v or {}) for k, v in services.items()} if isinstance(services, dict) else {}


def _replicas(service: dict[str, Any]) -> int:
    deploy = service.get("deploy") or {}
    for value in (deploy.get("replicas"), service.get("scale")):
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return 1


def _command(service: dict[str, Any]) -> str:
    command = service.get("command") or ""
    return " ".join(command) if isinstance(command, list) else str(command)


def scan_repo(
    root: Path,
    replicas: int = 0,
    pool_size: int = 0,
    max_connections: int = 0,
    other_connections: int = 0,
    include_tests: bool = False,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    beat_commands: list[tuple[str, int, int]] = []
    celery_apps: list[tuple[str, int]] = []
    beat_schedules: list[tuple[str, int]] = []
    discovered_replicas = 0
    discovered_pool = 0
    nginx_seen = False
    for path in _walk(root):
        rel = path.relative_to(root)
        rel_text = str(rel)
        is_source = path.suffix.lower() in _SOURCE_SUFFIXES
        is_config = bool(_CONFIG_NAMES.search(rel_text))
        if not is_source and not is_config:
            continue
        if is_source and not include_tests and _is_test(rel):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if is_source:
            has_transport = bool(_TRANSPORT.search(text))
            has_leader = bool(_LEADER.search(text))
            has_invalidation = bool(_INVALIDATION.search(text))
            for number, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith(("//", "#", "*", "/*")):
                    continue
                if _BUS.search(line):
                    findings.append(_finding("in-process-bus", "low" if has_transport else "high", rel_text, number,
                                             "in-process event bus; subscribers on other replicas never see the event",
                                             "publish through Redis, NATS or Postgres LISTEN/NOTIFY"))
                if (_INTERVAL.search(line) or _CRON.search(line)) and not has_leader:
                    findings.append(_finding("unled-scheduler", "medium", rel_text, number,
                                             "scheduled job with no leader election in this file; it runs on every replica",
                                             "take a Redis or Postgres advisory lock, or run it in one worker"))
                if _CACHE.search(line) and not has_invalidation:
                    findings.append(_finding("local-cache", "medium", rel_text, number,
                                             "module-level cache with no cross-instance invalidation",
                                             "use a shared cache or publish invalidations"))
                if _FILE_WRITE.search(line):
                    findings.append(_finding("local-files", "low", rel_text, number,
                                             "local file write; other replicas cannot read it",
                                             "write to object storage or a shared volume"))
                if _MEMORY_STATE.search(line):
                    findings.append(_finding("memory-state", "medium", rel_text, number,
                                             "session or rate-limit state held in process memory",
                                             "move it to Redis"))
                if _CELERY_APP.search(line):
                    celery_apps.append((rel_text, number))
                if _BEAT_SCHEDULE.search(line):
                    beat_schedules.append((rel_text, number))
                for pattern in _POOL:
                    match = pattern.search(line)
                    if match and not discovered_pool and "max_connections" not in line:
                        discovered_pool = int(match.group(1))
        if is_config:
            name = path.name.lower()
            if name.startswith(("docker-compose", "compose")):
                for service_name, service in _compose_services(text).items():
                    count = _replicas(service)
                    discovered_replicas = max(discovered_replicas, count) if service_name != "db" else discovered_replicas
                    if _BEAT_COMMAND.search(_command(service)):
                        beat_commands.append((rel_text, 0, count))
            elif name == "procfile" or name.startswith(("dockerfile", "supervisord")):
                for number, line in enumerate(lines, start=1):
                    if _BEAT_COMMAND.search(line):
                        beat_commands.append((rel_text, number, 1))
            if path.suffix == ".conf" and "upstream" in text:
                nginx_seen = True
                for item in infra_review.review_nginx(text):
                    if item["id"] in {"upstream-static-dns", "connection-upgrade-hardcoded"}:
                        findings.append(_finding("nginx-upstream", item["severity"], rel_text, 0, f"{item['where']}: {item['message']}", item["remediation"]))
    if celery_apps and (beat_schedules or beat_commands):
        total_beats = sum(count for _f, _l, count in beat_commands)
        if beat_schedules and not beat_commands:
            file, line = beat_schedules[0]
            findings.append(_finding("celery-beat", "high", file, line, "beat_schedule defined but no celery beat process is started anywhere",
                                     "run exactly one celery beat process"))
        elif total_beats > 1:
            file, line, _count = beat_commands[0]
            findings.append(_finding("celery-beat", "high", file, line, f"{total_beats} celery beat instances; every scheduled task fires {total_beats} times",
                                     "run a single beat instance"))
    effective_replicas = replicas or discovered_replicas
    effective_pool = pool_size or discovered_pool
    budget: dict[str, Any] = {"status": "not_assessed", "reason": "replicas, pool_size and max_connections are all required"}
    if effective_replicas and effective_pool and max_connections:
        used = effective_replicas * effective_pool + other_connections
        ratio = used / max_connections
        budget = {"status": "ok", "replicas": effective_replicas, "pool_size": effective_pool, "other": other_connections,
                  "used": used, "max_connections": max_connections, "ratio": round(ratio, 2)}
        if used > max_connections:
            budget["status"] = "risk"
            findings.append(_finding("db-connection-budget", "high", "", 0, f"{used} connections needed but max_connections is {max_connections}",
                                     "lower the pool, use PgBouncer, or raise max_connections"))
        elif ratio > 0.8:
            budget["status"] = "risk"
            findings.append(_finding("db-connection-budget", "medium", "", 0, f"{used} of {max_connections} connections in use ({ratio:.0%})",
                                     "leave headroom for migrations and admin connections"))
    checklist: list[dict[str, Any]] = []
    for check_id, description in CHECKS:
        hits = [f for f in findings if f["check"] == check_id]
        if check_id == "db-connection-budget":
            status = budget["status"]
        elif check_id == "nginx-upstream" and not nginx_seen:
            status = "not_assessed"
        elif check_id == "celery-beat" and not celery_apps:
            status = "not_applicable"
        else:
            status = "risk" if hits else "ok"
        checklist.append({"id": check_id, "description": description, "status": status,
                          "locations": [f"{h['file']}:{h['line']}" if h["line"] else h["file"] for h in hits]})
    return {"findings": findings, "checklist": checklist, "db_connection_budget": budget}
