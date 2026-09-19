from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.tool_results import to_tool_result


_RUNNING = ("planned", "in_progress")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@tool
def harness_plan(
    title: str,
    steps: list[str],
    required_tools: list[str] | None = None,
    required_skills: list[str] | None = None,
    verification: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Buat rencana langkah + daftar tools/skills sebagai conductor.

    Args:
        title: Judul task.
        steps: Daftar langkah.
        required_tools: Tools yang dipakai.
        required_skills: Skills yang dipakai.
        verification: Cara verifikasi rencana.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if not title.strip() or not steps:
        return json.dumps({"error": "title dan steps wajib diisi"}, ensure_ascii=False)
    plan_id = f"plan-{uuid.uuid4().hex[:16]}"
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO harness_plans
              (plan_id, owner, title, steps_json, required_tools_json,
               required_skills_json, verification, status, metadata_json,
               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?)
            """,
            (
                plan_id, owner, title,
                json.dumps(steps), json.dumps(required_tools or []),
                json.dumps(required_skills or []), verification,
                json.dumps({"chat_id": chat_id, "sender_id": sender_id}),
                _now_iso(), _now_iso(),
            ),
        )
    return json.dumps({
        "plan_id": plan_id,
        "title": title,
        "status": "planned",
        "step_count": len(steps),
    }, ensure_ascii=False)


@tool
def harness_execute(
    plan_id: str,
    record_actions: bool = True,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Mulai eksekusi rencana (status -> in_progress).

    Args:
        plan_id: ID rencana.
        record_actions: True untuk catat action trail.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        row = conn.execute(
            "SELECT status FROM harness_plans WHERE plan_id=?",
            (plan_id,),
        ).fetchone()
        if not row:
            return json.dumps({"error": "plan not found", "plan_id": plan_id}, ensure_ascii=False)
        if row["status"] not in _RUNNING:
            conn.execute(
                "UPDATE harness_plans SET status='in_progress', updated_at=? WHERE plan_id=?",
                (now, plan_id),
            )
        if record_actions:
            conn.execute(
                """
                INSERT INTO harness_actions
                  (action_id, plan_id, sequence, tool_name, args_json, outcome, recorded_at)
                VALUES (?, ?, 0, 'harness_plan', '{}', 'started', ?)
                """,
                (f"act-{uuid.uuid4().hex[:16]}", plan_id, now),
            )
    return json.dumps({"plan_id": plan_id, "status": "in_progress"}, ensure_ascii=False)


@tool
def harness_record_step(
    plan_id: str,
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
    outcome: str = "ok",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat satu langkah eksekusi ke action trail.

    Args:
        plan_id: ID rencana.
        tool_name: Nama tool yang baru dipanggil.
        tool_args: Argumen (disimpan sebagai JSON).
        outcome: ok|error|skipped.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM harness_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if not row:
            return json.dumps({"error": "plan not found", "plan_id": plan_id}, ensure_ascii=False)
        seq = conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS max_seq FROM harness_actions WHERE plan_id=?",
            (plan_id,),
        ).fetchone()["max_seq"] + 1
        conn.execute(
            """
            INSERT INTO harness_actions
              (action_id, plan_id, sequence, tool_name, args_json, outcome, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"act-{uuid.uuid4().hex[:16]}",
                plan_id, seq, tool_name,
                json.dumps(tool_args or {}), outcome, _now_iso(),
            ),
        )
    try:
        from xninetzy.interfaces.mcp_tool_adapter import (
            _auto_memory_record,
            _auto_graph_record,
            _auto_improve_record,
        )
        owner = (sender_id or chat_id or "system").strip() or "system"
        args_preview = tool_args or {}
        if outcome == "error":
            _auto_improve_record(tool_name, args_preview, RuntimeError(outcome), owner)
        else:
            _auto_improve_record(tool_name, args_preview, None, owner)
        if outcome == "ok":
            _auto_memory_record(tool_name, args_preview, json.dumps(args_preview, default=str)[:600], owner)
            from xninetzy.tools.manifest import manifest_for
            try:
                risk = manifest_for(tool_name).risk.value
            except Exception:
                risk = "write"
            _auto_graph_record(tool_name, args_preview, json.dumps(args_preview, default=str)[:400], risk, owner)
    except Exception:
        pass
    return json.dumps({"plan_id": plan_id, "sequence": seq, "tool_name": tool_name}, ensure_ascii=False)


