from __future__ import annotations

from langchain_core.tools import tool


@tool
async def web_search(query: str, limit: int = 5) -> str:
    """Cari informasi di web.

    Butuh TAVILY_API_KEY atau SERPER_API_KEY di .env.

    Args:
        query: Query pencarian
        limit: Jumlah hasil (default: 5)
    """
    from app.xninetzy.os.research.web_search import web_search as _search
    from app.xninetzy.core.config import get_settings
    s = get_settings()
    if not s.TAVILY_API_KEY and not s.SERPER_API_KEY:
        return "⚠️ Web search tidak aktif. Set TAVILY_API_KEY atau SERPER_API_KEY di .env"

    results = await _search(query, limit)
    if not results:
        return f"Tidak ada hasil untuk '{query}'."

    lines = [f"🌐 *Web Search:* `{query}`\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"*[{i}] {r['title']}*\n{r['url']}\n{r['snippet']}\n")
    return "\n".join(lines)


@tool
async def youtube_search(query: str, limit: int = 5) -> str:
    """Cari video YouTube yang relevan.

    Butuh YOUTUBE_API_KEY di .env.

    Args:
        query: Query pencarian video
        limit: Jumlah hasil (default: 5)
    """
    from app.xninetzy.os.research.youtube_search import youtube_search as _search
    from app.xninetzy.core.config import get_settings
    if not get_settings().YOUTUBE_API_KEY:
        return "⚠️ YouTube search tidak aktif. Set YOUTUBE_API_KEY di .env"

    results = await _search(query, limit)
    if not results:
        return f"Tidak ada video untuk '{query}'."

    lines = [f"📺 *YouTube:* `{query}`\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"*[{i}] {r['title']}*\nChannel: {r['channel']}\n{r['url']}\n{r['description']}\n")
    return "\n".join(lines)


@tool
async def research_light(topic: str, limit: int = 3) -> str:
    """Search ringan yang boleh dipakai semua user."""
    from app.xninetzy.os.research.web_search import web_search as _web
    results = await _web(topic, limit=limit)
    lines = [f"*Research Ringan: {topic}*\n", "*Ringkasan*"]
    if results:
        lines.append("Aku menemukan beberapa sumber awal. Gunakan ini untuk orientasi cepat, bukan riset final.\n")
        lines.append("*Sumber Singkat*")
        for i, result in enumerate(results[:limit], 1):
            lines.append(f"{i}. {result.get('title') or 'Untitled'}")
            if result.get("url"):
                lines.append(f"   {result['url']}")
            if result.get("snippet"):
                lines.append(f"   {result['snippet'][:180]}")
    else:
        lines.append("Provider web search belum aktif atau tidak ada hasil. Set TAVILY_API_KEY/SERPER_API_KEY untuk hasil web.")
    lines.append("\nKalau butuh riset mendalam, minta admin menjalankan:")
    lines.append(f"`/deep-research {topic}`")
    return "\n".join(lines)


@tool
async def research_create_subplans(topic: str, mode: str = "balanced") -> str:
    """Buat sub-plan riset tanpa menjalankan full deep research."""
    from app.xninetzy.os.research.subplanner import format_subplans_for_whatsapp, generate_research_subplans
    subplans = await generate_research_subplans(topic, None, mode)
    return format_subplans_for_whatsapp(topic, subplans)


@tool
async def research_web_collect(query: str, limit: int = 5) -> str:
    """Kumpulkan sumber web untuk query riset."""
    return await web_search.ainvoke({"query": query, "limit": limit})


@tool
async def research_youtube_collect(query: str, limit: int = 5) -> str:
    """Kumpulkan sumber YouTube untuk query riset."""
    return await youtube_search.ainvoke({"query": query, "limit": limit})


@tool
async def research_rank_sources(topic: str, sources: list[dict] | None = None) -> str:
    """Rank sumber riset sederhana berdasarkan relevansi judul/snippet."""
    from app.xninetzy.os.research.deep_research import rank_research_sources
    ranked = rank_research_sources(topic, [], sources or [], "balanced")
    if not ranked:
        return "Belum ada sumber untuk diranking."
    lines = [f"*Ranked Sources: {topic}*"]
    for i, source in enumerate(ranked, 1):
        lines.append(f"{i}. {source.get('title') or 'Untitled'}")
        lines.append(f"   Skor: {source.get('score', 0)}")
    return "\n".join(lines)


@tool
async def research_generate_brief(topic: str) -> str:
    """Buat brief riset kerangka tanpa menyimpan apa pun."""
    from app.xninetzy.os.research.subplanner import generate_research_subplans
    from app.xninetzy.os.research.deep_research import generate_research_brief
    subplans = await generate_research_subplans(topic, None, "balanced")
    return generate_research_brief(topic, subplans, [])


@tool
async def research_save_brief(topic: str, brief: str, chat_id: str = "system") -> str:
    """Buat approval request untuk menyimpan brief riset."""
    from app.xninetzy.os.hitl.approval_service import request_approval
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=None,
        action_type="save_research_to_obsidian",
        title=f"Simpan research: {topic}",
        summary="Menyimpan brief ke Obsidian/Knowledge membutuhkan approval jika impact tinggi.",
        payload={"topic": topic, "brief": brief},
    )
    return f"*Approval Required #{approval_id}*\nSimpan research `{topic}` membutuhkan approval admin.\nBalas `/approve {approval_id}` atau `/reject {approval_id}`."


@tool
async def youtube_learning_search(topic: str, level: str = "beginner", limit: int = 6) -> str:
    """Cari dan susun YouTube learning path untuk topik belajar."""
    from app.xninetzy.os.research.youtube_search import youtube_search as _search
    results = await _search(f"{topic} tutorial {level}", limit=limit)
    return _format_youtube_learning_path(topic, results)


@tool
async def youtube_playlist_finder(topic: str, limit: int = 5) -> str:
    """Cari playlist/tutorial series YouTube untuk topik belajar."""
    return await youtube_learning_search.ainvoke({"topic": f"{topic} playlist series", "limit": limit})


@tool
async def youtube_video_ranker(topic: str, videos: list[dict] | None = None) -> str:
    """Rank video YouTube berdasarkan relevansi ringan."""
    ranked = sorted(videos or [], key=lambda v: topic.lower() in (v.get("title", "").lower()), reverse=True)
    return _format_youtube_learning_path(topic, ranked)


def _format_youtube_learning_path(topic: str, results: list[dict]) -> str:
    lines = [f"*YouTube Learning Path: {topic}*\n"]
    buckets = [
        ("Level 1 - Fundamental", results[:2]),
        ("Level 2 - Praktik", results[2:4]),
        ("Level 3 - Advanced", results[4:6]),
    ]
    if not results:
        lines.append("YouTube API belum aktif atau tidak ada hasil.")
    for title, items in buckets:
        if not items:
            continue
        lines.append(f"*{title}*")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.get('title') or 'Video'}")
            lines.append("   Kenapa ditonton: relevan untuk urutan belajar topik ini.")
            lines.append(f"   Fokus catatan: {item.get('description') or 'Konsep dan praktik utama.'}")
            if item.get("url"):
                lines.append(f"   {item['url']}")
        lines.append("")
    lines.append("*Mau aku jadikan roadmap belajar + task harian?*")
    return "\n".join(lines).strip()


@tool
async def deep_research_topic(
    topic: str,
    chat_id: str = "system",
    sender_id: str | None = None,
    sender_name: str | None = None,
    chat_type: str = "private",
    metadata: dict | None = None,
    mode: str = "balanced",
    include_youtube: bool = True,
    include_academic: bool = False,
) -> str:
    """Lakukan deep research admin-only dengan subplanning, session, dan tanpa auto-save."""
    from app.xninetzy.os.research.deep_research import run_deep_research
    return await run_deep_research(
        topic=topic,
        chat_id=chat_id,
        sender_id=sender_id,
        sender_name=sender_name,
        chat_type=chat_type,
        metadata=metadata,
        mode=mode,
        include_youtube=include_youtube,
        include_academic=include_academic or mode == "quality",
    )
