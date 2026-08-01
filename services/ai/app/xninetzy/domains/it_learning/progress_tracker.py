from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect
from app.xninetzy.domains.it_learning.concept_graph import next_ready_concept


def get_roadmap_progress(roadmap_id: int) -> dict | None:
    with connect() as conn:
        roadmap = conn.execute(
            "SELECT * FROM learning_roadmaps WHERE id=?", (roadmap_id,)
        ).fetchone()
        if not roadmap:
            return None
        tasks = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) AS done
            FROM learning_tasks WHERE roadmap_id=?
            """,
            (roadmap_id,),
        ).fetchone()
        sessions = conn.execute(
            """
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(actual_minutes), 0) AS minutes,
                   AVG(mastery_after) AS average_mastery
            FROM learning_study_sessions
            WHERE roadmap_id=? AND status='completed'
            """,
            (roadmap_id,),
        ).fetchone()
        latest = conn.execute(
            """
            SELECT * FROM learning_study_sessions
            WHERE roadmap_id=? AND status='completed'
            ORDER BY completed_at DESC, id DESC LIMIT 1
            """,
            (roadmap_id,),
        ).fetchone()
        concepts = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN mastery>=0.8 THEN 1 ELSE 0 END) AS mastered,
                   AVG(mastery) AS average_mastery
            FROM learning_concepts WHERE roadmap_id=?
            """,
            (roadmap_id,),
        ).fetchone()
    total = int(tasks["total"] or 0)
    done = int(tasks["done"] or 0)
    return {
        "roadmap": dict(roadmap),
        "task_total": total,
        "task_done": done,
        "task_ratio": done / total if total else 0,
        "session_count": int(sessions["count"] or 0),
        "total_minutes": int(sessions["minutes"] or 0),
        "average_mastery": sessions["average_mastery"],
        "latest_session": dict(latest) if latest else None,
        "concept_total": int(concepts["total"] or 0),
        "concept_mastered": int(concepts["mastered"] or 0),
        "concept_average_mastery": concepts["average_mastery"],
    }


