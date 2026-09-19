from __future__ import annotations

import pytest

from xninetzy.os.research import academic_search as mod


def test_arxiv_endpoint_uses_https():
    assert mod.ARXIV_ENDPOINT.startswith("https://"), (
        f"ARXIV_ENDPOINT must be https://, got {mod.ARXIV_ENDPOINT!r} "
        "(http:// triggers 301 redirect on export.arxiv.org)"
    )


def test_arxiv_adapter_base_url_uses_https():
    from xninetzy.os.research.sources import arxiv as arxiv_mod

    assert arxiv_mod.ArxivAdapter.base_url.startswith("https://"), (
        f"ArxivAdapter.base_url must be https://, got {arxiv_mod.ArxivAdapter.base_url!r}"
    )


def test_fetch_text_client_follows_redirects():
    import inspect

    from xninetzy.os.research import academic_search

    source = inspect.getsource(academic_search._fetch_text)
    assert "follow_redirects=True" in source, (
        "_fetch_text must set follow_redirects=True so https upgrades (e.g. arxiv http→https) work without 301"
    )


def test_selected_sids_importable_from_package():
    from xninetzy.os.research.sources import selected_sids

    assert selected_sids([{"sid": "S1"}, {"sid": "S2"}, {"title": "no sid"}]) == {"S1", "S2"}


def test_assign_sids_importable_from_package():
    from xninetzy.os.research.sources import assign_sids

    out = assign_sids([{"title": "A"}, {"title": "B"}])
    assert [d["sid"] for d in out] == ["S1", "S2"]


def test_research_source_importable_from_package():
    from xninetzy.os.research.sources import ResearchSource, to_source_model

    assert to_source_model({"title": "Y"}) == ResearchSource(title="Y")


def test_citations_validate_works_without_import_error():
    from xninetzy.os.research.citations import validate_citations

    cleaned, removed = validate_citations(
        "[S1] and [S9] and [S2]",
        [{"sid": "S1"}, {"sid": "S2"}],
    )
    assert "[S1]" in cleaned and "[S2]" in cleaned
    assert removed == ["S9"]


def test_research_rank_sources_module_imports():
    from xninetzy.tools.ecosystem import research_tools

    assert hasattr(research_tools, "research_rank_sources"), (
        "research_rank_sources must be importable from research_tools"
    )


@pytest.mark.asyncio
async def test_arxiv_search_does_not_raise_on_https_redirect(monkeypatch):
    captured_urls: list[str] = []

    async def fake_fetch_text(url, params=None, headers=None):
        captured_urls.append(url)
        return (
            '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            '<entry><id>http://arxiv.org/abs/2401.12345v1</id>'
            "<title>Real Redirect Test</title>"
            "<summary>abstract.</summary>"
            '<published>2024-01-15T00:00:00Z</published>'
            '<author><name>Alice</name></author></entry></feed>'
        )

    monkeypatch.setattr(mod, "_fetch_text", fake_fetch_text)
    rows = await mod._arxiv_search("attention", 5)
    assert rows, "_arxiv_search must return rows"
    assert captured_urls, "_arxiv_search must invoke _fetch_text"
    assert captured_urls[0].startswith("https://"), (
        f"_arxiv_search called with {captured_urls[0]!r} — must be https to avoid 301"
    )
