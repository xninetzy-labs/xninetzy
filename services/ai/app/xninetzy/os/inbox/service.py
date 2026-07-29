from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.ecosystem.event_bus import (
    dispatch_recorded_event,
    record_event_in_transaction,
)


class CaptureKind(StrEnum):
    TASK = "task"
    LEARNING = "learning"
    IDEA = "idea"
    NOTE = "note"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class CaptureStatus(StrEnum):
    INBOX = "inbox"
    PROCESSED = "processed"
    ARCHIVED = "archived"


KINDS = {kind.value for kind in CaptureKind}
STATUSES = {status.value for status in CaptureStatus}
PRIORITIES = {"low", "medium", "high", "critical"}
PRIORITY_SCORE = {"low": 15, "medium": 35, "high": 65, "critical": 95}


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))


def _clean_content(content: str) -> str:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Capture tidak boleh kosong.")
    if len(cleaned) > 4000:
        raise ValueError("Capture maksimal 4000 karakter.")
    return cleaned


def _title(content: str) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    return compact[:120]


def infer_capture_kind(content: str) -> str:
    """Klasifikasikan capture secara deterministik tanpa panggilan LLM."""
    value = content.casefold()
    if re.search(r"https?://|www\.", value):
        return CaptureKind.REFERENCE.value
    if any(
        token in value
        for token in (
            "kerjakan",
            "tugas",
            "todo",
            "to-do",
            "deadline",
            "ingatkan",
            "harus ",
        )
    ):
        return CaptureKind.TASK.value
    if any(
        token in value
        for token in (
            "belajar",
            "pelajari",
            "latihan",
            "materi",
            "pahami",
            "roadmap",
        )
    ):
        return CaptureKind.LEARNING.value
    if any(
        token in value
        for token in ("ide ", "gimana kalau", "bagaimana kalau", "coba buat", "mungkin buat")
    ):
        return CaptureKind.IDEA.value
    if len(value.split()) <= 2:
        return CaptureKind.UNKNOWN.value
    return CaptureKind.NOTE.value


def _capture_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        return uuid.uuid4().hex
    normalized = idempotency_key.strip()
    if not normalized:
        return uuid.uuid4().hex
    return hashlib.sha256(f"os-capture:{normalized}".encode()).hexdigest()


def capture_item(
    content: str,
    *,
    kind: str = "auto",
    chat_id: str = "system",
    idempotency_key: str | None = None,
) -> tuple[dict, bool]:
    """Simpan input ambigu ke inbox instalasi dengan optional idempotency key."""
    init_db()
    cleaned = _clean_content(content)
    resolved_kind = infer_capture_kind(cleaned) if kind == "auto" else kind.casefold()
    if resolved_kind not in KINDS:
        raise ValueError("Kind harus task, learning, idea, note, reference, unknown, atau auto.")
    key = _capture_key(idempotency_key)
    now = _now().isoformat()
    created = False
    event_id: int | None = None
    with connect() as conn:
        result = conn.execute(
            """
            INSERT OR IGNORE INTO os_inbox_items
              (capture_key, chat_id, content, title, inferred_kind, status,
               metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,'inbox','{}',?,?)
            """,
            (key, chat_id, cleaned, _title(cleaned), resolved_kind, now, now),
        )
        created = result.rowcount > 0
        row = conn.execute(
            "SELECT * FROM os_inbox_items WHERE capture_key=?", (key,)
        ).fetchone()
        if created and row:
            event_id = record_event_in_transaction(
                conn,
                chat_id,
                "os_capture_created",
                "os_inbox",
                "os_capture",
                str(row["id"]),
                {"kind": resolved_kind},
                now,
            )
    if not row:
        raise RuntimeError("Capture gagal disimpan.")
    item = dict(row)
    if not created and (
        item["content"] != cleaned or item["inferred_kind"] != resolved_kind
    ):
        raise ValueError("Idempotency key sudah dipakai untuk capture berbeda.")
    if event_id is not None:
        dispatch_recorded_event(event_id)
    return item, created


