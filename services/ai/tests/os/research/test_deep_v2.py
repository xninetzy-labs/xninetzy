from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.research.sources import (
    ResearchSource,
    assign_sids,
    selected_sids,
    to_source_model,
)
from app.xninetzy.os.research import safe_fetch, web_search
from app.xninetzy.os.research import academic_search as academic_mod
from app.xninetzy.os.research import guards as guards_mod
from app.xninetzy.os.research.citations import format_sources_block, validate_citations
from app.xninetzy.os.research.safe_fetch import UnsafeUrlError, _validate_url


@pytest.fixture(autouse=True)
def sqlite_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "deep_v2.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def test_assign_sids_are_stable_and_sequential():
    ranked = [{"title": "A"}, {"title": "B"}, {"title": "C"}]
    with_sids = assign_sids(ranked)
    assert [s["sid"] for s in with_sids] == ["S1", "S2", "S3"]
    assert selected_sids(with_sids) == {"S1", "S2", "S3"}


def test_to_source_model_ignores_unknown_fields_and_keeps_evidence_level():
    model = to_source_model(
        {
            "sid": "S1",
            "title": "Paper",
            "evidence_level": "abstract",
            "unrelated": "drop me",
        }
    )
    assert isinstance(model, ResearchSource)
    assert model.evidence_level == "abstract"
    assert model.title == "Paper"


def test_default_evidence_level_is_snippet_not_fulltext():
    assert ResearchSource().evidence_level == "snippet"


def test_research_sources_table_created_by_migration():
    with connect() as conn:
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(research_sources)").fetchall()
        }
    assert {"session_id", "sid", "evidence_level", "doi"} <= cols


def test_research_sessions_gets_citation_report_column():
    with connect() as conn:
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(research_sessions)").fetchall()
        }
    assert "citation_report" in cols


def _fake_getaddrinfo(ip):
    def _inner(host, *args, **kwargs):
        return [(None, None, None, None, (ip, 0))]

    return _inner


def test_ssrf_rejects_non_http_scheme():
    with pytest.raises(UnsafeUrlError):
        _validate_url("file:///etc/passwd")
    with pytest.raises(UnsafeUrlError):
        _validate_url("ftp://example.com/x")


def test_ssrf_rejects_loopback_and_private(monkeypatch):
    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", _fake_getaddrinfo("127.0.0.1"))
    with pytest.raises(UnsafeUrlError):
        _validate_url("http://localhost/")
    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", _fake_getaddrinfo("10.0.0.5"))
    with pytest.raises(UnsafeUrlError):
        _validate_url("http://internal.example/")
    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", _fake_getaddrinfo("169.254.169.254"))
    with pytest.raises(UnsafeUrlError):
        _validate_url("http://metadata/")


def test_ssrf_allows_public_ip(monkeypatch):
    monkeypatch.setattr(safe_fetch.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    assert _validate_url("https://example.com/page") == "https://example.com/page"


@pytest.mark.asyncio
async def test_web_search_falls_back_to_ddgs_when_no_key(monkeypatch):
    get_settings.cache_clear()

    async def _fake_ddgs(query, limit):
        return [{"title": "Free hit", "url": "https://x.example/a", "snippet": "s"}]

    monkeypatch.setattr(web_search, "_ddgs_search", _fake_ddgs)
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("SERPER_API_KEY", "")
    get_settings.cache_clear()
    results = await web_search.web_search("langgraph", limit=3)
    assert results and results[0]["title"] == "Free hit"


@pytest.mark.asyncio
async def test_web_search_returns_empty_when_ddgs_empty(monkeypatch):
    async def _empty(query, limit):
        return []

    monkeypatch.setattr(web_search, "_ddgs_search", _empty)
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("SERPER_API_KEY", "")
    get_settings.cache_clear()
    assert await web_search.web_search("x", limit=3) == []


@pytest.mark.asyncio
async def test_academic_search_empty_providers_no_fabrication(monkeypatch):
    async def _empty(query, limit):
        return []

    monkeypatch.setattr(academic_mod, "_arxiv_search", _empty)
    monkeypatch.setattr(academic_mod, "_crossref_search", _empty)
    assert await academic_mod.academic_search("transformers", limit=3) == []


@pytest.mark.asyncio
async def test_academic_search_labels_abstract_not_fulltext(monkeypatch):
    async def _arxiv(query, limit):
        return [
            {
                "title": "Attention Is All You Need",
                "url": "http://arxiv.org/abs/1706.03762",
                "snippet": "abstract text",
                "source_type": "academic",
                "evidence_level": "abstract",
                "authors": ["Vaswani"],
                "year": 2017,
            }
        ]

    async def _empty(query, limit):
        return []

    monkeypatch.setattr(academic_mod, "_arxiv_search", _arxiv)
    monkeypatch.setattr(academic_mod, "_crossref_search", _empty)
    results = await academic_mod.academic_search("transformers", limit=3)
    assert results[0]["evidence_level"] == "abstract"
    assert results[0]["evidence_level"] != "fulltext"


def test_validate_citations_strips_unbacked_refs():
    sources = assign_sids([{"title": "A", "url": "https://a"}, {"title": "B", "url": "https://b"}])
    text = "Finding one [S1]. Finding two [S2]. Ghost [S3] and [S9]."
    cleaned, removed = validate_citations(text, sources)
    assert "[S1]" in cleaned and "[S2]" in cleaned
    assert "[S3]" not in cleaned and "[S9]" not in cleaned
    assert set(removed) == {"S3", "S9"}


def test_format_sources_block_shows_evidence_level():
    sources = assign_sids(
        [{"title": "Paper", "url": "https://doi/x", "evidence_level": "abstract"}]
    )
    block = format_sources_block(sources)
    assert "S1 [abstract] Paper" in block
    assert "https://doi/x" in block


def test_resource_guard_allows_when_under_limit(monkeypatch):
    monkeypatch.setattr(guards_mod, "count_active_runs", lambda chat_id: 0)
    ok, reason = guards_mod.check_resource_guards("chat-1")
    assert ok is True
    assert reason == "ok"


def test_resource_guard_blocks_over_concurrent_limit(monkeypatch):
    monkeypatch.setenv("DEEP_RESEARCH_MAX_CONCURRENT_PER_CHAT", "1")
    get_settings.cache_clear()
    monkeypatch.setattr(guards_mod, "count_active_runs", lambda chat_id: 1)
    ok, reason = guards_mod.check_resource_guards("chat-1")
    assert ok is False
    assert reason == "max_concurrent"
    msg = guards_mod.resource_guard_denied_message(reason)
    assert "masih berjalan" in msg
    get_settings.cache_clear()
