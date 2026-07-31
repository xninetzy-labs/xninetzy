from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.academic.qa_portal.automation import (
    QaPortalError,
    fill_all_questionnaires,
    list_questionnaires,
)


@tool
async def qa_list_kuesioner() -> str:
    """Daftar kuesioner QA (qa.unair.ac.id) untuk owner beserta kode dan link isinya."""
    try:
        entries = await list_questionnaires()
    except QaPortalError as exc:
        return f"Gagal mengambil daftar kuesioner QA: {exc}"
    if not entries:
        return "Tidak ada kuesioner QA yang tersedia."
    return "\n".join(f"{e['code']} — {e['title']}" for e in entries)


@tool
async def qa_fill_kuesioner(score: int = 10) -> str:
    """Isi semua kuesioner QA (qa.unair.ac.id) dengan skor yang diminta (default 10)."""
    if not 1 <= score <= 10:
        return "Skor harus antara 1 sampai 10."
    try:
        result = await fill_all_questionnaires(score=score)
    except QaPortalError as exc:
        return f"Gagal mengisi kuesioner QA: {exc}"
    lines = [f"Skor: {result['score']}"]
    for item in result["results"]:
        if "error" in item:
            lines.append(f"{item['code']} — ERROR: {item['error']}")
        else:
            sections = ", ".join(f"{s['name']}={s['filled']}" for s in item["sections"])
            lines.append(
                f"{item['code']} — {item['title']} — total {item['total_filled']} jawaban ({sections})"
            )
    return "\n".join(lines)
