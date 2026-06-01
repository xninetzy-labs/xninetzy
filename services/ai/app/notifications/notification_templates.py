from __future__ import annotations


def format_admin_notification(event_type: str, payload: dict) -> str:
    if event_type == "deep_research_started":
        return (
            "*Deep Research Started*\n"
            f"Requester: {payload.get('requester_name') or '-'}\n"
            f"Topic: {payload.get('topic') or '-'}\n"
            f"Mode: {payload.get('mode') or 'balanced'}\n"
            f"Chat: {payload.get('chat_type') or '-'}"
        )
    if event_type == "deep_research_plan_created":
        lines = [f"*Research Plan Created*\nTopic: {payload.get('topic') or '-'}", "Sub-plan:"]
        for i, title in enumerate(payload.get("subplans") or [], 1):
            lines.append(f"{i}. {title}")
        return "\n".join(lines)
    if event_type == "deep_research_done":
        return (
            "*Deep Research Done*\n"
            f"Topic: {payload.get('topic') or '-'}\n"
            f"Sub-plan: {payload.get('subplan_count', 0)}\n"
            f"Sources collected: {payload.get('sources_collected', 0)}\n"
            f"Sources selected: {payload.get('sources_selected', 0)}\n"
            "Status: brief ready\n\n"
            "Butuh approval jika ingin:\n"
            "• simpan ke Obsidian\n"
            "• ingest ke Knowledge\n"
            "• buat roadmap\n"
            "• buat banyak task\n"
            "• link ke Graph RAG"
        )
    return f"*Xninetzy Progress*\nEvent: {event_type}\nStatus: {payload.get('status') or '-'}"
