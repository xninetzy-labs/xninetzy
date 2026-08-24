from __future__ import annotations

from langchain_core.tools import tool


@tool
async def web_search(query: str, limit: int = 5) -> str:
    """Cari informasi di web.

    Menggunakan provider berbayar bila tersedia dan DDGS sebagai fallback gratis.

    Args:
        query: Query pencarian
        limit: Jumlah hasil (default: 5)
    """
    from app.xninetzy.os.research.web_search import web_search as _search

    results = await _search(query, limit)
    if not results:
        return f"Tidak ada hasil untuk '{query}'."

    lines = [f"🌐 *Web Search:* `{query}`\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"*[{i}] {r['title']}*\n{r['url']}\n{r['snippet']}\n")
    return "\n".join(lines)


@tool
def research_capabilities() -> dict:
    """Tampilkan status provider Deep Research tanpa membocorkan credential."""
    from app.xninetzy.os.research.web_search import research_capabilities as _capabilities
    return _capabilities()


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
    """Search ringan yang boleh dipakai semua user.

    Menggabungkan web, YouTube, dan paper akademik dalam satu panggilan cepat.
    """
    from app.xninetzy.os.research.light_pipeline import (
        collect_quick_sources,
        group_sources_by_type,
    )

    sources = await collect_quick_sources(topic, limit=int(limit))
    lines = [f"*Research Ringan: {topic}*\n", "*Ringkasan*"]
    if sources:
        lines.append(
            "Sumber awal lintas web, video, dan paper akademik. "
            "Gunakan untuk orientasi cepat, bukan riset final.\n"
        )
        grouped = group_sources_by_type(sources)
        labels = {
            "web": "🌐 *Web*",
            "academic": "🎓 *Paper Akademik*",
            "youtube": "📺 *YouTube*",
        }
        for kind in ("web", "academic", "youtube"):
            items = grouped.get(kind) or []
            if not items:
                continue
            lines.append(labels[kind])
            for i, result in enumerate(items[:limit], 1):
                lines.append(f"{i}. {result.get('title') or 'Untitled'}")
                if result.get("url"):
                    lines.append(f"   {result['url']}")
                snippet = result.get("snippet") or result.get("description") or ""
                if snippet:
                    lines.append(f"   {snippet[:180]}")
            lines.append("")
    else:
        lines.append(
            "Tidak ada sumber yang berhasil dikumpulkan. "
            "Coba ulangi atau gunakan kata kunci lain."
        )
    lines.append("Kalau butuh riset mendalam, minta admin menjalankan:")
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
    """Buat brief riset kerangka dengan sumber nyata (web + paper + video)."""
    from app.xninetzy.os.research.deep_research import generate_research_brief
    from app.xninetzy.os.research.light_pipeline import collect_quick_sources
    from app.xninetzy.os.research.subplanner import generate_research_subplans

    subplans = await generate_research_subplans(topic, None, "balanced")
    sources = await collect_quick_sources(topic, limit=3)
    for subplan in subplans[:2]:
        query = (subplan.search_queries or [None])[0]
        if query and query != topic:
            sources.extend(
                await collect_quick_sources(
                    query, limit=2, include_youtube=False, include_academic=True
                )
            )
    return generate_research_brief(topic, subplans, sources)


@tool
async def research_save_brief(topic: str, brief: str, chat_id: str = "system") -> str:
    """Buat approval request untuk menyimpan brief riset."""
    from app.xninetzy.os.hitl.approval_service import request_approval
    from app.xninetzy.os.notifications.admin_notifier import notify_admin_approval

    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=None,
        action_type="save_research_to_obsidian",
        title=f"Simpan research: {topic}",
        summary="Menyimpan brief ke Obsidian/Knowledge membutuhkan approval jika impact tinggi.",
        payload={"topic": topic, "brief": brief},
    )
    delivered = await notify_admin_approval(
        approval_id,
        "save_research_to_obsidian",
        f"Simpan research: {topic}",
        "Menyimpan brief ke Obsidian/Knowledge membutuhkan approval.",
    )
    status = (
        "Tombol dikirim ke WhatsApp admin."
        if delivered
        else "Pengiriman tombol gagal; periksa ADMIN_JID dan WA Engine."
    )
    return f"*Approval Required #{approval_id}*\n{status}"


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


@tool
async def deep_research_get(session_id: int, chat_id: str = "system") -> str:
    """Ambil status dan hasil satu deep research session berdasarkan ID.

    Args:
        session_id: ID session deep research
        chat_id: Chat pemilik session (diinjeksi server-side untuk MCP)
    """
    from app.xninetzy.os.research.session import get_research_session
    row = get_research_session(int(session_id))
    if not row or row.get("chat_id") != chat_id:
        return f"Session #{session_id} tidak ditemukan untuk chat ini."
    status = row.get("status") or "unknown"
    topic = row.get("topic") or ""
    lines = [f"*Deep Research #{session_id}* — `{status}`", f"Topik: {topic}"]
    brief = row.get("brief")
    if status == "done" and brief:
        lines.append("")
        lines.append(brief)
    elif status == "failed":
        lines.append("Riset gagal. Jalankan ulang dengan deep_research_topic.")
    else:
        lines.append("Riset masih berjalan. Cek lagi sebentar.")
    return "\n".join(lines)


