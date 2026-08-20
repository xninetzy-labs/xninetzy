from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EvidenceLevel = Literal["metadata", "snippet", "abstract", "fulltext"]
SourceType = Literal["web", "youtube", "academic", "upload"]


class ResearchSource(BaseModel):
    sid: str = ""
    title: str = ""
    url: str = ""
    snippet: str = ""
    source_type: SourceType = "web"
    evidence_level: EvidenceLevel = "snippet"
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str = ""
    video_id: str = ""
    score: float = 0.0
    why: str = ""
    provider: str = ""
    providers: list[str] = Field(default_factory=list)
    query_id: str = ""
    raw_rank: int | None = None
    canonical_url: str = ""
    content_hash: str = ""
    fetched_at: str = ""
    fulltext_status: str = "not_requested"
    evidence_locator: str = ""
    relevance_score: float = 0.0
    quality_score: float = 0.0
    duplicate_of: str = ""
    error: str = ""


def assign_sids(sources: list[dict]) -> list[dict]:
    result: list[dict] = []
    for index, source in enumerate(sources, 1):
        result.append({**source, "sid": f"S{index}"})
    return result


def to_source_model(source: dict) -> ResearchSource:
    known = {name for name in ResearchSource.model_fields}
    payload = {key: value for key, value in source.items() if key in known}
    return ResearchSource(**payload)


def selected_sids(sources: list[dict]) -> set[str]:
    return {source["sid"] for source in sources if source.get("sid")}
