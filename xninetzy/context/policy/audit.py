from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.sqlite import connect


AUDIT_OUTCOME_OK: str = "ok"
AUDIT_OUTCOME_ERROR: str = "error"
AUDIT_OUTCOME_BLOCKED: str = "blocked"

VALID_AUDIT_OUTCOMES: frozenset[str] = frozenset(
    {AUDIT_OUTCOME_OK, AUDIT_OUTCOME_ERROR, AUDIT_OUTCOME_BLOCKED}
)


@dataclass(frozen=True, slots=True)
class AuditLedgerEntry:
    id: int
    request_id: str
    provider_id: str
    capability: str
    side_effect_class: str
    idempotency_key: str | None
    approval_id: int | None
    args_hash: str
    args_bytes: int
    context_key: str
    outcome: str | None
    latency_ms: int | None
    error: str | None
    started_at: str
    finished_at: str | None


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_entry(row) -> AuditLedgerEntry:
    return AuditLedgerEntry(
        id=int(row["id"]),
        request_id=str(row["request_id"]),
        provider_id=str(row["provider_id"]),
        capability=str(row["capability"]),
        side_effect_class=str(row["side_effect_class"]),
        idempotency_key=row["idempotency_key"],
        approval_id=row["approval_id"],
        args_hash=str(row["args_hash"]),
        args_bytes=int(row["args_bytes"]),
        context_key=str(row["context_key"]),
        outcome=row["outcome"],
        latency_ms=row["latency_ms"],
        error=row["error"],
        started_at=str(row["started_at"]),
        finished_at=row["finished_at"],
    )


def _metadata_payload(metadata: dict[str, Any] | None) -> str:
    return json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)


def _replay_key(idempotency_key: str | None) -> str:
    return idempotency_key or f"non-idempotent:{_utcnow()}"


def record_audit_start(
    *,
    request_id: str,
    provider_id: str,
    capability: str,
    side_effect_class: str,
    idempotency_key: str | None,
    approval_id: int | None,
    args_hash: str,
    args_bytes: int,
    context_key: str,
    metadata: dict[str, Any] | None = None,
    now: str | None = None,
) -> AuditLedgerEntry:
    stamp = now or _utcnow()
    replay_key = _replay_key(idempotency_key)
    with connect() as conn:
        existing = conn.execute(
            "SELECT id FROM audit_invocations WHERE request_id = ? AND idempotency_key = ?",
            (request_id, replay_key),
        ).fetchone()
        if existing is not None:
            row = conn.execute(
                "SELECT * FROM audit_invocations WHERE id = ?",
                (existing["id"],),
            ).fetchone()
            return _row_to_entry(row)
        cursor = conn.execute(
            """
            INSERT INTO audit_invocations
                (request_id, provider_id, capability, side_effect_class,
                 idempotency_key, approval_id, args_hash, args_bytes,
                 context_key, started_at, outcome, latency_ms, error, finished_at)
            VALUES (:request_id, :provider_id, :capability, :side_effect_class,
                    :idempotency_key, :approval_id, :args_hash, :args_bytes,
                    :context_key, :started_at, :outcome, :latency_ms, :error, :finished_at)
            """,
            {
                "request_id": request_id,
                "provider_id": provider_id,
                "capability": capability,
                "side_effect_class": side_effect_class,
                "idempotency_key": replay_key,
                "approval_id": approval_id,
                "args_hash": args_hash,
                "args_bytes": args_bytes,
                "context_key": context_key,
                "started_at": stamp,
                "outcome": None,
                "latency_ms": None,
                "error": None,
                "finished_at": None,
            },
        )
        audit_id = int(cursor.lastrowid or 0)
    entry = get_audit_entry(audit_id)
    assert entry is not None
    return entry


def complete_audit_entry(
    *,
    audit_id: int,
    outcome: str,
    latency_ms: int | None = None,
    error: str | None = None,
    now: str | None = None,
) -> AuditLedgerEntry:
    if outcome not in VALID_AUDIT_OUTCOMES:
        raise ValueError(f"invalid audit outcome: {outcome!r}")
    stamp = now or _utcnow()
    with connect() as conn:
        conn.execute(
            """
            UPDATE audit_invocations
            SET outcome = ?, latency_ms = ?, error = ?, finished_at = ?
            WHERE id = ?
            """,
            (outcome, latency_ms, error, stamp, audit_id),
        )
    entry = get_audit_entry(audit_id)
    assert entry is not None
    return entry


def get_audit_entry(audit_id: int) -> AuditLedgerEntry | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM audit_invocations WHERE id = ?",
            (audit_id,),
        ).fetchone()
    return _row_to_entry(row) if row else None


def find_audit_by_idempotency(
    idempotency_key: str | None,
) -> AuditLedgerEntry | None:
    if not idempotency_key:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM audit_invocations WHERE idempotency_key = ? "
            "ORDER BY id DESC LIMIT 1",
            (idempotency_key,),
        ).fetchone()
    return _row_to_entry(row) if row else None


def list_audit_entries(
    *,
    request_id: str | None = None,
    context_key: str | None = None,
    limit: int = 100,
) -> list[AuditLedgerEntry]:
    clauses: list[str] = []
    params: list[Any] = []
    if request_id is not None:
        clauses.append("request_id = ?")
        params.append(request_id)
    if context_key is not None:
        clauses.append("context_key = ?")
        params.append(context_key)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        f"SELECT * FROM audit_invocations {where} "
        "ORDER BY id DESC LIMIT ?"
    )
    params.append(int(limit))
    with connect() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [_row_to_entry(row) for row in rows]
