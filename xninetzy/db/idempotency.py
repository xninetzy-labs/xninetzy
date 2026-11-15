from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping
import asyncio

from xninetzy.db.sqlite import connect

IDEMPOTENCY_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
    storage_key TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

IDEMPOTENCY_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_idempotency_scope "
    "ON idempotency_keys(scope, updated_at)"
)


class IdempotencyPendingError(RuntimeError):
    """The reservation is active or its previous outcome needs reconciliation."""


def storage_key(
    scope: str, idempotency_key: str, payload: Mapping[str, Any] | None
) -> str:
    material = json.dumps(payload or {}, sort_keys=True, default=str)
    raw = f"{scope}\n{idempotency_key.strip()}\n{material}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize(result: Any) -> str:
    try:
        return json.dumps({"value": result}, default=str)
    except (TypeError, ValueError):
        return json.dumps({"value": str(result)})


def _deserialize(raw: str | None) -> Any:
    if not raw:
        return None
    data = json.loads(raw)
    return data.get("value")


def idempotent_call(
    scope: str,
    idempotency_key: str | None,
    payload: Mapping[str, Any] | None,
    execute: Callable[[], Any],
) -> tuple[Any, bool]:
    """Run ``execute`` once per (scope, key, payload); replay the stored result.

    SQLite atomically reserves the key before execution. An existing pending
    reservation is never taken over: it may belong to a concurrent caller or
    an interrupted operation whose side effects need reconciliation. Ordinary
    exceptions release the reservation for callers that can safely retry;
    this helper cannot establish whether an external side effect occurred.
    """
    normalized = (idempotency_key or "").strip()
    if not normalized:
        return execute(), True

    key = storage_key(scope, normalized, payload)
    now = _now_iso()
    with connect() as conn:
        conn.execute(IDEMPOTENCY_TABLE_DDL)
        conn.execute(IDEMPOTENCY_INDEX_DDL)
        reserved = (
            conn.execute(
                """
                INSERT OR IGNORE INTO idempotency_keys
                  (storage_key, scope, status, result_json, created_at, updated_at)
                VALUES (?, ?, 'pending', NULL, ?, ?)
                """,
                (key, scope, now, now),
            ).rowcount
            > 0
        )
        if not reserved:
            row = conn.execute(
                "SELECT status, result_json FROM idempotency_keys WHERE storage_key=?",
                (key,),
            ).fetchone()
            if row and row["status"] == "done":
                return _deserialize(row["result_json"]), False
            raise IdempotencyPendingError(
                "Idempotency reservation is pending; reconcile the previous "
                "attempt before retrying."
            )

    try:
        result = execute()
    except Exception:
        with connect() as conn:
            conn.execute("DELETE FROM idempotency_keys WHERE storage_key=?", (key,))
        raise

    with connect() as conn:
        conn.execute(
            "UPDATE idempotency_keys SET status='done', result_json=?, updated_at=? WHERE storage_key=?",
            (_serialize(result), _now_iso(), key),
        )
    return result, True


def _reserve_bound(scope: str, token: str, payload: Mapping[str, Any]) -> tuple[str, bool, Any]:
    """Separate gateway namespace keeps legacy payload-sensitive keys intact."""
    key = storage_key("gateway-v1:" + scope, token, {})
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    with connect() as conn:
        conn.execute(IDEMPOTENCY_TABLE_DDL)
        conn.execute(IDEMPOTENCY_INDEX_DDL)
        reserved = conn.execute(
            "INSERT OR IGNORE INTO idempotency_keys (storage_key,scope,status,result_json,created_at,updated_at) VALUES (?,?,'pending',?,?,?)",
            (key, "gateway-v1:" + scope, json.dumps({"payload_hash": digest}), _now_iso(), _now_iso()),
        ).rowcount
        if reserved:
            return key, True, None
        row = conn.execute("SELECT status,result_json FROM idempotency_keys WHERE storage_key=?", (key,)).fetchone()
        envelope = json.loads(row["result_json"] or "{}") if row else {}
        if envelope.get("payload_hash") != digest:
            raise ValueError("idempotency_payload_mismatch")
        if row["status"] != "done":
            raise IdempotencyPendingError("idempotency_pending: reconcile prior outcome; automatic takeover is forbidden")
        return key, False, envelope.get("value")


def _finish_bound(key: str, value: Any) -> None:
    with connect() as conn:
        row = conn.execute("SELECT result_json FROM idempotency_keys WHERE storage_key=?", (key,)).fetchone()
        envelope = json.loads(row["result_json"])
        envelope["value"] = value
        conn.execute("UPDATE idempotency_keys SET status='done',result_json=?,updated_at=? WHERE storage_key=? AND status='pending'",
                     (json.dumps(envelope, default=str), _now_iso(), key))


async def idempotent_ainvoke(
    scope: str, token: str, payload: Mapping[str, Any], execute: Callable[[], Awaitable[Any]],
) -> Any:
    """Bind one key to exact normalized payload; retain uncertain reservations.

    Timeout, cancellation, handler failure or commit failure never releases the
    reservation: a sync worker may still finish after async cancellation. This
    is replay prevention, not an external exactly-once guarantee.
    """
    key, reserved, replay = await asyncio.to_thread(_reserve_bound, scope, token, payload)
    if not reserved:
        return replay
    value = await execute()
    await asyncio.to_thread(_finish_bound, key, value)
    return value


def idempotent_invoke(scope: str, token: str, payload: Mapping[str, Any], execute: Callable[[], Any]) -> tuple[Any, bool]:
    """Synchronous counterpart with the same durable uncertain-outcome rules."""
    key, reserved, replay = _reserve_bound(scope, token, payload)
    if not reserved:
        return replay, False
    value = execute()
    _finish_bound(key, value)
    return value, True
