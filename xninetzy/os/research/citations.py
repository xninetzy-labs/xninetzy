from __future__ import annotations

import re

from app.xninetzy.os.research.sources import selected_sids

_CITATION = re.compile(r"\[S(\d+)\]")


def validate_citations(text: str, sources: list[dict]) -> tuple[str, list[str]]:
    valid = selected_sids(sources)
    removed: list[str] = []

    def _replace(match: re.Match) -> str:
        token = f"S{match.group(1)}"
        if token in valid:
            return match.group(0)
        removed.append(token)
        return ""

    cleaned = _CITATION.sub(_replace, text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned, removed


def format_sources_block(sources: list[dict]) -> str:
    lines = ["*Sumber*"]
    for source in sources:
        sid = source.get("sid") or "?"
        title = source.get("title") or "Untitled"
        url = source.get("url") or ""
        level = source.get("evidence_level") or "snippet"
        tail = f" — {url}" if url else ""
        collected = source.get("collected_at") or ""
        stamp = f" · diambil {collected}" if collected else ""
        lines.append(f"{sid} [{level}] {title}{tail}{stamp}")
    return "\n".join(lines)
