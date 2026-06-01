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
    from app.research.web_search import web_search as _search
    from app.core.config import get_settings
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
    from app.research.youtube_search import youtube_search as _search
    from app.core.config import get_settings
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
async def deep_research_topic(topic: str, goal: str = "", depth: str = "normal",
                               chat_id: str = "system") -> str:
    """Lakukan riset mendalam tentang suatu topik: knowledge, web, YouTube.

    Simpan hasilnya ke Obsidian dan knowledge base.

    Args:
        topic: Topik yang ingin diriset
        goal: Tujuan riset (opsional)
        depth: normal|deep
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.knowledge.rag import build_rag_context
    from app.research.web_search import web_search as _web
    from app.research.youtube_search import youtube_search as _yt
    from app.knowledge.ingestion import ingest_text
    from app.tools.internal.datetime_info import get_now_info
    from app.ecosystem.event_bus import record_event

    now = get_now_info()
    parts: list[str] = [f"# Research Brief: {topic}\n\n*Tujuan:* {goal or 'General research'}\n*Tanggal:* {now['date']}\n"]

    # Local knowledge
    local_ctx = build_rag_context(topic, top_k=3)
    if local_ctx:
        parts.append("## Dari Knowledge Base\n" + local_ctx)

    # Web search
    web_results = await _web(topic + " tutorial guide", limit=4)
    if web_results:
        parts.append("\n## Sumber Web Terbaik\n")
        for r in web_results[:4]:
            parts.append(f"- [{r['title']}]({r['url']})\n  {r['snippet']}")

    # YouTube
    yt_results = await _yt(topic + " tutorial", limit=3)
    if yt_results:
        parts.append("\n## Video Rekomendasi\n")
        for r in yt_results[:3]:
            parts.append(f"- [{r['title']}]({r['url']}) — {r['channel']}")

    parts.append("\n## Roadmap Belajar\n1. Pahami konsep dasar\n2. Praktik dengan contoh\n3. Bangun mini project\n4. Review dan dokumentasikan")
    parts.append("\n## Pertanyaan Lanjutan\n- Apa prerequisite utama?\n- Apa use case nyatanya?\n- Apa kesalahan umum yang perlu dihindari?")

    full_text = "\n".join(parts)

    # Save to Obsidian
    try:
        from app.obsidian.vault_service import ObsidianVaultService
        obs_path = f"Research/{topic.replace('/', '-')[:40]}/{now['date']}-brief.md"
        note_content = (
            f"---\ntype: research\ntopic: \"{topic}\"\ncreated: {now['date']}\ntags: [research]\n---\n\n"
            + full_text
        )
        ObsidianVaultService().create_note(obs_path, note_content, overwrite=True)
    except Exception:
        obs_path = None

    # Ingest to knowledge
    ingest_text(f"Research: {topic} ({now['date']})", full_text, "research_brief")
    record_event(chat_id, "research_saved", "whatsapp", "research", topic, {"topic": topic})

    # Return WA-formatted summary (truncated)
    summary = f"🔬 *Deep Research: {topic}*\n\n"
    if local_ctx:
        summary += "✅ Found local knowledge\n"
    if web_results:
        summary += f"✅ {len(web_results)} web sources\n"
    if yt_results:
        summary += f"✅ {len(yt_results)} YouTube videos\n"
    if obs_path:
        summary += f"\nDisimpan ke: `{obs_path}`"
    summary += f"\n\nKetik *knowledge_answer {topic}* untuk tanya jawab."
    return summary
