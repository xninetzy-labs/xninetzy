from __future__ import annotations

from dataclasses import dataclass

from xninetzy.os.research.sources import SourceCategory, get_adapter
from xninetzy.os.research.sources.base import SourceAdapter


@dataclass(frozen=True)
class RouteRequest:
    category: SourceCategory
    requires_open_access: bool = False
    language: str = "en"
    freshness_days: int | None = None


_ROUTING_TABLE: dict[SourceCategory, tuple[str, ...]] = {
    SourceCategory.PAPER: ("openalex", "arxiv", "crossref", "semantic_scholar", "pubmed"),
    SourceCategory.CODE: ("github",),
    SourceCategory.DATASET: ("huggingface", "zenodo", "kaggle"),
    SourceCategory.NEWS: ("hackernews", "reddit", "rss"),
    SourceCategory.COMPANY: (),
    SourceCategory.MODEL: ("huggingface",),
    SourceCategory.BENCHMARK: ("papers_with_code", "open_llm_leaderboard"),
    SourceCategory.SECURITY: ("nvd",),
    SourceCategory.PATENT: ("patentsview",),
    SourceCategory.ECONOMICS: ("world_bank", "fred", "bps"),
    SourceCategory.GEOGRAPHIC: ("osm",),
    SourceCategory.ENTITY: ("wikidata", "dbpedia"),
    SourceCategory.GENERAL: ("stackoverflow", "wayback"),
}


def route_sources(request: RouteRequest) -> list[SourceAdapter]:
    chosen_ids = _ROUTING_TABLE.get(request.category, ())
    adapters: list[SourceAdapter] = []
    for source_id in chosen_ids:
        adapter = get_adapter(source_id)
        if adapter is None:
            continue
        adapters.append(adapter)
    return adapters


def route_by_name(name: str, **kwargs: object) -> list[SourceAdapter]:
    try:
        category = SourceCategory(name.strip().casefold())
    except ValueError:
        return []
    requires_oa = bool(kwargs.get("requires_open_access", False))
    language = str(kwargs.get("language", "en"))
    freshness = kwargs.get("freshness_days")
    freshness_int = int(freshness) if isinstance(freshness, int) else None
    request = RouteRequest(
        category=category,
        requires_open_access=requires_oa,
        language=language,
        freshness_days=freshness_int,
    )
    return route_sources(request)


def available_categories() -> list[str]:
    populated = [
        cat.value for cat, ids in _ROUTING_TABLE.items() if ids
    ]
    return sorted(populated)
