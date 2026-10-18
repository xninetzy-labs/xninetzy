from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.sqlite import connect, init_db

STATUSES = frozenset({"open", "fixed", "accepted", "false_positive"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def location_fingerprint(asset: str, location: str, category: str) -> str:
    raw = f"{asset.strip().lower()}|{location.strip().lower()}|{category.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def upsert_finding(
    conn: Any,
    scope_token: str,
    *,
    fingerprint: str,
    asset: str,
    location: str,
    category: str,
    title: str,
    evidence: str,
    severity: str,
    confidence: float,
    reproduction: str,
    remediation: str = "",
    impact: str = "",
) -> tuple[int, str]:
    now = _now()
    row = conn.execute(
        "SELECT l.finding_id AS finding_id, f.status AS status "
        "FROM security_finding_lifecycle l JOIN security_findings f ON f.id = l.finding_id "
        "WHERE l.scope_token=? AND l.fingerprint=?",
        (scope_token, fingerprint),
    ).fetchone()
    if row:
        finding_id = int(row["finding_id"])
        outcome = "seen"
        if row["status"] == "fixed":
            conn.execute("UPDATE security_findings SET status='open', updated_at=? WHERE id=?", (now, finding_id))
            outcome = "reopened"
        else:
            conn.execute("UPDATE security_findings SET updated_at=? WHERE id=?", (now, finding_id))
        conn.execute(
            "UPDATE security_finding_lifecycle SET last_seen=?, seen_count=seen_count+1 WHERE finding_id=?",
            (now, finding_id),
        )
        return finding_id, outcome
    cursor = conn.execute(
        """
        INSERT INTO security_findings
          (scope_token, asset, location, category, title, evidence, precondition,
           reproduction, impact, confidence, severity, remediation, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'in-scope', ?, ?, ?, ?, ?, 'open', ?, ?)
        """,
        (scope_token, asset, location, category, title, evidence, reproduction,
         impact, confidence, severity, remediation, now, now),
    )
    finding_id = int(cursor.lastrowid)
    conn.execute(
        "INSERT INTO security_finding_lifecycle "
        "(finding_id, scope_token, fingerprint, first_seen, last_seen, seen_count) VALUES (?, ?, ?, ?, ?, 1)",
        (finding_id, scope_token, fingerprint, now, now),
    )
    return finding_id, "created"


def update_finding_status(
    scope_token: str,
    finding_id: int,
    status: str,
    fix_ref: str = "",
    regression_test: str = "",
    reason: str = "",
) -> dict[str, Any] | None:
    if status not in STATUSES:
        raise ValueError(f"status harus salah satu dari {sorted(STATUSES)}")
    init_db()
    now = _now()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, status FROM security_findings WHERE id=? AND scope_token=?",
            (finding_id, scope_token),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE security_findings SET status=?, updated_at=?, "
            "regression_test=CASE WHEN ?<>'' THEN ? ELSE regression_test END WHERE id=?",
            (status, now, regression_test, regression_test, finding_id),
        )
        conn.execute(
            "UPDATE security_finding_lifecycle SET fix_ref=CASE WHEN ?<>'' THEN ? ELSE fix_ref END, "
            "status_reason=CASE WHEN ?<>'' THEN ? ELSE status_reason END WHERE finding_id=?",
            (fix_ref, fix_ref, reason, reason, finding_id),
        )
    return {"finding_id": finding_id, "previous_status": row["status"], "status": status, "fix_ref": fix_ref, "regression_test": regression_test}


def list_findings(scope_token: str) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT f.*, l.fingerprint AS fingerprint, l.first_seen AS first_seen, "
            "l.last_seen AS last_seen, l.seen_count AS seen_count, l.fix_ref AS fix_ref "
            "FROM security_findings f LEFT JOIN security_finding_lifecycle l ON l.finding_id = f.id "
            "WHERE f.scope_token=? ORDER BY f.id",
            (scope_token,),
        ).fetchall()
    return [dict(r) for r in rows]


def record_run(
    scope_token: str,
    tool: str,
    target: str,
    status: str,
    hit_count: int,
    detail: dict[str, Any] | None = None,
    version: str = "",
) -> int:
    init_db()
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO security_scan_runs (scope_token, tool, target, status, hit_count, detail_json, version, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (scope_token, tool, target, status, hit_count, json.dumps(detail or {}, ensure_ascii=False), version, _now()),
        )
        return int(cursor.lastrowid)


def list_runs(scope_token: str) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM security_scan_runs WHERE scope_token=? ORDER BY id", (scope_token,),
        ).fetchall()
    return [dict(r) for r in rows]
