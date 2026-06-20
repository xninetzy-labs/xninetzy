from __future__ import annotations

from app.xninetzy.os.notifications.admin_notifier import notify_admin
from app.xninetzy.os.research.actions.base import ResearchActionInput
from app.xninetzy.os.research.actions.registry import ResearchActionRegistry
from app.xninetzy.os.research.permissions import can_run_deep_research, deep_research_denied_message
from app.xninetzy.os.research.session import (
    add_sources,
    add_substep,
    create_research_session,
    fail_session,
    finish_session,
    set_plan,
    update_substep_status,
)
from app.xninetzy.os.research.subplanner import ResearchSubPlan


MODE_LIMITS = {
    "speed": {"selected": 5, "query_limit": 3, "per_query": 2},
    "balanced": {"selected": 8, "query_limit": 8, "per_query": 3},
    "quality": {"selected": 12, "query_limit": 12, "per_query": 4},
}


def _limits(mode: str) -> dict:
    return MODE_LIMITS.get(mode, MODE_LIMITS["balanced"])


def rank_research_sources(topic: str, subplans: list[ResearchSubPlan], sources: list[dict], mode: str) -> list[dict]:
    seen: set[str] = set()
    ranked: list[dict] = []
    topic_words = {w.lower() for w in topic.split() if len(w) > 2}
    for source in sources:
        url = source.get("url") or source.get("video_id") or source.get("title")
        if not url or url in seen:
            continue
        seen.add(url)
        text = f"{source.get('title','')} {source.get('snippet','')} {source.get('description','')}".lower()
        score = sum(1 for word in topic_words if word in text)
        if source.get("source_type") == "youtube":
            score += 1
        ranked.append({**source, "score": score, "why": "Relevan dengan fokus riset dan cocok sebagai sumber belajar."})
    ranked.sort(key=lambda item: item.get("score", 0), reverse=True)
    return ranked[: _limits(mode)["selected"]]


def generate_research_brief(topic: str, subplans: list[ResearchSubPlan], sources: list[dict]) -> str:
    web_sources = [s for s in sources if s.get("source_type") != "youtube"]
    youtube_sources = [s for s in sources if s.get("source_type") == "youtube"]
    lines = [f"*Deep Research Brief: {topic}*\n"]
    lines.append("*1. Tujuan*")
    lines.append(f"Memetakan {topic} menjadi konsep, sumber belajar, risiko, dan langkah implementasi MVP.\n")
    lines.append("*2. Sub-Plan Riset*")
    for i, subplan in enumerate(subplans, 1):
        lines.append(f"{i}. {subplan.title}")
        lines.append(f"   Fokus: {subplan.question}")
    lines.append("\n*3. Temuan Utama*")
    lines.append("• Mulai dari konsep inti sebelum memilih tools.")
    lines.append("• Pisahkan research, knowledge storage, roadmap, dan approval agar aman.")
    lines.append("• Untuk Xninetzy, MVP terbaik adalah SQLite-first dan WhatsApp-first.\n")
    lines.append("*4. Ringkasan per Sub-Plan*")
    for i, subplan in enumerate(subplans, 1):
        lines.append(f"*Sub-plan {i} - {subplan.title}*")
        lines.append(f"• {subplan.expected_output}")
    lines.append("\n*5. Sumber Terpilih*")
    if web_sources:
        for i, source in enumerate(web_sources[:8], 1):
            lines.append(f"{i}. {source.get('title') or 'Untitled'}")
            if source.get("url"):
                lines.append(f"   {source['url']}")
            lines.append(f"   Kenapa penting: {source.get('why')}")
    else:
        lines.append("Belum ada sumber web karena provider search belum aktif atau tidak mengembalikan hasil.")
    lines.append("\n*6. YouTube Learning Path*")
    if youtube_sources:
        for i, source in enumerate(youtube_sources[:6], 1):
            lines.append(f"{i}. {source.get('title') or 'Video'}")
            lines.append(f"   Fokus: {source.get('description') or 'Belajar bertahap dari video ini.'}")
            if source.get("url"):
                lines.append(f"   {source['url']}")
    else:
        lines.append("Belum ada video karena YouTube API belum aktif atau tidak mengembalikan hasil.")
    lines.append("\n*7. Rekomendasi Belajar*")
    lines.append("• Mulai dari definisi dan arsitektur.")
    lines.append("• Praktikkan dengan mini project kecil.")
    lines.append("• Simpan catatan penting ke Obsidian setelah approval.\n")
    lines.append("*8. Graph RAG Draft*")
    lines.append("Node yang disarankan:")
    lines.append(f"• topic: {topic}")
    lines.append("• concept: konsep dasar, arsitektur, MVP")
    lines.append("• source: sumber web/video terpilih")
    lines.append("Edge:")
    lines.append("• topic related_to concept")
    lines.append("• research_brief references source")
    lines.append("• roadmap created_from research_brief\n")
    lines.append("*9. Next Action*")
    lines.append("Balas:")
    lines.append("• `simpan ke obsidian`")
    lines.append("• `buat roadmap`")
    lines.append("• `ingest ke knowledge`")
    lines.append("• `hubungkan ke graph`")
    return "\n".join(lines)


