from contextlib import contextmanager

import pytest

from app.xninetzy.os.web_analysis.discovery import (
    DiscoveredPage,
    WebDiscoveryResult,
    WebDiscoveryService,
)
from app.xninetzy.os.web_analysis.sites import SiteDefinition


class DummyCache:
    @contextmanager
    def lease(self, slug):
        yield


@pytest.mark.asyncio
async def test_discovery_orchestration_is_bounded(monkeypatch):
    service = WebDiscoveryService(cache=DummyCache())
    site = SiteDefinition(
        slug="public-test",
        name="Public web: example.com",
        base_url="https://example.com",
        public_paths=("/",),
        authenticated_paths=(),
        login_path="/",
        dynamic=True,
    )

    monkeypatch.setattr(
        "app.xninetzy.os.web_analysis.discovery.get_site",
        lambda value: site,
    )
    expected = WebDiscoveryResult(
        status="completed",
        source_url="https://example.com",
        site_slug=site.slug,
        pages=[
            DiscoveredPage(
                url="https://example.com",
                title="Example",
                text="safe evidence",
            )
        ],
    )

    async def fake_crawl(*args, **kwargs):
        assert kwargs["depth"] == 1
        assert kwargs["max_pages"] == 2
        return expected

    monkeypatch.setattr(service, "_crawl", fake_crawl)
    monkeypatch.setattr(service, "_save_result", lambda result: None)
    result = await service.discover("https://example.com", depth=1, max_pages=2)
    assert result is expected


@pytest.mark.asyncio
async def test_discovery_rejects_depth_above_config(monkeypatch):
    monkeypatch.setenv("WEB_ANALYSIS_DISCOVERY_MAX_DEPTH", "1")
    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(ValueError, match="depth"):
        await WebDiscoveryService(cache=DummyCache()).discover(
            "https://example.com",
            depth=2,
            max_pages=1,
        )