@tool
async def deep_research_list(limit: int = 5, chat_id: str = "system") -> str:
    """Daftar deep research session terbaru untuk chat ini.

    Args:
        limit: Jumlah session (maks 50)
        chat_id: Chat pemilik session (diinjeksi server-side untuk MCP)
    """
    from app.xninetzy.os.research.session import list_research_sessions
    rows = list_research_sessions(chat_id, limit=int(limit))
    if not rows:
        return "Belum ada deep research session di chat ini."
    lines = ["*Deep Research Sessions*"]
    for row in rows:
        lines.append(
            f"#{row['id']} [{row.get('status')}] {row.get('topic') or 'Untitled'} "
            f"({row.get('mode')})"
        )
    return "\n".join(lines)


@tool
async def research_search_papers(
    query: str, sources: str = "arxiv,crossref", max_results: int = 5
) -> str:
    """Cari paper akademik via arXiv dan CrossRef (gratis, tanpa API key).

    Args:
        query: Topik atau kata kunci penelitian
        sources: Sumber dipisah koma: arxiv, crossref
        max_results: Jumlah hasil per sumber (default: 5)
    """
    from app.xninetzy.os.research.academic_search import search_papers

    results = await search_papers(query, sources=sources, max_results=int(max_results))
    if not results:
        return f"Tidak ada paper ditemukan untuk '{query}'."

    lines = [f"🎓 *Paper Search:* `{query}`\n"]
    for i, r in enumerate(results, 1):
        authors = ", ".join(r.get("authors", [])[:3])
        year = r.get("year") or "?"
        ident = r.get("identifier", "")
        lines.append(
            f"*[{i}] {r['title']}* ({r['identifier_kind']}: `{ident}`, {year})\n"
            f"{authors}\n{r['url']}\n{r['snippet']}\n"
        )
    return "\n".join(lines)


@tool
async def research_get_paper(
    identifier: str,
    source: str = "auto",
    ingest: bool = False,
    chat_id: str = "system",
) -> str:
    """Ambil detail satu paper dari DOI atau ID/URL arXiv.

    Args:
        identifier: DOI (10.xxxx/...), ID arXiv (2401.12345), atau URL keduanya
        source: auto|doi|arxiv (default: auto-deteksi)
        ingest: True untuk menyimpan metadata+abstrak ke knowledge base
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.research.academic_search import get_paper

    paper = await get_paper(identifier, source=source)
    if paper.get("status") != "ok":
        return f"❌ {paper.get('error', 'Paper gagal diambil.')}"

    authors = ", ".join(paper.get("authors", [])[:6])
    lines = [
        f"📄 *{paper['title']}*\n"
        f"Penulis: {authors}\n"
        f"Tahun: {paper.get('year') or '?'} | Jenis: {paper.get('identifier_kind')}\n"
        f"ID: `{paper.get('identifier')}`\n"
        f"URL: {paper.get('url')}"
    ]
    if paper.get("container"):
        lines.append(f"Publikasi: {paper['container']}")
    abstract = paper.get("abstract") or paper.get("snippet") or ""
    if abstract:
        lines.append(f"\nAbstrak: {abstract[:800]}")

    if ingest and abstract:
        from app.xninetzy.os.knowledge.ingestion import ingest_text

        result = ingest_text(
            title=paper["title"],
            text=f"{paper['title']}\n\n{abstract}",
            source_type="web_article",
            uri=paper.get("url"),
        )
        lines.append(f"\n📚 Knowledge base: {result.get('status')} (ID `{result.get('source_id', '?')}`)")

    return "\n".join(lines)


@tool
async def research_download_paper(identifier: str, source: str = "auto") -> str:
    """Unduh PDF paper yang open-access secara legal (arXiv / tautan OA CrossRef).

    Sci-Hub sengaja tidak didukung.

    Args:
        identifier: DOI, ID arXiv, atau URL keduanya
        source: auto|doi|arxiv (default: auto-deteksi)
    """
    from app.xninetzy.os.research.academic_search import download_paper_pdf

    result = await download_paper_pdf(identifier, source=source)
    if result["status"] == "downloaded":
        return (
            f"✅ PDF tersimpan: `{result['path']}`\n"
            f"*{result.get('title', '')}* ({result['bytes'] // 1024} KB)\n"
            f"Sumber: {result.get('source_url')}"
        )
    return f"❌ {result.get('error', 'Unduhan gagal.')}"
