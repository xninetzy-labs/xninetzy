from __future__ import annotations

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


def build_personal_context(chat_id: str, message: str) -> dict:
    """Build a compact personal context dict to enrich the agent's system prompt."""
    context: dict = {
        "active_goals": [],
        "today_tasks": [],
        "urgent_deadlines": [],
        "recent_daily_summary": None,
        "relevant_knowledge": [],
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
            f"[{t.get('priority', '?')}] {t['title']}"
            for t in tasks
        ]
    except Exception as e:
        logger.debug("Context: tasks fetch failed: %s", e)

    try:
        from app.xninetzy.os.academic.hebat.storage import list_assignments
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from app.xninetzy.core.config import get_settings
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
        soon = now + timedelta(days=3)
        assigns = [
            a for a in list_assignments()
            if a.get("due_at") and a.get("submission_status", "").lower() not in ("submitted for grading",)
        ]
        deadlines = []
        for a in assigns[:3]:
            deadlines.append(f"{a['title']} → {a.get('due_at', '?')}")
        context["urgent_deadlines"] = deadlines
    except Exception as e:
        logger.debug("Context: HEBAT deadlines fetch failed: %s", e)

    try:
        from app.xninetzy.os.life.journal_manager import get_latest_review
        review = get_latest_review()
        if review:
            context["recent_daily_summary"] = review.get("summary", "")[:200]
    except Exception as e:
        logger.debug("Context: daily review fetch failed: %s", e)

    try:
        if any(kw in message.lower() for kw in ["belajar", "materi", "konsep", "jelaskan", "apa itu"]):
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

    if ctx.get("recent_daily_summary"):
        parts.append(f"Yesterday summary: {ctx['recent_daily_summary']}")

    if ctx.get("relevant_knowledge"):
        parts.append("Relevant knowledge: " + ", ".join(ctx["relevant_knowledge"]))

    if not parts:
        return ""

    return "\n[Personal Context]\n" + "\n".join(parts) + "\n"
