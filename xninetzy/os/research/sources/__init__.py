from xninetzy.os.research.sources import (
    arbeitnow,
    arxiv,
    bps,
    crossref,
    dbpedia,
    dblp,
    europe_pmc,
    fred,
    github,
    hackernews,
    huggingface,
    kaggle,
    nvd,
    open_llm_leaderboard,
    openalex,
    osm,
    papers_with_code,
    patentsview,
    pubmed,
    reddit,
    remoteok,
    rss,
    semantic_scholar,
    stackoverflow,
    wayback,
    wikidata,
    wikipedia,
    world_bank,
)
from xninetzy.os.research.sources.base import (
    CircuitBreaker,
    HealthStatus,
    RateLimit,
    RetryPolicy,
    SourceAdapter,
    SourceCategory,
    SourceRecord,
)
from xninetzy.os.research.sources.rate_limit import (
    CircuitBreakerGuard,
    RateLimiter,
    retry_async,
)
from xninetzy.os.research.sources.registry import (
    SOURCE_REGISTRY,
    build_breaker,
    build_rate_limiter,
    clear_registry,
    get_adapter,
    list_adapters,
    register_adapter,
)
from xninetzy.os.research.sources.sid import (
    ResearchSource,
    assign_sids,
    selected_sids,
    to_source_model,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerGuard",
    "HealthStatus",
    "RateLimit",
    "RateLimiter",
    "ResearchSource",
    "RetryPolicy",
    "SOURCE_REGISTRY",
    "SourceAdapter",
    "SourceCategory",
    "SourceRecord",
    "arbeitnow",
<<<<<<< Updated upstream
=======
    "assign_sids",
>>>>>>> Stashed changes
    "arxiv",
    "assign_sids",
    "bps",
    "build_breaker",
    "build_rate_limiter",
    "clear_registry",
    "crossref",
    "dbpedia",
    "dblp",
    "europe_pmc",
    "fred",
    "get_adapter",
    "github",
    "hackernews",
    "huggingface",
    "kaggle",
    "list_adapters",
    "nvd",
    "open_llm_leaderboard",
    "openalex",
    "osm",
    "papers_with_code",
    "patentsview",
    "pubmed",
    "reddit",
    "register_adapter",
    "remoteok",
    "retry_async",
    "rss",
    "selected_sids",
    "semantic_scholar",
    "stackoverflow",
    "to_source_model",
    "wayback",
    "wikidata",
    "wikipedia",
    "world_bank",
]


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