async def run_deep_research(
    topic: str,
    chat_id: str,
    sender_id: str | None,
    sender_name: str | None,
    chat_type: str,
    metadata: dict | None,
    mode: str = "balanced",
    include_youtube: bool = True,
    include_academic: bool = False,
) -> str:
    mode = mode if mode in MODE_LIMITS else "balanced"
    allowed, reason = can_run_deep_research(sender_id, sender_name, chat_type, metadata)
    if not allowed:
        return deep_research_denied_message(reason)

    session_id = create_research_session(chat_id, topic, sender_id, sender_name, mode)
    await notify_admin(
        "deep_research_started",
        {"requester_name": sender_name, "topic": topic, "mode": mode, "chat_type": chat_type},
        "medium",
    )
    try:
        plan_step = add_substep(session_id, "planning", "Membuat rencana riset", topic)
        plan_action = ResearchActionRegistry.get("plan")
        plan = await plan_action.execute(ResearchActionInput(session_id=session_id, topic=topic, mode=mode)) if plan_action else None
        update_substep_status(session_id, plan_step, "done", plan.data if plan else {})

        sub_step = add_substep(session_id, "subplanning", "Memecah topik menjadi sub-plan")
        sub_action = ResearchActionRegistry.get("subplan")
        sub_result = await sub_action.execute(
            ResearchActionInput(
                session_id=session_id,
                topic=topic,
                mode=mode,
                config={"scope": (plan.data or {}).get("scope") if plan else None},
            )
        )
        subplans = [ResearchSubPlan(**item) for item in sub_result.data["subplans"]]
        set_plan(session_id, [sp.model_dump() for sp in subplans])
        update_substep_status(session_id, sub_step, "done", {"count": len(subplans)})
        await notify_admin(
            "deep_research_plan_created",
            {"topic": topic, "subplans": [sp.title for sp in subplans]},
            "medium",
        )

        all_sources: list[dict] = []
        query_count = 0
        limits = _limits(mode)
        web_action = ResearchActionRegistry.get("web_search")
        yt_action = ResearchActionRegistry.get("youtube_search")
        academic_action = ResearchActionRegistry.get("academic_search")

        for subplan in subplans:
            search_step = add_substep(session_id, "web_searching", subplan.title, payload={"queries": subplan.search_queries})
            for query in subplan.search_queries:
                if query_count >= limits["query_limit"]:
                    break
                query_count += 1
                if web_action:
                    out = await web_action.execute(
                        ResearchActionInput(
                            session_id=session_id,
                            topic=topic,
                            query=query,
                            mode=mode,
                            config={"limit": limits["per_query"]},
                        )
                    )
                    all_sources.extend(out.data.get("sources", []))
                if include_youtube and yt_action and query_count <= 3:
                    out = await yt_action.execute(
                        ResearchActionInput(
                            session_id=session_id,
                            topic=topic,
                            query=f"{query} tutorial",
                            mode=mode,
                            config={"limit": 2, "include_youtube": True},
                        )
                    )
                    all_sources.extend(out.data.get("sources", []))
                if include_academic and academic_action and mode == "quality" and query_count == 1:
                    out = await academic_action.execute(
                        ResearchActionInput(
                            session_id=session_id,
                            topic=topic,
                            query=query,
                            mode=mode,
                            config={"include_academic": True},
                        )
                    )
                    all_sources.extend(out.data.get("sources", []))
            update_substep_status(session_id, search_step, "done")

        add_sources(session_id, all_sources)
        rank_step = add_substep(session_id, "source_ranking", "Ranking dan deduplikasi sumber")
        ranked = rank_research_sources(topic, subplans, all_sources, mode)
        update_substep_status(session_id, rank_step, "done", {"selected": len(ranked)})
        brief_step = add_substep(session_id, "brief_writing", "Menulis research brief")
        brief = generate_research_brief(topic, subplans, ranked)
        update_substep_status(session_id, brief_step, "done")
        done_step = add_substep(session_id, "done", "Riset selesai")
        update_substep_status(session_id, done_step, "done")
        finish_session(session_id, brief)
        await notify_admin(
            "deep_research_done",
            {
                "topic": topic,
                "subplan_count": len(subplans),
                "sources_collected": len(all_sources),
                "sources_selected": len(ranked),
            },
            "medium",
        )
        return brief
    except Exception as exc:
        fail_session(session_id, str(exc))
        await notify_admin("deep_research_failed", {"topic": topic, "status": str(exc)}, "critical")
        return f"⚠️ Deep research gagal: {exc}"
