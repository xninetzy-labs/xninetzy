from __future__ import annotations

from xninetzy.os.research.sources.browser_scraper import make_fake_session


KALIBRR_HTML = """
<html><body>
<div class="k-list-item">
  <a class="k-list-item__title" href="/jobs/abc123">Backend Engineer Intern</a>
  <div class="k-list-item__company">PT Tokopedia</div>
  <div class="k-list-item__location">Jakarta</div>
  <span class="k-list-item__posted-at">2026-09-20</span>
  <p class="k-list-item__desc">Python, Django, REST API, PostgreSQL.</p>
</div>
<div class="k-list-item">
  <a class="k-list-item__title" href="/jobs/def456">Data Scientist Intern</a>
  <div class="k-list-item__company">PT Gojek</div>
  <div class="k-list-item__location">Jakarta</div>
  <span class="k-list-item__posted-at">2026-09-18</span>
  <p class="k-list-item__desc">Python, SQL, machine learning.</p>
</div>
</body></html>
"""

GLINTS_HTML = """
<html><body>
<article role="article" class="Opportunityscard">
  <h2><a aria-label="Job card title" href="/id/opportunities/xyz/frontend-intern">Frontend Intern</a></h2>
  <div class="Opportunityscard__company">PT Bukalapak</div>
  <div class="Opportunityscard__location">Bandung</div>
  <time>2026-09-19</time>
  <p class="Opportunityscard__description">React, TypeScript, Next.js.</p>
</article>
</body></html>
"""

DEALLS_HTML = """
<html><body>
<a class="job-link" href="/loker/devops-intern~pt-traveloka-789">
  <h3 class="job-title">DevOps Intern</h3>
  <span class="company-name">PT Traveloka</span>
  <span class="job-location">Jakarta</span>
  <span class="posted-date">2026-09-21</span>
  <p class="job-snippet">Docker, Kubernetes, Terraform.</p>
</a>
</body></html>
"""

JOBSTREET_HTML = """
<html><body>
<article data-automation="job-item">
  <h1 class="job-title"><a href="/id/job/ml-engineer-jr">ML Engineer (Junior)</a></h1>
  <span class="company-name">PT Shopee Indonesia</span>
  <ul class="job-location"><li>Jakarta</li></ul>
  <time class="job-date">2026-09-15</time>
  <div class="job-description">Python, PyTorch, AWS.</div>
</article>
</body></html>
"""


def test_kalibrr_parses_listings_into_source_records():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    adapter = KalibrrAdapter(session_factory=lambda: make_fake_session({KalibrrAdapter.SEARCH_URL.split("?")[0]: KALIBRR_HTML}))
    import asyncio

    records = asyncio.run(adapter.search("engineer", limit=10))
    assert len(records) == 2
    first = records[0]
    assert first.title == "Backend Engineer Intern"
    assert first.author == "PT Tokopedia"
    assert "tokopedia" in first.url or "abc123" in first.url
    assert first.identifiers["kalibrr_slug"] == "abc123"
    assert "python" in first.snippet.lower()


def test_glints_parses_listings_into_source_records():
    from xninetzy.os.research.sources.glints import GlintsAdapter

    html_by_url = {GlintsAdapter.SEARCH_URL.split("?")[0]: GLINTS_HTML}
    adapter = GlintsAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    records = asyncio.run(adapter.search("frontend", limit=10))
    assert len(records) == 1
    first = records[0]
    assert first.title == "Frontend Intern"
    assert first.author == "PT Bukalapak"
    assert first.identifiers["glints_slug"] == "frontend-intern"


def test_dealls_parses_listings_into_source_records():
    from xninetzy.os.research.sources.dealls import DeallsAdapter

    html_by_url = {DeallsAdapter.SEARCH_URL.split("?")[0]: DEALLS_HTML}
    adapter = DeallsAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    records = asyncio.run(adapter.search("devops", limit=10))
    assert len(records) == 1
    first = records[0]
    assert first.title == "DevOps Intern"
    assert first.author == "PT Traveloka"
    assert first.identifiers["dealls_slug"] == "devops-intern~pt-traveloka-789"


def test_jobstreet_parses_listings_into_source_records():
    from xninetzy.os.research.sources.jobstreet_id import JobstreetIDAdapter

    html_by_url = {JobstreetIDAdapter.SEARCH_URL: JOBSTREET_HTML}
    adapter = JobstreetIDAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    records = asyncio.run(adapter.search("ml", limit=10))
    assert len(records) == 1
    first = records[0]
    assert first.title == "ML Engineer (Junior)"
    assert first.author == "PT Shopee Indonesia"
    assert first.identifiers["jobstreet_slug"] == "ml-engineer-jr"


def test_adapter_returns_empty_when_browser_unavailable():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    def boom():
        from xninetzy.os.auth.browser.gateway import BrowserGatewayUnavailable

        async def fail():
            raise BrowserGatewayUnavailable("playwright not installed")

        return fail()

    adapter = KalibrrAdapter(session_factory=boom)
    import asyncio

    records = asyncio.run(adapter.search("engineer", limit=10))
    assert records == []


def test_adapter_handles_empty_html():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    html_by_url = {KalibrrAdapter.SEARCH_URL: "<html><body></body></html>"}
    adapter = KalibrrAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    records = asyncio.run(adapter.search("engineer", limit=10))
    assert records == []


def test_adapter_logs_tos_warning_on_each_call(caplog):
    import logging

    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    html_by_url = {KalibrrAdapter.SEARCH_URL: KALIBRR_HTML}
    adapter = KalibrrAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    with caplog.at_level(logging.INFO, logger="xninetzy.os.research.sources.browser_scraper"):
        asyncio.run(adapter.search("engineer", limit=10))
    assert any("terms-of-service" in record.message for record in caplog.records)


def test_circuit_breaker_trips_after_failures():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    def boom():
        from xninetzy.os.auth.browser.gateway import BrowserGatewayUnavailable

        async def fail():
            raise BrowserGatewayUnavailable("browser gone")

        return fail()

    adapter = KalibrrAdapter(session_factory=boom)
    import asyncio

    for _ in range(6):
        asyncio.run(adapter.search("engineer", limit=10))
    assert adapter._breaker._state.state in {"open", "half_open"}


def test_fetch_returns_record_when_url_is_recognized():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    html_by_url = {
        "https://www.kalibrr.com/c/jobs/abc123": KALIBRR_HTML,
        KalibrrAdapter.SEARCH_URL: KALIBRR_HTML,
    }
    adapter = KalibrrAdapter(session_factory=lambda: make_fake_session(html_by_url))
    import asyncio

    record = asyncio.run(adapter.fetch("https://www.kalibrr.com/c/jobs/abc123"))
    assert record is not None
    assert record.title in {"Backend Engineer Intern", "Data Scientist Intern"}


def test_fetch_returns_none_for_unknown_url():
    from xninetzy.os.research.sources.kalibrr import KalibrrAdapter

    adapter = KalibrrAdapter(
        session_factory=lambda: make_fake_session({KalibrrAdapter.SEARCH_URL: KALIBRR_HTML})
    )
    import asyncio

    assert asyncio.run(adapter.fetch("https://unknown.example/jobs/x")) is None
