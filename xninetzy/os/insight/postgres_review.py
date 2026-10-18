from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from xninetzy.os.security.guards import redact_secrets

SEP = "\x1f"
QUERY_TIMEOUT_MS = 8000
SEQ_SCAN_MIN_ROWS = 10000
_READ_ONLY = re.compile(r"^\s*(?:select|show)\b", re.IGNORECASE)


class PsqlMissing(RuntimeError):
    pass


class PsqlError(RuntimeError):
    pass


def parse_dsn(dsn: str) -> dict[str, str]:
    parsed = urlparse(dsn)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("dsn harus postgresql://")
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": parsed.path.lstrip("/") or "postgres",
    }


def run_sql(parts: dict[str, str], sql: str, executor: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> list[list[str]]:
    if not _READ_ONLY.match(sql):
        raise PsqlError("hanya SELECT/SHOW yang diizinkan")
    binary = shutil.which("psql")
    if binary is None:
        raise PsqlMissing("psql tidak ditemukan")
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PGPASSWORD": parts.get("password", ""),
        "PGCONNECT_TIMEOUT": "5",
        "PGOPTIONS": f"-c default_transaction_read_only=on -c statement_timeout={QUERY_TIMEOUT_MS}",
    }
    command = [binary, "-X", "-A", "-t", "-F", SEP, "-v", "ON_ERROR_STOP=1",
               "-h", parts["host"], "-p", parts["port"], "-U", parts["user"], "-d", parts["dbname"], "-c", sql]
    proc = executor(command, capture_output=True, text=True, timeout=30, check=False, env=env)
    if proc.returncode != 0:
        message = (proc.stderr or "").replace(parts.get("password", "\0"), "***").strip()
        raise PsqlError(redact_secrets(message)[:300])
    return [line.split(SEP) for line in (proc.stdout or "").splitlines() if line.strip()]


def _finding(rule: str, severity: str, message: str, remediation: str) -> dict[str, str]:
    return {"id": rule, "severity": severity, "message": message, "remediation": remediation}


def review(dsn: str, pool_budget: int = 0, executor: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict[str, Any]:
    parts = parse_dsn(dsn)
    notes: list[str] = []
    findings: list[dict[str, str]] = []
    max_connections = int(run_sql(parts, "SHOW max_connections", executor)[0][0])
    activity = run_sql(
        parts,
        "SELECT coalesce(nullif(application_name,''),'(none)'), coalesce(state,'(none)'), count(*) "
        "FROM pg_stat_activity WHERE datname = current_database() GROUP BY 1,2 ORDER BY 3 DESC",
        executor,
    )
    by_application: dict[str, int] = {}
    for application, _state, count in activity:
        by_application[application] = by_application.get(application, 0) + int(count)
    total = sum(by_application.values())
    top_statements: list[dict[str, Any]] = []
    extension = run_sql(parts, "SELECT count(*) FROM pg_extension WHERE extname = 'pg_stat_statements'", executor)
    if extension and extension[0][0] == "1":
        try:
            rows = run_sql(
                parts,
                "SELECT left(query, 200), calls, round(total_exec_time::numeric, 1), round(mean_exec_time::numeric, 2), rows "
                "FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20",
                executor,
            )
        except PsqlError as exc:
            rows = []
            notes.append(f"pg_stat_statements tidak dapat dibaca: {exc}")
        top_statements = [
            {"query": redact_secrets(r[0]), "calls": int(r[1]), "total_ms": float(r[2]), "mean_ms": float(r[3]), "rows": int(r[4])}
            for r in rows
        ]
    else:
        notes.append("pg_stat_statements tidak terpasang; top query tidak tersedia")
    seq_rows = run_sql(
        parts,
        "SELECT relname, seq_scan, seq_tup_read, coalesce(idx_scan, 0), n_live_tup FROM pg_stat_user_tables "
        f"WHERE n_live_tup > {SEQ_SCAN_MIN_ROWS} AND seq_scan > coalesce(idx_scan, 0) ORDER BY seq_tup_read DESC LIMIT 20",
        executor,
    )
    index_hints = [
        {"table": r[0], "seq_scan": int(r[1]), "seq_tup_read": int(r[2]), "idx_scan": int(r[3]), "live_rows": int(r[4])}
        for r in seq_rows
    ]
    if index_hints:
        findings.append(_finding("seq-scan-heavy", "medium", f"{len(index_hints)} large tables are scanned sequentially more often than by index", "review query filters and add indexes"))
    if pool_budget:
        if pool_budget > max_connections:
            findings.append(_finding("pool-exceeds-max", "high", f"pool budget {pool_budget} exceeds max_connections {max_connections}", "lower pool sizes or add PgBouncer"))
        elif pool_budget > 0.8 * max_connections:
            findings.append(_finding("pool-near-max", "medium", f"pool budget {pool_budget} is {pool_budget / max_connections:.0%} of max_connections", "leave headroom for admin and migrations"))
    if total > 0.8 * max_connections:
        findings.append(_finding("connections-near-max", "medium", f"{total} of {max_connections} connections in use", "reduce pool sizes or use a pooler"))
    return {
        "max_connections": max_connections,
        "connections": {"total": total, "by_application": dict(sorted(by_application.items(), key=lambda kv: kv[1], reverse=True))},
        "pool_budget": pool_budget or None,
        "top_statements": top_statements,
        "missing_index_hints": index_hints,
        "findings": findings,
        "notes": notes,
    }
