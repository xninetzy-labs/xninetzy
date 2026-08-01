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
    if event_type == "krs_watcher_change":
        return (
            "*KRS Watcher — Perubahan Terdeteksi*\n"
            f"Jadwal: {payload.get('announcement') or 'belum ada pengumuman'}\n"
            f"MK terambil: {payload.get('mk_count', 0)}\n"
            f"Dalam jendela buka: {'ya' if payload.get('in_window') else 'tidak'}"
        )
    if event_type == "krs_watcher_session_expired":
        return (
            "*KRS Watcher — Sesi Kedaluwarsa*\n"
            f"{payload.get('detail') or '-'}"
        )
    if event_type == "krs_war_started":
        return (
            "*KRS War — Dimulai*\n"
            f"Window: {payload.get('window') or '-'}\n"
            f"MK dalam plan: {payload.get('courses') or payload.get('mk_count') or 0}\n"
            f"Semester: {payload.get('semester') or '-'}"
        )
    if event_type == "krs_war_taken":
        return (
            "*KRS War — Selesai*\n"
            f"Window: {payload.get('window') or '-'}\n"
            f"Diambil: {payload.get('taken', 0)}\n"
            f"Sudah terambil: {payload.get('already_taken', 0)}\n"
            f"Dilewati: {payload.get('skipped', 0)}\n"
            f"Ringkasan: {payload.get('summary') or '-'}"
        )
    if event_type == "krs_war_error":
        return (
            "*KRS War — Error*\n"
            f"Window: {payload.get('window') or '-'}\n"
            f"Detail: {payload.get('error') or payload.get('detail') or '-'}"
        )
    if event_type == "krs_war_calibrated":
        return (
            "*KRS War Kalibrasi*\n"
            f"Window: {payload.get('window') or '-'}\n"
            f"Strategi: {payload.get('strategy') or 'none'}\n"
            f"Target ditemukan: {payload.get('target_count', 0)} MK\n"
            f"Status: {payload.get('status') or '-'}"
        )
    return f"*Xninetzy Progress*\nEvent: {event_type}\nStatus: {payload.get('status') or '-'}"
