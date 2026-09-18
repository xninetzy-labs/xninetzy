from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.tool_results import to_tool_result


_VALID_SEVERITY = {"info", "warning", "error", "high", "critical"}
_VALID_KIND = {"trace", "metric", "log", "audit", "alert", "checkpoint"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@tool
def observability_emit(
    event_kind: str,
    severity: str = "info",
    source: str = "",
    subject: str = "",
    payload: dict[str, Any] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Emit satu observability event.

    Args:
        event_kind: trace|metric|log|audit|alert|checkpoint.
        severity: info|warning|error|high|critical.
        source: Sumber event.
        subject: Subjek (tool_name, plan_id, ...).
        payload: Payload data.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if event_kind not in _VALID_KIND:
        return json.dumps({"error": f"event_kind harus salah satu dari {sorted(_VALID_KIND)}"}, ensure_ascii=False)
    if severity not in _VALID_SEVERITY:
        return json.dumps({"error": f"severity harus salah satu dari {sorted(_VALID_SEVERITY)}"}, ensure_ascii=False)
    event_id = f"evt-{uuid.uuid4().hex[:16]}"
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_kind, severity,
                source or "unspecified",
                subject,
                json.dumps(payload or {}),
                _now_iso(),
            ),
        )
    return json.dumps({"event_id": event_id, "event_kind": event_kind, "severity": severity}, ensure_ascii=False)


@tool
def observability_query(
    event_kind: str = "",
    severity: str = "",
    source: str = "",
    subject: str = "",
    since_minutes: int = 60,
    limit: int = 50,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Query observability events dengan filter.

    Args:
        event_kind: Filter event kind (kosong=all).
        severity: Filter severity.
        source: Filter source.
        subject: Filter subject.
        since_minutes: Window waktu ke belakang (cap 10080 = 7d).
        limit: Maks baris (cap 500).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_window = max(1, min(since_minutes, 10080))
    bounded_limit = max(1, min(limit, 500))
    _ensure_db()
    where = ["occurred_at >= datetime('now', ?)"]
    params: list[Any] = [f"-{bounded_window} minutes"]
    if event_kind:
        where.append("event_kind=?")
        params.append(event_kind)
    if severity:
        where.append("severity=?")
        params.append(severity)
    if source:
        where.append("source=?")
        params.append(source)
    if subject:
        where.append("subject=?")
        params.append(subject)
    params.append(bounded_limit)
    sql = f"""
        SELECT id, event_kind, severity, source, subject, payload_json, occurred_at
          FROM observability_events
         WHERE {" AND ".join(where)}
         ORDER BY id DESC
         LIMIT ?
    """
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    items = []
    for row in rows:
        record = _row_dict(row)
        record["id"] = f"evt-{record['id']}"
        record["payload"] = json.loads(record.pop("payload_json") or "{}")
        items.append(record)
    return to_tool_result(
        f"{len(items)} event dalam {bounded_window} menit terakhir",
        items,
        filters={"event_kind": event_kind, "severity": severity, "source": source, "subject": subject},
        window_minutes=bounded_window,
    )


@tool
def observability_summary(
    since_minutes: int = 60,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Ringkasan jumlah event per kind + severity.

    Args:
        since_minutes: Window waktu ke belakang (cap 10080 = 7d).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_window = max(1, min(since_minutes, 10080))
    _ensure_db()
    with connect() as conn:
        by_kind = conn.execute(
            """
            SELECT event_kind, COUNT(*) AS n
              FROM observability_events
             WHERE occurred_at >= datetime('now', ?)
             GROUP BY event_kind ORDER BY n DESC
            """,
            (f"-{bounded_window} minutes",),
        ).fetchall()
        by_sev = conn.execute(
            """
            SELECT severity, COUNT(*) AS n
              FROM observability_events
             WHERE occurred_at >= datetime('now', ?)
             GROUP BY severity ORDER BY n DESC
            """,
            (f"-{bounded_window} minutes",),
        ).fetchall()
        top_subjects = conn.execute(
            """
            SELECT subject, COUNT(*) AS n
              FROM observability_events
             WHERE occurred_at >= datetime('now', ?)
               AND subject != ''
             GROUP BY subject ORDER BY n DESC LIMIT 10
            """,
            (f"-{bounded_window} minutes",),
        ).fetchall()
    return json.dumps({
        "window_minutes": bounded_window,
        "by_kind": [_row_dict(row) for row in by_kind],
        "by_severity": [_row_dict(row) for row in by_sev],
        "top_subjects": [_row_dict(row) for row in top_subjects],
    }, ensure_ascii=False)


@tool
def observability_checkpoint(
    label: str,
    payload: dict[str, Any] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Set checkpoint signpost untuk rewind/audit nanti.

    Args:
        label: Label checkpoint.
        payload: Payload opsional.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if not label.strip():
        return json.dumps({"error": "label wajib diisi"}, ensure_ascii=False)
    event_id = f"evt-{uuid.uuid4().hex[:16]}"
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('checkpoint', 'info', 'observability_checkpoint', ?, ?, ?)
            """,
            (
                label,
                json.dumps(payload or {}),
                _now_iso(),
            ),
        )
    return json.dumps({"event_id": event_id, "label": label, "kind": "checkpoint"}, ensure_ascii=False)


@tool
def observability_recent_checkpoints(
    limit: int = 10,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Ambil checkpoint terbaru untuk rewind context.

    Args:
        limit: Maks (cap 200).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 200))
    _ensure_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, subject, payload_json, occurred_at
              FROM observability_events
             WHERE event_kind='checkpoint'
             ORDER BY id DESC LIMIT ?
            """,
            (bounded_limit,),
        ).fetchall()
    items = []
    for row in rows:
        record = _row_dict(row)
        record["id"] = f"evt-{record['id']}"
        record["payload"] = json.loads(record.pop("payload_json") or "{}")
        items.append(record)
    return to_tool_result(
        f"{len(items)} checkpoint terbaru",
        items,
        limit=bounded_limit,
    )
