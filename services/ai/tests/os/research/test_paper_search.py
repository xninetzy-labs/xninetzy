from __future__ import annotations

import pytest

from app.xninetzy.os.research import academic_search as mod

ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>Test Paper One</title>
    <summary>First abstract.</summary>
    <published>2024-01-15T00:00:00Z</published>
    <author><name>Alice Chen</name></author>
    <link title="pdf" href="https://arxiv.org/pdf/2401.12345v1" type="application/pdf"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2402.99999v2</id>
    <title>Test Paper Two</title>
    <summary>Second abstract.</summary>
    <published>2024-02-01T00:00:00Z</published>
    <author><name>Bob Lee</name></author>
  </entry>
</feed>
"""

CROSSREF_JSON = {
    "message": {
        "items": [
            {
                "title": ["A CrossRef Study"],
                "DOI": "10.1000/xyz123",
                "URL": "https://doi.org/10.1000/xyz123",
                "abstract": "<p>Jats abstract body.</p>",
                "issued": {"date-parts": [[2023, 5]]},
                "author": [{"given": "Bob", "family": "Lee"}],
            },
            {"title": [], "DOI": "10.1000/notitle"},
        ]
    }
}


def test_normalize_identifier_variants():
    assert mod.normalize_identifier("10.1000/abc") == ("doi", "10.1000/abc")
    assert mod.normalize_identifier("https://doi.org/10.1000/abc") == ("doi", "10.1000/abc")
    assert mod.normalize_identifier("2401.12345") == ("arxiv", "2401.12345")
    assert mod.normalize_identifier("2401.12345v2") == ("arxiv", "2401.12345v2")
    assert mod.normalize_identifier("https://arxiv.org/abs/2401.12345") == ("arxiv", "2401.12345")
    assert mod.normalize_identifier("https://arxiv.org/pdf/2401.12345v1.pdf") == (
        "arxiv",
        "2401.12345v1.pdf",
    )
    assert mod.normalize_identifier("random words")[0] == "unknown"


def test_parse_arxiv_response_extracts_entries_and_pdf_link():
    results = mod.parse_arxiv_response(ARXIV_ATOM, limit=5)
    assert len(results) == 2
    first = results[0]
    assert first["title"] == "Test Paper One"
    assert first["identifier"] == "2401.12345v1"
    assert first["identifier_kind"] == "arxiv"
    assert first["year"] == 2024
    assert first["authors"] == ["Alice Chen"]
    assert first["pdf_url"].endswith("2401.12345v1")
    second = results[1]
    assert second["pdf_url"].endswith("2402.99999v2")


def test_parse_arxiv_response_respects_limit():
    assert len(mod.parse_arxiv_response(ARXIV_ATOM, limit=1)) == 1


def test_parse_crossref_items_skips_incomplete_and_labels_evidence():
    results = mod.parse_crossref_items(CROSSREF_JSON, limit=5)
    assert len(results) == 1
    item = results[0]
    assert item["title"] == "A CrossRef Study"
    assert item["identifier_kind"] == "doi"
    assert item["doi"] == "10.1000/xyz123"
    assert item["year"] == 2023
    assert item["evidence_level"] == "abstract"


@pytest.mark.asyncio
async def test_search_papers_merges_selected_sources(monkeypatch):
    async def fake_arxiv(query, limit):
        return [{"title": "A", "identifier_kind": "arxiv"}]

    async def fake_crossref(query, limit):
        return [{"title": "B", "identifier_kind": "doi"}]

    monkeypatch.setattr(mod, "_arxiv_search", fake_arxiv)
    monkeypatch.setattr(mod, "_crossref_search", fake_crossref)

    both = await mod.search_papers("q", sources="arxiv,crossref", max_results=2)
    only_arxiv = await mod.search_papers("q", sources="arxiv", max_results=2)

    assert [r["title"] for r in both] == ["A", "B"]
    assert [r["title"] for r in only_arxiv] == ["A"]


@pytest.mark.asyncio
async def test_get_paper_doi_via_crossref(monkeypatch):
    async def fake_fetch_json(url, params=None, headers=None):
        assert url.endswith("/works/10.1000/xyz123")
        return {"message": CROSSREF_JSON["message"]["items"][0]}

    monkeypatch.setattr(mod, "_fetch_json", fake_fetch_json)
    paper = await mod.get_paper("10.1000/xyz123")
    assert paper["status"] == "ok"
    assert paper["identifier_kind"] == "doi"
    assert paper["title"] == "A CrossRef Study"


@pytest.mark.asyncio
async def test_get_paper_arxiv_auto_detected(monkeypatch):
    async def fake_fetch_text(url, params=None, headers=None):
        assert params["id_list"] == "2401.12345"
        return ARXIV_ATOM

    monkeypatch.setattr(mod, "_fetch_text", fake_fetch_text)
    paper = await mod.get_paper("2401.12345")
    assert paper["status"] == "ok"
    assert paper["identifier_kind"] == "arxiv"
    assert paper["abstract"] == "First abstract."


@pytest.mark.asyncio
async def test_get_paper_unknown_identifier_reports_invalid():
    paper = await mod.get_paper("bukan identifier")
    assert paper["status"] == "invalid_identifier"


@pytest.mark.asyncio
async def test_download_paper_pdf_saves_open_access_file(monkeypatch, tmp_path):
    async def fake_get_paper(identifier, source="auto"):
        return {
            "status": "ok",
            "title": "Great Paper!",
            "identifier": "2401.12345",
            "url": "https://arxiv.org/abs/2401.12345",
            "pdf_url": "https://arxiv.org/pdf/2401.12345",
        }

    async def fake_fetch_bytes(url):
        return b"%PDF-fake"

    monkeypatch.setattr(mod, "get_paper", fake_get_paper)
    monkeypatch.setattr(mod, "_fetch_bytes", fake_fetch_bytes)

    result = await mod.download_paper_pdf("2401.12345", save_dir=tmp_path)
    assert result["status"] == "downloaded"
    path = tmp_path / result["path"]
    assert path.exists() or (tmp_path / path.name).exists()
    assert result["bytes"] == len(b"%PDF-fake")


@pytest.mark.asyncio
async def test_download_paper_without_legal_oa_is_honest(monkeypatch):
    async def fake_get_paper(identifier, source="auto"):
        return {
            "status": "ok",
            "title": "Paywalled",
            "identifier": "10.1000/pay",
            "url": "https://doi.org/10.1000/pay",
            "oa_pdf_urls": [],
        }

    monkeypatch.setattr(mod, "get_paper", fake_get_paper)
    result = await mod.download_paper_pdf("10.1000/pay")
    assert result["status"] == "no_oa_pdf"
    assert "Sci-Hub" in result["error"]