def list_captures(status: str = "inbox", limit: int = 20) -> list[dict]:
    """List capture installation-global berdasarkan status."""
    init_db()
    normalized = status.casefold()
    if normalized != "all" and normalized not in STATUSES:
        raise ValueError("Status harus inbox, processed, archived, atau all.")
    bounded = min(max(int(limit), 1), 50)
    with connect() as conn:
        if normalized == "all":
            rows = conn.execute(
                "SELECT * FROM os_inbox_items ORDER BY id DESC LIMIT ?", (bounded,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM os_inbox_items WHERE status=? ORDER BY id ASC LIMIT ?",
                (normalized, bounded),
            ).fetchall()
    return [dict(row) for row in rows]


def capture_summary() -> dict:
    """Ringkas jumlah item inbox per status dan kind."""
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT status, inferred_kind, COUNT(*) AS total
            FROM os_inbox_items GROUP BY status, inferred_kind
            """
        ).fetchall()
    summary = {"inbox": 0, "processed": 0, "archived": 0, "by_kind": {}}
    for row in rows:
        summary[row["status"]] = summary.get(row["status"], 0) + row["total"]
        if row["status"] == CaptureStatus.INBOX.value:
            summary["by_kind"][row["inferred_kind"]] = row["total"]
    return summary


def triage_capture(
    capture_id: int,
    *,
    target: str = "task",
    priority: str = "medium",
    due_at: str | None = None,
    chat_id: str = "system",
) -> dict:
    """Promosikan capture ke task atau archive secara atomik dan replay-safe."""
    init_db()
    normalized_target = target.casefold()
    normalized_priority = priority.casefold()
    if normalized_target not in {"task", "archive"}:
        raise ValueError("Target triage harus task atau archive.")
    if normalized_priority not in PRIORITIES:
        raise ValueError("Priority harus low, medium, high, atau critical.")
    now = _now().isoformat()
    event_id: int | None = None
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM os_inbox_items WHERE id=?", (capture_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Capture #{capture_id} tidak ditemukan.")
        item = dict(row)
        if item["status"] != CaptureStatus.INBOX.value:
            return {**item, "replayed": True}
        if normalized_target == "archive":
            conn.execute(
                """
                UPDATE os_inbox_items
                SET status='archived', target_type='archive', processed_at=?, updated_at=?
                WHERE id=? AND status='inbox'
                """,
                (now, now, capture_id),
            )
            target_id = None
            status = CaptureStatus.ARCHIVED.value
        else:
            domain = (
                "learning"
                if item["inferred_kind"] == CaptureKind.LEARNING.value
                else "personal"
            )
            task = conn.execute(
                """
                INSERT INTO tasks
                  (title, description, status, priority, domain, due_at, source,
                   created_at, updated_at)
                VALUES (?,?, 'inbox', ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["title"],
                    item["content"],
                    normalized_priority,
                    domain,
                    due_at,
                    f"os_capture:{capture_id}",
                    now,
                    now,
                ),
            )
            target_id = int(task.lastrowid)
            conn.execute(
                """
                INSERT INTO entity_links
                  (chat_id, source_type, source_id, relation, target_type,
                   target_id, metadata_json, created_at)
                VALUES (?, 'os_capture', ?, 'promoted_to', 'task', ?, ?, ?)
                """,
                (
                    chat_id,
                    str(capture_id),
                    str(target_id),
                    json.dumps({"kind": item["inferred_kind"]}),
                    now,
                ),
            )
            conn.execute(
                """
                UPDATE os_inbox_items
                SET status='processed', target_type='task', target_id=?,
                    processed_at=?, updated_at=?
                WHERE id=? AND status='inbox'
                """,
                (str(target_id), now, now, capture_id),
            )
            status = CaptureStatus.PROCESSED.value
        event_type = (
            "os_capture_archived"
            if normalized_target == "archive"
            else "os_capture_promoted"
        )
        event_id = record_event_in_transaction(
            conn,
            chat_id,
            event_type,
            "os_inbox",
            "os_capture",
            str(capture_id),
            {"target": normalized_target, "target_id": target_id},
            now,
        )
    if event_id is not None:
        dispatch_recorded_event(event_id)
    return {
        **item,
        "status": status,
        "target_type": normalized_target,
        "target_id": str(target_id) if target_id is not None else None,
        "replayed": False,
    }


