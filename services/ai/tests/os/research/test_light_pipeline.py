from __future__ import annotations

import pytest

from app.xninetzy.os.research import light_pipeline
from app.xninetzy.os.research.citations import format_sources_block
from app.xninetzy.os.research.light_pipeline import (
    collect_quick_sources,
    group_sources_by_type,
)
from app.xninetzy.tools.ecosystem import research_tools


class _FakeAction:
    def __init__(self, sources: list[dict], fail: bool = False):
        self._sources = sources
        self._fail = fail

    async def execute(self, input):
        if self._fail:
            raise RuntimeError("provider down")
        return type("Out", (), {"data": {"sources": self._sources}})


def _patch_registry(monkeypatch, mapping: dict):
    class _Registry:
        @staticmethod
        def get(name):
            return mapping.get(name)

    monkeypatch.setattr(light_pipeline.ResearchActionRegistry, "get", _Registry.get)


@pytest.mark.asyncio
async def test_collect_quick_sources_merges_and_stamps_timestamp(monkeypatch):
    _patch_registry(
        monkeypatch,
        {
            "web_search": _FakeAction([{"title": "Web", "source_type": "web"}]),
            "youtube_search": _FakeAction([{"title": "Video", "source_type": "youtube"}]),
            "academic_search": _FakeAction([{"title": "Paper", "source_type": "academic"}]),
        },
    )
    sources = await collect_quick_sources("rag", limit=2)
    assert [s["title"] for s in sources] == ["Web", "Video", "Paper"]
    assert all(s["collected_at"] for s in sources)


@pytest.mark.asyncio
async def test_collect_quick_sources_survives_single_provider_failure(monkeypatch):
    _patch_registry(
        monkeypatch,
        {
            "web_search": _FakeAction([], fail=True),
            "youtube_search": None,
            "academic_search": _FakeAction([{"title": "Paper", "source_type": "academic"}]),
        },
    )
    sources = await collect_quick_sources("rag", limit=2)
    assert [s["title"] for s in sources] == ["Paper"]


def test_group_sources_by_type():
    grouped = group_sources_by_type(
        [
            {"source_type": "web"},
            {"source_type": "academic"},
            {"source_type": "youtube"},
            {"source_type": "mystery"},
        ]
    )
    assert set(grouped) == {"web", "academic", "youtube"}
    assert len(grouped["web"]) == 2


@pytest.mark.asyncio
async def test_research_light_renders_all_source_groups(monkeypatch):
    async def fake_collect(topic, limit=3, **kwargs):
        return [
            {"title": "Web Result", "url": "https://w", "snippet": "snip", "source_type": "web", "collected_at": "2026-08-24T00:00:00+00:00"},
            {"title": "Paper Result", "url": "https://p", "snippet": "abs", "source_type": "academic", "collected_at": "2026-08-24T00:00:00+00:00"},
            {"title": "Video Result", "url": "https://y", "description": "desc", "source_type": "youtube", "collected_at": "2026-08-24T00:00:00+00:00"},
        ]

    monkeypatch.setattr(light_pipeline, "collect_quick_sources", fake_collect)

    result = await research_tools.research_light.ainvoke({"topic": "rag"})
    assert "🌐 *Web*" in result
    assert "🎓 *Paper Akademik*" in result
    assert "📺 *YouTube*" in result
    assert "Paper Result" in result


@pytest.mark.asyncio
async def test_research_light_honest_when_nothing_found(monkeypatch):
    async def fake_collect(topic, limit=3, **kwargs):
        return []

    monkeypatch.setattr(light_pipeline, "collect_quick_sources", fake_collect)
    result = await research_tools.research_light.ainvoke({"topic": "rag"})
    assert "Tidak ada sumber" in result
    assert "TAVILY" not in result


@pytest.mark.asyncio
async def test_generate_brief_includes_real_sources_with_timestamps(monkeypatch):
    async def fake_collect(topic, limit=3, **kwargs):
        if topic.startswith("Apa definisi"):
            return []
        return [
            {
                "title": "Real Paper",
                "url": "https://arxiv.org/abs/2401.12345",
                "snippet": "abstract",
                "source_type": "academic",
                "evidence_level": "abstract",
                "collected_at": "2026-08-24T01:02:03+00:00",
            }
        ]

    monkeypatch.setattr(light_pipeline, "collect_quick_sources", fake_collect)

    result = await research_tools.research_generate_brief.ainvoke({"topic": "retrieval augmented generation"})
    assert "Sumber Terpilih" in result
    assert "Real Paper" in result
    assert "https://arxiv.org/abs/2401.12345" in result
    assert "diambil 2026-08-24T01:02:03+00:00" in result


def test_format_sources_block_appends_collected_stamp():
    block = format_sources_block(
        [{"sid": "S1", "title": "T", "url": "https://u", "evidence_level": "abstract", "collected_at": "2026-08-24T00:00:00+00:00"}]
    )
    assert "S1 [abstract] T — https://u · diambil 2026-08-24T00:00:00+00:00" in block
