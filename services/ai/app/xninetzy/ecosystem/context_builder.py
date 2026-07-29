from __future__ import annotations

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


def build_personal_context(chat_id: str, message: str) -> dict:
    """Build a compact personal context dict to enrich the agent's system prompt."""
    context: dict = {
        "active_goals": [],
        "today_tasks": [],
        "urgent_deadlines": [],
        "academic_schedule": [],
        "recent_daily_summary": None,
        "relevant_knowledge": [],
        "active_roadmaps": [],
        "learning_focus": None,
        "habit_status": [],
        "workout_summary": None,
        "recent_events": [],
    }

    try:
        from app.xninetzy.os.life.goal_manager import list_goals

        goals = list_goals(status="active", limit=3)
        context["active_goals"] = [
            f"{g['title']} ({g.get('domain', '?')}, {g.get('horizon', '?')})"
            for g in goals
        ]
    except Exception as e:
        logger.debug("Context: goals fetch failed: %s", e)

    try:
        from app.xninetzy.os.life.task_manager import list_tasks_today

        tasks = list_tasks_today()[:5]
        context["today_tasks"] = [
            f"[{t.get('priority', '?')}] {t['title']}" for t in tasks
        ]
    except Exception as e:
        logger.debug("Context: tasks fetch failed: %s", e)

    try:
        from app.xninetzy.os.academic.hebat.storage import list_assignments

        assigns = [
            a
            for a in list_assignments()
            if a.get("due_at")
            and a.get("submission_status", "").lower() not in ("submitted for grading",)
        ]
        deadlines = []
        for a in assigns[:3]:
            deadlines.append(f"{a['title']} → {a.get('due_at', '?')}")
        context["urgent_deadlines"] = deadlines
    except Exception as e:
        logger.debug("Context: HEBAT deadlines fetch failed: %s", e)

    try:
        from app.xninetzy.core.config import get_settings

        if get_settings().WEB_ANALYSIS_ENCRYPTION_KEY:
            from app.xninetzy.os.web_analysis.snapshot_manager import SnapshotManager

            snapshot = SnapshotManager().load("mahasiswa", "schedule")
            items = (snapshot or {}).get("items") or []
            context["academic_schedule"] = [
                f"{item.get('when') or item.get('start') or '?'} — "
                f"{item.get('label') or item.get('course') or 'Jadwal'}"
                for item in items[:5]
            ]
    except Exception as e:
        logger.debug("Context: local portal schedule fetch failed: %s", e)

    try:
        from app.xninetzy.os.life.journal_manager import get_latest_review

        review = get_latest_review()
        if review:
            context["recent_daily_summary"] = review.get("summary", "")[:200]
    except Exception as e:
        logger.debug("Context: daily review fetch failed: %s", e)

    try:
        from app.xninetzy.domains.it_learning.roadmap_store import (
            list_roadmaps_with_progress,
        )

        roadmaps = list_roadmaps_with_progress(status="active", limit=3)
        context["active_roadmaps"] = [
            f"{r['topic']} ({r.get('completed_tasks') or 0}/{r.get('task_count') or 0} task)"
            for r in roadmaps
        ]
    except Exception as e:
        logger.debug("Context: roadmap fetch failed: %s", e)

    try:
        from app.xninetzy.domains.it_learning.progress_tracker import build_today_plan

        plan = build_today_plan()
        if plan:
            context["learning_focus"] = (
                f"{plan['mode']}: {plan['focus']} ({plan['minutes']} menit)"
            )
    except Exception as e:
        logger.debug("Context: learning focus fetch failed: %s", e)

    try:
        from app.xninetzy.os.life.habit_manager import get_habit_today

        context["habit_status"] = [
            f"{h['name']} {h['done_today']}/{h['target_count']}"
            for h in get_habit_today()[:5]
        ]
    except Exception as e:
        logger.debug("Context: habit fetch failed: %s", e)

    try:
        from app.xninetzy.os.life.workout_manager import get_workout_summary

        workout = get_workout_summary("week")
        context["workout_summary"] = (
            f"{workout['session_count']} sesi, {workout['total_minutes']} menit minggu ini"
        )
    except Exception as e:
        logger.debug("Context: workout fetch failed: %s", e)

    try:
        from app.xninetzy.ecosystem.event_bus import recent_events

        context["recent_events"] = [
            f"{event['event_type']}:{event.get('entity_type') or 'system'}"
            for event in recent_events(limit=5)
        ]
    except Exception as e:
        logger.debug("Context: recent events fetch failed: %s", e)

    try:
        if any(
            kw in message.lower()
            for kw in ["belajar", "materi", "konsep", "jelaskan", "apa itu"]
        ):
            from app.xninetzy.os.knowledge.rag import quick_search

            hits = quick_search(message, limit=3)
            context["relevant_knowledge"] = [h.get("title", "?") for h in hits]
    except Exception as e:
        logger.debug("Context: knowledge search failed: %s", e)

    return context


def format_context_for_prompt(ctx: dict) -> str:
    """Format personal context into a compact string for injection into agent prompt."""
    parts: list[str] = []

    if ctx.get("active_goals"):
        parts.append("Active goals: " + " | ".join(ctx["active_goals"]))

    if ctx.get("today_tasks"):
        parts.append("Today tasks: " + " | ".join(ctx["today_tasks"]))

    if ctx.get("urgent_deadlines"):
        parts.append("Urgent HEBAT deadlines: " + " | ".join(ctx["urgent_deadlines"]))

    if ctx.get("academic_schedule"):
        parts.append("Local academic schedule: " + " | ".join(ctx["academic_schedule"]))

    if ctx.get("recent_daily_summary"):
        parts.append(f"Yesterday summary: {ctx['recent_daily_summary']}")

    if ctx.get("relevant_knowledge"):
        parts.append("Relevant knowledge: " + ", ".join(ctx["relevant_knowledge"]))

    if ctx.get("active_roadmaps"):
        parts.append("Active learning roadmaps: " + " | ".join(ctx["active_roadmaps"]))

    if ctx.get("learning_focus"):
        parts.append("Adaptive learning focus: " + ctx["learning_focus"])

    if ctx.get("habit_status"):
        parts.append("Today habits: " + " | ".join(ctx["habit_status"]))

    if ctx.get("workout_summary"):
        parts.append("Workout: " + ctx["workout_summary"])

    if ctx.get("recent_events"):
        parts.append("Recent OS events: " + " | ".join(ctx["recent_events"]))

    if not parts:
        return ""

    return "\n[Personal Context]\n" + "\n".join(parts) + "\n"