def _parse_due(value: str | None, timezone: ZoneInfo) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone) if parsed.tzinfo is None else parsed.astimezone(timezone)


def build_attention_queue(limit: int = 5, now: datetime | None = None) -> list[dict]:
    """Bangun queue fokus deterministik dari task, learning state, dan OS inbox."""
    init_db()
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo(get_settings().APP_TIMEZONE))
    bounded = min(max(int(limit), 1), 10)
    items: list[dict] = []
    with connect() as conn:
        tasks = conn.execute(
            """
            SELECT * FROM tasks WHERE status NOT IN ('done','cancelled')
            ORDER BY id ASC LIMIT 100
            """
        ).fetchall()
        captures = conn.execute(
            "SELECT * FROM os_inbox_items WHERE status='inbox' ORDER BY id ASC LIMIT 50"
        ).fetchall()
    task_titles: set[str] = set()
    for row in tasks:
        task = dict(row)
        title_key = task["title"].casefold().strip()
        task_titles.add(title_key)
        priority = task.get("priority") or "medium"
        score = PRIORITY_SCORE.get(priority, PRIORITY_SCORE["medium"])
        reasons = [f"priority {priority}"]
        due = _parse_due(task.get("due_at"), current.tzinfo)
        if due:
            days = (due.date() - current.date()).days
            if days < 0:
                score += 120
                reasons.append(f"overdue {abs(days)} hari")
            elif days == 0:
                score += 100
                reasons.append("due hari ini")
            elif days <= 3:
                score += 60 - (days * 10)
                reasons.append(f"due {days} hari lagi")
        if task.get("status") == "next":
            score += 15
            reasons.append("sudah dipilih sebagai next")
        items.append(
            {
                "kind": "task",
                "id": int(task["id"]),
                "title": task["title"],
                "score": score,
                "reason": ", ".join(reasons),
                "action": f"Selesaikan task #{task['id']}",
            }
        )
    try:
        from app.xninetzy.domains.it_learning.progress_tracker import build_today_plan

        plan = build_today_plan(now=current)
    except Exception:
        plan = None
    if plan and plan["focus"].casefold().strip() not in task_titles:
        is_recall = plan["mode"] == "recall"
        items.append(
            {
                "kind": "recall" if is_recall else "learning",
                "id": int(plan.get("recall_card_id") or plan["roadmap_id"]),
                "title": plan["focus"],
                "score": 75 if is_recall else 60 if plan["mode"] == "resume" else 50,
                "reason": plan["reason"],
                "action": (
                    f"Jawab recall card #{plan['recall_card_id']}"
                    if is_recall
                    else f"Mulai sesi belajar {plan['minutes']} menit"
                ),
            }
        )
    for position, row in enumerate(captures):
        capture = dict(row)
        base = {
            "task": 45,
            "learning": 42,
            "unknown": 40,
            "idea": 32,
            "note": 28,
            "reference": 25,
        }.get(capture["inferred_kind"], 25)
        items.append(
            {
                "kind": "capture",
                "id": int(capture["id"]),
                "title": capture["title"],
                "score": base + max(0, 10 - position),
                "reason": f"belum ditriage ({capture['inferred_kind']})",
                "action": f"Triage capture #{capture['id']}",
            }
        )
    items.sort(key=lambda item: (-item["score"], item["kind"], item["id"]))
    return items[:bounded]
