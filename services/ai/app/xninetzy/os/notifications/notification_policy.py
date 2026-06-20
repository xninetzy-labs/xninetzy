from __future__ import annotations


ADMIN_EVENTS = {
    "deep_research_started",
    "deep_research_plan_created",
    "deep_research_done",
    "deep_research_failed",
    "deep_research_needs_approval",
    "hebat_login_debug_done",
    "hebat_login_debug_failed",
    "roadmap_draft_created",
    "roadmap_needs_approval",
    "knowledge_ingest_needs_approval",
}


def should_notify_admin(event_type: str, impact: str) -> bool:
    if event_type == "deep_research_denied":
        return impact in {"high", "critical"}
    if event_type == "deep_research_source_collected":
        return False
    if event_type == "deep_research_substep_started":
        return impact in {"high", "critical"}
    return event_type in ADMIN_EVENTS or impact in {"high", "critical"}


def should_notify_chat(event_type: str, chat_type: str, requester_is_admin: bool) -> bool:
    if event_type in {"deep_research_done", "deep_research_failed", "deep_research_needs_approval"}:
        return True
    if event_type == "deep_research_started":
        return requester_is_admin and chat_type == "private"
    return False
