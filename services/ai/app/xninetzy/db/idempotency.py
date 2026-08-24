from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from app.xninetzy.db.sqlite import connect

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

    A pending reservation left by a crashed attempt is taken over on retry,
    so a failed run never poisons its key. Concurrent duplicate execution is
    out of scope for the single-process deployment and remains guarded by
    downstream unique constraints where they exist.
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
