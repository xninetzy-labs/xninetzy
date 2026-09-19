from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_EVIDENCE_LEVELS = frozenset({"metadata", "snippet", "abstract", "fulltext"})


@dataclass(frozen=True)
class ResearchSource:
    sid: str | None = None
    title: str = ""
    url: str = ""
    source: str = ""
    source_type: str = ""
    evidence_level: str = "snippet"
    published_at: str | None = None
    author: str | None = None
    snippet: str = ""
    content: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    license: str | None = None
    citation: str | None = None
    confidence: float = 0.0


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def to_source_model(record: dict[str, Any] | ResearchSource) -> ResearchSource:
    if isinstance(record, ResearchSource):
        return record
    if not isinstance(record, dict):
        return ResearchSource()
    level = _coerce_text(record.get("evidence_level")) or "snippet"
    if level not in _EVIDENCE_LEVELS:
        level = "snippet"
    identifiers = record.get("identifiers")
    if not isinstance(identifiers, dict):
        identifiers = {}
    else:
        identifiers = {str(k): str(v) for k, v in identifiers.items()}
    return ResearchSource(
        sid=_coerce_text(record.get("sid")) or None,
        title=_coerce_text(record.get("title")),
        url=_coerce_text(record.get("url")),
        source=_coerce_text(record.get("source")),
        source_type=_coerce_text(record.get("source_type")),
        evidence_level=level,
        published_at=record.get("published_at"),
        author=record.get("author"),
        snippet=_coerce_text(record.get("snippet")),
        content=record.get("content"),
        identifiers=identifiers,
        license=record.get("license"),
        citation=record.get("citation"),
        confidence=float(record.get("confidence") or 0.0),
    )


def assign_sids(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, item in enumerate(ranked, start=1):
        sid = f"S{index}"
        if isinstance(item, dict):
            new_item = dict(item)
        else:
            new_item = {"value": item}
        new_item["sid"] = sid
        out.append(new_item)
    return out


def selected_sids(sources: list[dict[str, Any]]) -> set[str]:
    sids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        sid = source.get("sid")
        if isinstance(sid, str) and sid:
            sids.add(sid)
    return sids