@tool
def harness_verify(
    plan_id: str,
    evidence: str,
    passed: bool,
    notes: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat hasil verifikasi rencana.

    Args:
        plan_id: ID rencana.
        evidence: Bukti verifikasi.
        passed: True jika lulus.
        notes: Catatan tambahan.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    now = _now_iso()
    final_status = "verified" if passed else "failed"
    with connect() as conn:
        exists = conn.execute("SELECT id FROM harness_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if not exists:
            return json.dumps({"error": "plan not found", "plan_id": plan_id}, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO harness_verifications
              (plan_id, passed, evidence, notes, verified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (plan_id, 1 if passed else 0, evidence, notes, now),
        )
        conn.execute(
            "UPDATE harness_plans SET status=?, updated_at=? WHERE plan_id=?",
            (final_status, now, plan_id),
        )
    return json.dumps({"plan_id": plan_id, "status": final_status, "passed": passed}, ensure_ascii=False)


@tool
def harness_recover(
    plan_id: str,
    from_sequence: int,
    new_status: str = "planned",
    reason: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Rollback langkah + reset status rencana untuk re-run.

    Args:
        plan_id: ID rencana.
        from_sequence: Sequence minimum yang akan di-truncate.
        new_status: Status tujuan (planned|in_progress).
        reason: Alasan recovery.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if new_status not in {"planned", "in_progress"}:
        return json.dumps({"error": "new_status tidak valid"}, ensure_ascii=False)
    _ensure_db()
    now = _now_iso()
    with connect() as conn:
        deleted = conn.execute(
            "DELETE FROM harness_actions WHERE plan_id=? AND sequence>=?",
            (plan_id, from_sequence),
        ).rowcount
        conn.execute(
            "UPDATE harness_plans SET status=?, updated_at=? WHERE plan_id=?",
            (new_status, now, plan_id),
        )
    return json.dumps({
        "plan_id": plan_id,
        "truncated": deleted,
        "status": new_status,
        "reason": reason,
    }, ensure_ascii=False)


@tool
def harness_trace(
    plan_id: str,
    include_actions: bool = True,
    include_verifications: bool = True,
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Lihat urutan langkah + verifikasi untuk satu rencana.

    Args:
        plan_id: ID rencana.
        include_actions: Sertakan action trail.
        include_verifications: Sertakan verifications.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    payload: dict[str, Any] = {"plan_id": plan_id}
    with connect() as conn:
        plan = conn.execute(
            "SELECT plan_id, owner, title, status, steps_json FROM harness_plans WHERE plan_id=?",
            (plan_id,),
        ).fetchone()
        if not plan:
            return json.dumps({"error": "plan not found", "plan_id": plan_id}, ensure_ascii=False)
        payload["plan"] = {
            **_row_dict(plan),
            "steps": json.loads(plan["steps_json"]),
        }
        if include_actions:
            rows = conn.execute(
                """
                SELECT sequence, tool_name, args_json, outcome, recorded_at
                  FROM harness_actions
                 WHERE plan_id=?
                 ORDER BY sequence ASC
                """,
                (plan_id,),
            ).fetchall()
            payload["actions"] = [
                {
                    **_row_dict(row),
                    "args": json.loads(row["args_json"]),
                }
                for row in rows
            ]
        if include_verifications:
            rows = conn.execute(
                """
                SELECT passed, evidence, notes, verified_at
                  FROM harness_verifications
                 WHERE plan_id=?
                 ORDER BY id DESC
                """,
                (plan_id,),
            ).fetchall()
            payload["verifications"] = [_row_dict(row) for row in rows]
    return json.dumps(payload, ensure_ascii=False)


@tool
def harness_review(
    owner: str = "system",
    status_filter: str = "",
    limit: int = 10,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Review semua rencana milik owner dengan ringkasan status.

    Args:
        owner: Owner principal.
        status_filter: Filter status (kosong=all, planned|in_progress|verified|failed).
        limit: Maks baris (cap 100).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 100))
    _ensure_db()
    with connect() as conn:
        if status_filter:
            rows = conn.execute(
                """
                SELECT plan_id, title, status, created_at, updated_at
                  FROM harness_plans
                 WHERE owner=? AND status=?
                 ORDER BY updated_at DESC
                 LIMIT ?
                """,
                (owner, status_filter, bounded_limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT plan_id, title, status, created_at, updated_at
                  FROM harness_plans
                 WHERE owner=?
                 ORDER BY updated_at DESC
                 LIMIT ?
                """,
                (owner, bounded_limit),
            ).fetchall()
    items = [_row_dict(row) for row in rows]
    return to_tool_result(
        f"{len(items)} rencana untuk owner={owner}",
        items,
        owner=owner,
        status_filter=status_filter,
    )


@tool
def harness_plan_drift_detect(
    plan_id: str,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Bandingkan required_tools sebuah plan dengan registry saat ini.

    Args:
        plan_id: Plan id.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT plan_id, required_tools_json, status FROM harness_plans WHERE plan_id=?",
            (plan_id,),
        ).fetchone()
    if row is None:
        return to_tool_result(
            f"plan {plan_id} tidak ditemukan",
            {"plan_id": plan_id, "status": "not_found"},
            plan_id=plan_id,
        )
    required = []
    try:
        raw = row["required_tools_json"]
        if raw:
            required = [str(item) for item in json.loads(raw)]
    except (json.JSONDecodeError, TypeError):
        required = []
    from xninetzy.tools.registry import get_all_tools

    registered = {tool.name for tool in get_all_tools()}
    missing = sorted(set(required) - registered)
    drift = {
        "plan_id": plan_id,
        "status": row["status"],
        "required": required,
        "registered_count": len(registered),
        "missing_tools": missing,
        "drift_detected": bool(missing),
    }
    return to_tool_result(
        f"plan {plan_id}: drift={'ya' if missing else 'tidak'}",
        drift,
        plan_id=plan_id,
    )


@tool
def harness_resume_safe(
    plan_id: str,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Baca checkpoint terakhir dan kembalikan aksi yang masih bisa diulang.

    Args:
        plan_id: Plan id.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    with connect() as conn:
        plan_row = conn.execute(
            "SELECT plan_id, status FROM harness_plans WHERE plan_id=?",
            (plan_id,),
        ).fetchone()
        if plan_row is None:
            return to_tool_result(
                f"plan {plan_id} tidak ditemukan",
                {"plan_id": plan_id, "status": "not_found"},
                plan_id=plan_id,
            )
        action_rows = conn.execute(
            """
            SELECT action_id, sequence, tool_name, args_json, outcome
              FROM harness_actions
             WHERE plan_id=?
             ORDER BY sequence ASC
            """,
            (plan_id,),
        ).fetchall()
    last_sequence = -1
    replayable: list[dict[str, Any]] = []
    completed_sequences: set[int] = set()
    for row in action_rows:
        try:
            sequence = int(row["sequence"])
        except (TypeError, ValueError):
            continue
        completed_sequences.add(sequence)
        last_sequence = max(last_sequence, sequence)
        if str(row["outcome"] or "").strip().lower() != "ok":
            replayable.append(
                {
                    "action_id": row["action_id"],
                    "sequence": sequence,
                    "tool_name": row["tool_name"],
                    "outcome": row["outcome"],
                }
            )
    next_sequence = last_sequence + 1 if last_sequence >= 0 else 0
    return to_tool_result(
        f"plan {plan_id}: replay {len(replayable)} actions from sequence {next_sequence}",
        {
            "plan_id": plan_id,
            "plan_status": plan_row["status"],
            "last_sequence": last_sequence,
            "next_sequence": next_sequence,
            "replayable": replayable,
            "completed_count": len(completed_sequences),
        },
        plan_id=plan_id,
    )


@tool
def harness_checkpoint_commit(
    plan_id: str,
    step_id: str,
    status: str,
    payload: dict[str, Any] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat checkpoint persisten untuk satu langkah plan.

    Args:
        plan_id: Plan id.
        step_id: Step identifier.
        status: ok|error|halted|skipped.
        payload: Optional dict for audit context.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    _ensure_db()
    bounded_status = str(status or "").strip().lower() or "unknown"
    if bounded_status not in {"ok", "error", "halted", "skipped", "unknown"}:
        bounded_status = "unknown"
    payload_json = json.dumps(payload or {}, ensure_ascii=False, default=str)
    now = _now_iso()
    event_subject = f"{plan_id}:{step_id}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('harness_checkpoint', 'info', 'harness_tools', ?, ?, ?)
            """,
            (event_subject, payload_json, now),
        )
    return to_tool_result(
        f"checkpoint {plan_id}:{step_id} -> {bounded_status}",
        {
            "plan_id": plan_id,
            "step_id": step_id,
            "status": bounded_status,
            "occurred_at": now,
        },
        plan_id=plan_id,
        step_id=step_id,
    )
