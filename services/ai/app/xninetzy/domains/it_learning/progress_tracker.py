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


def build_today_plan(roadmap_id: int | None = None) -> dict | None:
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
            return {
                "roadmap_id": active["roadmap_id"],
                "roadmap_title": active["roadmap_title"],
                "mode": "resume",
                "focus": active["objective"],
                "minutes": active["planned_minutes"],
                "reason": f"Sesi #{active['id']} masih aktif.",
                "recall": "Lanjutkan dari titik terakhir dan catat evidence saat selesai.",
                "session_id": active["id"],
                "concept_id": None,
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
        concept = next_ready_concept(conn, int(roadmap["id"]))
    task_focus = pending["title"] if pending else roadmap["target"] or roadmap["topic"]
    focus = f"{task_focus} — {concept['title']}" if concept else task_focus
    concept_reason = (
        f" Konsep siap berikutnya: {concept['title']} ({float(concept['mastery']):.0%})."
        if concept
        else ""
    )
    if not latest:
        return {
            "roadmap_id": roadmap["id"],
            "roadmap_title": roadmap["title"],
            "mode": "start",
            "focus": focus,
            "minutes": 25,
            "reason": "Belum ada sesi aktual untuk roadmap ini." + concept_reason,
            "recall": "Tulis apa yang sudah diketahui sebelum membuka materi.",
            "session_id": None,
            "concept_id": int(concept["id"]) if concept else None,
        }
    mastery = float(latest["mastery_after"] or 0)
    energy = latest["energy_after"] or latest["energy_before"] or 3
    minutes = 15 if energy <= 2 else 35 if energy >= 4 else 25
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
