from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.idempotency import idempotent_call
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.tool_results import to_tool_result


_VALID_TARGET_KIND = {"tool", "skill", "procedure", "rule", "memory", "workflow"}
_VALID_ROLLOUT = {"candidate", "canary", "full", "hold"}
_VALID_STATUS = {"proposed", "approved", "rejected", "running", "verified", "retired"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@tool
def improvement_detect(
    scope: str,
    signal: str,
    target_kind: str = "tool",
    target_id: str = "",
    notes: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Deteksi sinyal perbaikan (failure berulang, metric drift, dll).

    Args:
        scope: tool|skill|procedure|workflow|memory.
        signal: Sinyal kegagalan/peluang.
        target_kind: target_kind opsional (default=tool).
        target_id: ID target (jika diketahui).
        notes: Catatan.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if scope not in _VALID_TARGET_KIND:
        return json.dumps({"error": f"scope harus salah satu dari {sorted(_VALID_TARGET_KIND)}"}, ensure_ascii=False)
    signal_id = f"sig-{uuid.uuid4().hex[:16]}"
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('improvement_detected', 'info', 'improvement_detect', ?, ?, ?)
            """,
            (
                f"{scope}:{target_id or signal}",
                json.dumps({"signal": signal, "notes": notes, "owner": owner}),
                _now_iso(),
            ),
        )
    return json.dumps({
        "signal_id": signal_id,
        "scope": scope,
        "target_kind": target_kind,
        "target_id": target_id,
        "signal": signal,
    }, ensure_ascii=False)


@tool
def improvement_propose(
    scope: str,
    title: str,
    rationale: str,
    target_kind: str = "tool",
    target_id: str = "",
    rollout: str = "candidate",
    metrics: dict[str, Any] | None = None,
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Ajukan proposal perbaikan formal.

    Args:
        scope: tool|skill|procedure|workflow|memory.
        title: Judul ringkas.
        rationale: Alasan perubahan.
        target_kind: target_kind default 'tool'.
        target_id: ID target.
        rollout: candidate|canary|full|hold.
        metrics: Metric payload (sukses_rate|latency|...).
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if scope not in _VALID_TARGET_KIND:
        return json.dumps({"error": f"scope harus salah satu dari {sorted(_VALID_TARGET_KIND)}"}, ensure_ascii=False)
    if rollout not in _VALID_ROLLOUT:
        return json.dumps({"error": f"rollout harus salah satu dari {sorted(_VALID_ROLLOUT)}"}, ensure_ascii=False)
    if not title.strip() or not rationale.strip():
        return json.dumps({"error": "title dan rationale wajib diisi"}, ensure_ascii=False)

    def _do() -> str:
        proposal_id = f"imp-{uuid.uuid4().hex[:16]}"
        now = _now_iso()
        _ensure_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO improvement_proposals
                  (proposal_id, user_id, scope, target_kind, target_id, title,
                   rationale, metrics_json, rollout, status, metadata_json,
                   source_type, source_id, problem, proposed_change,
                   target_area, patch_json, risk_level,
                   created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id, owner, scope, target_kind, target_id,
                    title, rationale, json.dumps(metrics or {}), rollout,
                    json.dumps({"chat_id": chat_id, "sender_id": sender_id}),
                    scope, target_id, rationale, "",
                    target_kind, json.dumps({}), "medium",
                    now, now,
                ),
            )
        return json.dumps({
            "proposal_id": proposal_id,
            "scope": scope,
            "status": "proposed",
            "rollout": rollout,
        }, ensure_ascii=False)

    return idempotent_call(
        "improvement_propose", idempotency_key,
        {"owner": owner, "scope": scope, "title": title},
        _do,
    )[0]


@tool
def improvement_evaluate(
    proposal_id: str,
    metric_name: str,
    baseline: float,
    candidate: float,
    notes: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat evaluasi baseline vs kandidat untuk satu metric.

    Args:
        proposal_id: ID proposal.
        metric_name: sukses_rate|latency|cost|recall|...
        baseline: Nilai baseline.
        candidate: Nilai kandidat.
        notes: Catatan evaluasi.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    delta = candidate - baseline
    if delta >= 0:
        verdict = "improved" if baseline else "baseline_set"
    else:
        verdict = "regressed"
    _ensure_db()
    with connect() as conn:
        exists = conn.execute(
            "SELECT id FROM improvement_proposals WHERE proposal_id=?", (proposal_id,),
        ).fetchone()
        if not exists:
            return json.dumps({"error": "proposal not found", "proposal_id": proposal_id}, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO improvement_evaluations
              (proposal_id, metric_name, baseline, candidate, delta, verdict, notes, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (proposal_id, metric_name, baseline, candidate, delta, verdict, notes, _now_iso()),
        )
    return json.dumps({
        "proposal_id": proposal_id,
        "metric_name": metric_name,
        "delta": delta,
        "verdict": verdict,
    }, ensure_ascii=False)


@tool
def improvement_approve(
    proposal_id: str,
    approver: str = "system",
    rationale: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Setujui proposal (status approved).

    Args:
        proposal_id: ID proposal.
        approver: Nama approver.
        rationale: Alasan approval.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, status, metadata_json FROM improvement_proposals WHERE proposal_id=?",
            (proposal_id,),
        ).fetchone()
        if not row:
            return json.dumps({"error": "proposal not found", "proposal_id": proposal_id}, ensure_ascii=False)
        meta = json.loads(row["metadata_json"] or "{}")
        meta["approved_by"] = approver
        meta["approved_rationale"] = rationale
        conn.execute(
            """
            UPDATE improvement_proposals
               SET status='approved', rollout='canary', updated_at=?, metadata_json=?
             WHERE proposal_id=?
            """,
            (now, json.dumps(meta, ensure_ascii=False), proposal_id),
        )
    return json.dumps({"proposal_id": proposal_id, "status": "approved", "approver": approver}, ensure_ascii=False)


@tool
def improvement_reject(
    proposal_id: str,
    rationale: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Tolak proposal (status rejected).

    Args:
        proposal_id: ID proposal.
        rationale: Alasan.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        row = conn.execute(
            "SELECT metadata_json FROM improvement_proposals WHERE proposal_id=?",
            (proposal_id,),
        ).fetchone()
        if not row:
            return json.dumps({"error": "proposal not found", "proposal_id": proposal_id}, ensure_ascii=False)
        meta = json.loads(row["metadata_json"] or "{}")
        meta["reject_rationale"] = rationale
        conn.execute(
            "UPDATE improvement_proposals SET status='rejected', updated_at=?, metadata_json=? WHERE proposal_id=?",
            (now, json.dumps(meta, ensure_ascii=False), proposal_id),
        )
    return json.dumps({"proposal_id": proposal_id, "status": "rejected"}, ensure_ascii=False)


@tool
def improvement_regress(
    proposal_id: str,
    metric_name: str,
    observed_value: float,
    threshold: float = 0.0,
    notes: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat regresi yang disebabkan oleh proposal yang sudah jadi.

    Args:
        proposal_id: ID proposal penyebab.
        metric_name: Metric yang turun.
        observed_value: Nilai yang diamati.
        threshold: Ambang toleransi (default 0).
        notes: Catatan.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    regression = observed_value < threshold
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('improvement_regression', ?, 'improvement_regress', ?, ?, ?)
            """,
            (
                "high" if regression else "info",
                f"proposal:{proposal_id}",
                json.dumps({
                    "proposal_id": proposal_id,
                    "metric_name": metric_name,
                    "observed_value": observed_value,
                    "threshold": threshold,
                    "regression": regression,
                    "notes": notes,
                }),
                _now_iso(),
            ),
        )
        if regression:
            conn.execute(
                "UPDATE improvement_proposals SET status='retired', updated_at=? WHERE proposal_id=?",
                (_now_iso(), proposal_id),
            )
    return json.dumps({
        "proposal_id": proposal_id,
        "regression": regression,
        "metric_name": metric_name,
        "observed": observed_value,
    }, ensure_ascii=False)


@tool
def improvement_list(
    owner: str = "system",
    status: str = "",
    scope: str = "",
    limit: int = 20,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """List proposals dengan filter opsional.

    Args:
        owner: Owner principal.
        status: Filter status (kosong=all).
        scope: Filter scope (kosong=all).
        limit: Maks baris (cap 200).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 200))
    _ensure_db()
    where = ["user_id=?"]
    params: list[Any] = [owner]
    if status:
        where.append("status=?")
        params.append(status)
    if scope:
        where.append("scope=?")
        params.append(scope)
    sql = f"""
        SELECT proposal_id, scope, target_kind, target_id, title, rollout, status, created_at
          FROM improvement_proposals
         WHERE {" AND ".join(where)}
         ORDER BY updated_at DESC
         LIMIT ?
    """
    params.append(bounded_limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    items = [_row_dict(row) for row in rows]
    return to_tool_result(
        f"{len(items)} proposal untuk owner={owner}",
        items,
        owner=owner,
        status=status,
        scope=scope,
    )
