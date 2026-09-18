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


_VALID_EPISODE_STATUS = {"active", "promoted", "retired", "deprecated"}
_VALID_PROCEDURE_STATUS = {"candidate", "verified", "promoted", "retired"}
_VALID_PROMOTION_STAGES = {"OBSERVATION", "CANDIDATE", "VERIFIED", "PROMOTED", "REUSED", "REEVALUATED", "RETIRED"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@tool
def memory_episode_store(
    task: str,
    intent: str,
    plan: list[str],
    actions: list[dict[str, Any]],
    outcome: str = "",
    verification: str = "",
    reward: float = 0.0,
    usefulness: float = 0.5,
    related_tools: list[str] | None = None,
    owner: str = "system",
    scope: str = "personal",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Simpan episode (task + plan + actions + outcome) untuk pembelajaran.

    Args:
        task: Nama task yang dijalankan.
        intent: Intent asli.
        plan: Daftar langkah rencana.
        actions: Daftar aksi (tool, args, latency, result).
        outcome: success|partial|failure.
        verification: Bukti verifikasi.
        reward: Skor reward 0-1.
        usefulness: Skor kegunaan 0-1.
        related_tools: Daftar nama tool yang dipakai.
        owner: Owner principal.
        scope: personal|team|project.
        chat_id: Chat ID.
        sender_id: Owner principal (dari context).
        idempotency_key: Kunci opsional.
    """
    bounded_reward = max(0.0, min(reward, 1.0))
    bounded_use = max(0.0, min(usefulness, 1.0))

    def _do() -> str:
        episode_id = f"ep-{uuid.uuid4().hex[:16]}"
        now = _now_iso()
        _ensure_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_episodes
                  (episode_id, scope, owner, task, intent, plan_json, actions_json,
                   outcome, verification, reward, usefulness, related_tools_json,
                   metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id, scope, owner, task, intent,
                    json.dumps(plan), json.dumps(actions),
                    outcome, verification, bounded_reward, bounded_use,
                    json.dumps(related_tools or []),
                    json.dumps({"chat_id": chat_id, "sender_id": sender_id}),
                    now, now,
                ),
            )
        payload = {
            "episode_id": episode_id,
            "task": task,
            "owner": owner,
            "reward": bounded_reward,
            "usefulness": bounded_use,
        }
        return json.dumps(payload, ensure_ascii=False)

    return idempotent_call(
        "memory_episode_store", idempotency_key,
        {"task": task, "owner": owner, "intent": intent},
        _do,
    )[0]


@tool
def memory_episode_search(
    query: str,
    owner: str = "system",
    limit: int = 10,
    min_reward: float = 0.0,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Cari episode berdasarkan substring task/intent/outcome.

    Args:
        query: String yang dicari.
        owner: Owner principal.
        limit: Maks hasil (cap 100).
        min_reward: Skor reward minimum (0-1).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 100))
    bounded_min = max(0.0, min(min_reward, 1.0))
    _ensure_db()
    needle = f"%{query.strip().lower()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT episode_id, task, intent, outcome, reward, usefulness,
                   plan_json, actions_json, related_tools_json, created_at
              FROM memory_episodes
             WHERE owner=? AND reward>=? AND status='active'
               AND (LOWER(task) LIKE ? OR LOWER(intent) LIKE ? OR LOWER(outcome) LIKE ?)
             ORDER BY reward DESC, usefulness DESC, created_at DESC
             LIMIT ?
            """,
            (owner, bounded_min, needle, needle, needle, bounded_limit),
        ).fetchall()
    items = []
    for row in rows:
        record = _row_dict(row)
        record["plan"] = json.loads(record.pop("plan_json"))
        record["actions"] = json.loads(record.pop("actions_json"))
        record["related_tools"] = json.loads(record.pop("related_tools_json"))
        items.append(record)
    return to_tool_result(
        f"{len(items)} episode cocok untuk '{query}'.",
        items,
        owner=owner,
        query=query,
        limit=bounded_limit,
    )


@tool
def memory_failure_store(
    failure_class: str,
    title: str,
    context: str = "",
    root_cause: str = "",
    recovery: str = "",
    recovery_success: bool = False,
    related_tool: str = "",
    related_skill: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Catat pola kegagalan ke failure memory untuk pembelajaran ulang.

    Args:
        failure_class: TOOL_NOT_FOUND|INVALID_INPUT|TIMEOUT|RATE_LIMIT|PARSING_FAILURE|...
        title: Judul ringkas.
        context: Konteks saat gagal.
        root_cause: Akar penyebab.
        recovery: Strategi pemulihan.
        recovery_success: True jika recovery berhasil.
        related_tool: Tool terkait.
        related_skill: Skill terkait.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if not failure_class.strip() or not title.strip():
        return json.dumps({"error": "failure_class dan title wajib diisi"}, ensure_ascii=False)

    def _do() -> str:
        failure_id = f"fail-{uuid.uuid4().hex[:16]}"
        now = _now_iso()
        _ensure_db()
        with connect() as conn:
            existing = conn.execute(
                """
                SELECT id, recurrence_count FROM memory_failures
                 WHERE owner=? AND failure_class=? AND title=?
                """,
                (owner, failure_class, title),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE memory_failures
                       SET recurrence_count = recurrence_count + 1,
                           last_seen_at = ?,
                           root_cause = COALESCE(NULLIF(?, ''), root_cause),
                           recovery = COALESCE(NULLIF(?, ''), recovery),
                           recovery_success = CASE WHEN ? THEN 1 ELSE recovery_success END
                     WHERE id = ?
                    """,
                    (now, root_cause, recovery, recovery_success, existing["id"]),
                )
                return json.dumps({
                    "failure_id": failure_id,
                    "deduplicated": True,
                    "recurrence_count": existing["recurrence_count"] + 1,
                }, ensure_ascii=False)
            conn.execute(
                """
                INSERT INTO memory_failures
                  (failure_id, owner, failure_class, title, context, root_cause,
                   recovery, recovery_success, related_tool, related_skill,
                   metadata_json, last_seen_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    failure_id, owner, failure_class, title, context, root_cause,
                    recovery, 1 if recovery_success else 0, related_tool, related_skill,
                    json.dumps({"chat_id": chat_id, "sender_id": sender_id}),
                    now, now,
                ),
            )
        return json.dumps({
            "failure_id": failure_id,
            "failure_class": failure_class,
            "deduplicated": False,
        }, ensure_ascii=False)

    return idempotent_call(
        "memory_failure_store", idempotency_key,
        {"owner": owner, "failure_class": failure_class, "title": title},
        _do,
    )[0]


@tool
def memory_procedure_store(
    name: str,
    trigger: str,
    steps: list[str],
    tools: list[str] | None = None,
    skills: list[str] | None = None,
    verification: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Simpan prosedur (workflow yang terbukti berhasil) untuk dipakai ulang.

    Args:
        name: Nama prosedur.
        trigger: Kondisi pemicu.
        steps: Daftar langkah.
        tools: Tool yang dipakai.
        skills: Skill yang dipakai.
        verification: Cara verifikasi.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if not name.strip() or not trigger.strip() or not steps:
        return json.dumps({"error": "name, trigger, dan steps wajib diisi"}, ensure_ascii=False)

    def _do() -> str:
        procedure_id = f"proc-{uuid.uuid4().hex[:16]}"
        now = _now_iso()
        _ensure_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_procedures
                  (procedure_id, owner, name, trigger, steps_json, tools_json,
                   skills_json, verification, status, metadata_json,
                   created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    procedure_id, owner, name, trigger,
                    json.dumps(steps), json.dumps(tools or []),
                    json.dumps(skills or []), verification, "candidate",
                    json.dumps({"chat_id": chat_id, "sender_id": sender_id}),
                    now, now,
                ),
            )
        return json.dumps({
            "procedure_id": procedure_id,
            "name": name,
            "status": "candidate",
        }, ensure_ascii=False)

    return idempotent_call(
        "memory_procedure_store", idempotency_key,
        {"owner": owner, "name": name, "trigger": trigger},
        _do,
    )[0]


@tool
def memory_promote(
    source_kind: str,
    source_id: str,
    target_kind: str,
    target_id: str = "",
    rationale: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Naikkan tingkatan entry memory: OBSERVATION→CANDIDATE→VERIFIED→PROMOTED.

    Args:
        source_kind: episode|failure|procedure.
        source_id: ID entry sumber.
        target_kind: candidate|verified|procedure|lesson.
        target_id: ID target jika sudah ada.
        rationale: Alasan promosi.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if source_kind not in {"episode", "failure", "procedure", "observation"}:
        return json.dumps({"error": "source_kind tidak dikenal"}, ensure_ascii=False)
    stage = target_kind.upper() if target_kind.upper() in _VALID_PROMOTION_STAGES else "CANDIDATE"
    if source_kind in {"episode", "failure", "procedure"} and not source_id:
        return json.dumps({"error": "source_id wajib diisi"}, ensure_ascii=False)

    def _do() -> str:
        now = _now_iso()
        _ensure_db()
        verdict = "promoted" if stage in {"VERIFIED", "PROMOTED"} else "candidate"
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_promotion_log
                  (source_kind, source_id, candidate_kind, candidate_id,
                   stage, verdict, rationale, owner, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_kind, source_id, target_kind, target_id,
                    stage, verdict, rationale, owner, now,
                ),
            )
            if source_kind == "procedure" and stage in {"VERIFIED", "PROMOTED"}:
                conn.execute(
                    "UPDATE memory_procedures SET status=?, updated_at=? WHERE procedure_id=?",
                    (stage.lower(), now, source_id),
                )
            elif source_kind == "episode" and stage == "PROMOTED":
                conn.execute(
                    "UPDATE memory_episodes SET status=?, updated_at=? WHERE episode_id=?",
                    ("promoted", now, source_id),
                )
        return json.dumps({
            "source_kind": source_kind,
            "source_id": source_id,
            "stage": stage,
            "verdict": verdict,
        }, ensure_ascii=False)

    return idempotent_call(
        "memory_promote", idempotency_key,
        {"source_kind": source_kind, "source_id": source_id, "target_kind": target_kind},
        _do,
    )[0]


@tool
def memory_retire(
    source_kind: str,
    source_id: str,
    rationale: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Turunkan / retire entry memory yang sudah usang atau salah.

    Args:
        source_kind: episode|failure|procedure.
        source_id: ID entry.
        rationale: Alasan retire.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if source_kind not in {"episode", "procedure", "failure"}:
        return json.dumps({"error": "source_kind tidak dikenal"}, ensure_ascii=False)

    def _do() -> str:
        now = _now_iso()
        _ensure_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_promotion_log
                  (source_kind, source_id, candidate_kind, candidate_id,
                   stage, verdict, rationale, owner, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_kind, source_id, "retired", "",
                    "RETIRED", "retired", rationale, owner, now,
                ),
            )
            if source_kind == "procedure":
                conn.execute(
                    "UPDATE memory_procedures SET status='retired', updated_at=? WHERE procedure_id=?",
                    (now, source_id),
                )
            elif source_kind == "episode":
                conn.execute(
                    "UPDATE memory_episodes SET status='retired', updated_at=? WHERE episode_id=?",
                    (now, source_id),
                )
        return json.dumps({"source_kind": source_kind, "source_id": source_id, "verdict": "retired"}, ensure_ascii=False)

    return idempotent_call(
        "memory_retire", idempotency_key,
        {"source_kind": source_kind, "source_id": source_id},
        _do,
    )[0]


@tool
def memory_relevance(
    query: str,
    owner: str = "system",
    episode_limit: int = 5,
    procedure_limit: int = 3,
    failure_limit: int = 3,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Ambil episode + procedure + failure relevan untuk query saat ini.

    Args:
        query: Pertanyaan/tugas saat ini.
        owner: Owner principal.
        episode_limit: Maks episode.
        procedure_limit: Maks procedure.
        failure_limit: Maks failure.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_ep = max(1, min(episode_limit, 25))
    bounded_proc = max(0, min(procedure_limit, 25))
    bounded_fail = max(0, min(failure_limit, 25))
    needle = f"%{query.strip().lower()}%"
    _ensure_db()
    payload: dict[str, Any] = {"query": query, "owner": owner}
    with connect() as conn:
        ep_rows = conn.execute(
            """
            SELECT episode_id, task, intent, outcome, reward, usefulness
              FROM memory_episodes
             WHERE owner=? AND status='active'
               AND (LOWER(task) LIKE ? OR LOWER(intent) LIKE ?)
             ORDER BY reward DESC, usefulness DESC, updated_at DESC
             LIMIT ?
            """,
            (owner, needle, needle, bounded_ep),
        ).fetchall()
        proc_rows = conn.execute(
            """
            SELECT procedure_id, name, trigger, success_count, failure_count, status
              FROM memory_procedures
             WHERE owner=? AND status IN ('candidate','verified','promoted')
               AND (LOWER(name) LIKE ? OR LOWER(trigger) LIKE ?)
             ORDER BY success_count DESC, updated_at DESC
             LIMIT ?
            """,
            (owner, needle, needle, bounded_proc),
        ).fetchall()
        fail_rows = conn.execute(
            """
            SELECT failure_id, failure_class, title, recurrence_count, recovery_success
              FROM memory_failures
             WHERE owner=? AND (LOWER(title) LIKE ? OR LOWER(failure_class) LIKE ?)
             ORDER BY recurrence_count DESC, last_seen_at DESC
             LIMIT ?
            """,
            (owner, needle, needle, bounded_fail),
        ).fetchall()
    payload["episodes"] = [_row_dict(row) for row in ep_rows]
    payload["procedures"] = [_row_dict(row) for row in proc_rows]
    payload["failures"] = [_row_dict(row) for row in fail_rows]
    return json.dumps(payload, ensure_ascii=False)