def build_today_plan(
    roadmap_id: int | None = None,
    now: datetime | None = None,
    available_minutes: int | None = None,
    energy: int | None = None,
) -> dict | None:
    timezone = ZoneInfo(get_settings().APP_TIMEZONE)
    current = now or datetime.now(timezone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone)
    else:
        current = current.astimezone(timezone)
    with connect() as conn:
        active = conn.execute(
            """
            SELECT s.*, r.title AS roadmap_title
            FROM learning_study_sessions s
            JOIN learning_roadmaps r ON r.id=s.roadmap_id
            WHERE s.status='active' ORDER BY s.id DESC LIMIT 1
            """
        ).fetchone()
        if active:
            planned_minutes = int(active["planned_minutes"] or 25)
            if available_minutes is not None:
                planned_minutes = min(planned_minutes, max(5, available_minutes))
            return {
                "roadmap_id": active["roadmap_id"],
                "roadmap_title": active["roadmap_title"],
                "mode": "resume",
                "focus": active["objective"],
                "minutes": planned_minutes,
                "reason": f"Sesi #{active['id']} masih aktif.",
                "recall": "Lanjutkan dari titik terakhir dan catat evidence saat selesai.",
                "session_id": active["id"],
                "concept_id": None,
                "recall_card_id": None,
            }
        recall_params: list[object] = [current.isoformat()]
        recall_filter = ""
        if roadmap_id is not None:
            recall_filter = "AND card.roadmap_id=?"
            recall_params.append(roadmap_id)
        due_recall = conn.execute(
            f"""
            SELECT card.*, concept.title AS concept_title,
                   roadmap.title AS roadmap_title
            FROM learning_recall_cards card
            JOIN learning_concepts concept ON concept.id=card.concept_id
            JOIN learning_roadmaps roadmap ON roadmap.id=card.roadmap_id
            WHERE card.status='active' AND card.due_at<=? {recall_filter}
            ORDER BY card.due_at ASC, card.id ASC LIMIT 1
            """,
            recall_params,
        ).fetchone()
        if due_recall:
            recall_minutes = 10
            if available_minutes is not None:
                recall_minutes = min(recall_minutes, max(5, available_minutes))
            return {
                "roadmap_id": due_recall["roadmap_id"],
                "roadmap_title": due_recall["roadmap_title"],
                "mode": "recall",
                "focus": due_recall["question"],
                "minutes": recall_minutes,
                "reason": (
                    f"Recall card #{due_recall['id']} jatuh tempo sejak "
                    f"{due_recall['due_at']}."
                ),
                "recall": (
                    f"Jawab tanpa membuka catatan: /recall answer "
                    f"{due_recall['id']} <confidence 1-5> <jawaban>"
                ),
                "session_id": None,
                "concept_id": due_recall["concept_id"],
                "recall_card_id": due_recall["id"],
            }
        if roadmap_id is None:
            roadmap = conn.execute(
                "SELECT * FROM learning_roadmaps WHERE status='active' ORDER BY updated_at DESC, id DESC LIMIT 1"
            ).fetchone()
        else:
            roadmap = conn.execute(
                "SELECT * FROM learning_roadmaps WHERE id=? AND status='active'",
                (roadmap_id,),
            ).fetchone()
        if not roadmap:
            return None
        concept = next_ready_concept(conn, int(roadmap["id"]))
        pending = None
        if concept:
            pending = conn.execute(
                """
                SELECT task.*
                FROM learning_tasks task
                JOIN learning_concept_tasks link ON link.learning_task_id=task.id
                WHERE task.roadmap_id=? AND task.status!='done' AND link.concept_id=?
                ORDER BY task.day_index, task.id LIMIT 1
                """,
                (roadmap["id"], concept["id"]),
            ).fetchone()
        if pending is None:
            pending = conn.execute(
                "SELECT * FROM learning_tasks WHERE roadmap_id=? AND status!='done' ORDER BY day_index, id LIMIT 1",
                (roadmap["id"],),
            ).fetchone()
        latest = conn.execute(
            """
            SELECT * FROM learning_study_sessions
            WHERE roadmap_id=? AND status='completed'
            ORDER BY completed_at DESC, id DESC LIMIT 1
            """,
            (roadmap["id"],),
        ).fetchone()
    task_focus = pending["title"] if pending else roadmap["target"] or roadmap["topic"]
    focus = f"{task_focus} — {concept['title']}" if concept else task_focus
    concept_reason = (
        f" Konsep siap berikutnya: {concept['title']} ({float(concept['mastery']):.0%})."
        if concept
        else ""
    )
    if not latest:
        start_minutes = 25
        if energy is not None and energy <= 2:
            start_minutes = 15
        if available_minutes is not None:
            start_minutes = min(start_minutes, max(5, available_minutes))
        return {
            "roadmap_id": roadmap["id"],
            "roadmap_title": roadmap["title"],
            "mode": "start",
            "focus": focus,
            "minutes": start_minutes,
            "reason": "Belum ada sesi aktual untuk roadmap ini." + concept_reason,
            "recall": "Tulis apa yang sudah diketahui sebelum membuka materi.",
            "session_id": None,
            "concept_id": int(concept["id"]) if concept else None,
            "recall_card_id": None,
        }
    mastery = float(latest["mastery_after"] or 0)
    effective_energy = energy or latest["energy_after"] or latest["energy_before"] or 3
    minutes = 15 if effective_energy <= 2 else 35 if effective_energy >= 4 else 25
    if available_minutes is not None:
        minutes = min(minutes, max(5, available_minutes))
    if mastery < 0.6:
        mode = "reinforce"
        focus = latest["objective"]
        reason = f"Mastery terakhir {mastery:.0%}; konsep perlu diperkuat."
        recall = (
            "Jelaskan kembali tanpa melihat catatan, lalu ulangi bagian yang gagal."
        )
    elif mastery < 0.8:
        mode = "practice"
        reason = (
            f"Mastery terakhir {mastery:.0%}; lanjutkan dengan latihan terarah."
            + concept_reason
        )
        recall = f"Mulai dengan recall singkat: {latest['objective']}."
    else:
        mode = "advance"
        reason = (
            f"Mastery terakhir {mastery:.0%}; siap maju sambil menjaga recall."
            + concept_reason
        )
        recall = f"Uji ulang satu pertanyaan tentang {latest['objective']} sebelum fokus baru."
    return {
        "roadmap_id": roadmap["id"],
        "roadmap_title": roadmap["title"],
        "mode": mode,
        "focus": focus,
        "minutes": minutes,
        "reason": reason,
        "recall": recall,
        "session_id": None,
        "concept_id": int(concept["id"]) if concept else None,
        "recall_card_id": None,
    }


def get_weekly_learning_summary(roadmap_id: int | None = None) -> dict:
    timezone = ZoneInfo(get_settings().APP_TIMEZONE)
    cutoff = (datetime.now(timezone) - timedelta(days=7)).isoformat()
    conditions = ["status='completed'", "completed_at>=?"]
    params: list[object] = [cutoff]
    if roadmap_id is not None:
        conditions.append("roadmap_id=?")
        params.append(roadmap_id)
    where = " AND ".join(conditions)
    with connect() as conn:
        summary = conn.execute(
            f"""
            SELECT COUNT(*) AS count,
                   COALESCE(SUM(actual_minutes), 0) AS minutes,
                   AVG(mastery_after) AS average_mastery
            FROM learning_study_sessions WHERE {where}
            """,
            params,
        ).fetchone()
        recent = conn.execute(
            f"""
            SELECT objective, mastery_after, actual_minutes
            FROM learning_study_sessions WHERE {where}
            ORDER BY completed_at DESC, id DESC LIMIT 3
            """,
            params,
        ).fetchall()
    return {
        "session_count": int(summary["count"] or 0),
        "total_minutes": int(summary["minutes"] or 0),
        "average_mastery": summary["average_mastery"],
        "recent": [dict(row) for row in recent],
    }
