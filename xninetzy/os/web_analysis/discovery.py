from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.cache_manager import AnalysisBusyError, AnalysisCacheManager
from app.xninetzy.os.web_analysis.security import detect_human_verification, is_safe_request_method
from app.xninetzy.os.web_analysis.sites import get_site


class DiscoveredPage(BaseModel):
    url: str
    title: str = ""
    depth: int = 0
    text: str = ""
    links: list[str] = Field(default_factory=list)


class WebDiscoveryResult(BaseModel):
    status: str
    source_url: str
    site_slug: str
    pages: list[DiscoveredPage] = Field(default_factory=list)
    links: int = 0
    human_verification: bool = False
    graph_nodes: int = 0
    graph_edges: int = 0
    knowledge_sources: int = 0
    captures: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class WebDiscoveryService:
    def __init__(self, cache: AnalysisCacheManager | None = None) -> None:
        self.cache = cache or AnalysisCacheManager()

    async def discover(
        self,
        source_url: str,
        *,
        depth: int = 1,
        max_pages: int | None = None,
        ingest_to_knowledge: bool = False,
        capture_visual: bool = False,
    ) -> WebDiscoveryResult:
        site = get_site(source_url)
        settings = get_settings()
        init_db()
        run_migrations()
        if not settings.WEB_ANALYSIS_ENABLED:
            return WebDiscoveryResult(
                status="configuration_required",
                source_url=source_url,
                site_slug=site.slug,
            )
        max_depth = max(0, settings.WEB_ANALYSIS_DISCOVERY_MAX_DEPTH)
        if depth < 0 or depth > max_depth:
            raise ValueError(f"depth harus berada di antara 0 dan {max_depth}.")
        page_limit = max_pages or settings.WEB_ANALYSIS_MAX_PAGES
        if page_limit < 1 or page_limit > settings.WEB_ANALYSIS_MAX_PAGES:
            raise ValueError(
                f"max_pages harus berada di antara 1 dan {settings.WEB_ANALYSIS_MAX_PAGES}."
            )
        if not site.dynamic:
            source_url = site.absolute_url(site.public_paths[0])
        else:
            source_url = AnalyzerService._canonical_url(source_url)

        try:
            with self.cache.lease(site.slug):
                result = await self._crawl(
                    source_url,
                    site,
                    depth=depth,
                    max_pages=page_limit,
                    ingest_to_knowledge=ingest_to_knowledge,
                    capture_visual=capture_visual,
                )
        except AnalysisBusyError as exc:
            return WebDiscoveryResult(
                status="busy",
                source_url=source_url,
                site_slug=site.slug,
                errors=[str(exc)],
            )
        self._save_result(result)
        return result

    async def _crawl(
        self,
        source_url: str,
        site,
        *,
        depth: int,
        max_pages: int,
        ingest_to_knowledge: bool,
        capture_visual: bool,
    ) -> WebDiscoveryResult:
        settings = get_settings()
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return WebDiscoveryResult(
                status="failed",
                source_url=source_url,
                site_slug=site.slug,
                errors=["Playwright tidak tersedia."],
            )

        pages: list[DiscoveredPage] = []
        queued: list[tuple[str, int, str | None]] = [(source_url, 0, None)]
        visited: set[str] = set()
        parent_links: list[tuple[str, str]] = []
        errors: list[str] = []
        human_verification = False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=settings.WEB_ANALYSIS_HEADLESS)
            try:
                context = await browser.new_context()
                async def block_mutations(route) -> None:
                    if is_safe_request_method(route.request.method):
                        await route.continue_()
                    else:
                        await route.abort("blockedbyclient")

                await context.route("**/*", block_mutations)
                page = await context.new_page()
                while queued and len(visited) < max_pages:
                    target, current_depth, parent = queued.pop(0)
                    canonical = AnalyzerService._canonical_url(target)
                    if canonical in visited or not AnalyzerService._safe_to_visit(site, canonical):
                        continue
                    visited.add(canonical)
                    try:
                        await page.goto(
                            canonical,
                            wait_until="domcontentloaded",
                            timeout=settings.WEB_ANALYSIS_TIMEOUT_MS,
                        )
                        await asyncio.sleep(settings.WEB_ANALYSIS_REQUEST_DELAY_SECONDS)
                        html = await page.content()
                        if detect_human_verification(html, canonical):
                            human_verification = True
                        title = (await page.title()).strip()[:300]
                        try:
                            body = await page.locator("body").inner_text(
                                timeout=settings.WEB_ANALYSIS_TIMEOUT_MS
                            )
                        except Exception:
                            body = ""
                        text = re.sub(r"\s+", " ", body).strip()[:12_000]
                        links = [
                            AnalyzerService._canonical_url(link)
                            for link in await AnalyzerService._discover_links(page)
                            if AnalyzerService._safe_to_visit(site, AnalyzerService._canonical_url(link))
                        ]
                        links = list(dict.fromkeys(links))
                        pages.append(
                            DiscoveredPage(
                                url=canonical,
                                title=title,
                                depth=current_depth,
                                text=text,
                                links=links[:100],
                            )
                        )
                        if parent:
                            parent_links.append((parent, canonical))
                        if human_verification:
                            break
                        if current_depth < depth:
                            for link in links:
                                if link not in visited:
                                    queued.append((link, current_depth + 1, canonical))
                    except Exception as exc:
                        errors.append(f"{canonical}: {type(exc).__name__}")
            finally:
                await browser.close()

        result = WebDiscoveryResult(
            status="human_verification_required" if human_verification else "completed",
            source_url=source_url,
            site_slug=site.slug,
            pages=pages,
            links=len(parent_links),
            human_verification=human_verification,
            errors=errors[:10],
        )
        await self._persist_evidence(
            result,
            parent_links,
            ingest_to_knowledge=ingest_to_knowledge,
            capture_visual=capture_visual,
        )
        return result

    async def _persist_evidence(
        self,
        result: WebDiscoveryResult,
        parent_links: list[tuple[str, str]],
        *,
        ingest_to_knowledge: bool,
        capture_visual: bool,
    ) -> None:
        settings = get_settings()
        graph_keys: dict[str, str] = {}
        if settings.GRAPHRAG_V3_ENABLED:
            from app.xninetzy.os.graph.v3 import graph_service

            for page in result.pages:
                try:
                    node = graph_service.upsert_node(
                        node_type="web_page",
                        title=page.url,
                        content=page.text[:6_000] or page.title,
                        properties={
                            "url": page.url,
                            "title": page.title,
                            "depth": page.depth,
                            "site_slug": result.site_slug,
                        },
                        provenance={
                            "source": "web_discovery",
                            "uri": page.url,
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                        },
                        identity=page.url,
                        actor="web_discovery",
                    )
                    graph_keys[page.url] = node.key
                    result.graph_nodes += 1
                except Exception as exc:
                    result.errors.append(f"graph node {page.url}: {type(exc).__name__}")
            for parent, child in parent_links:
                if parent not in graph_keys or child not in graph_keys:
                    continue
                try:
                    graph_service.upsert_edge(
                        source_key=graph_keys[parent],
                        target_key=graph_keys[child],
                        edge_type="links_to",
                        provenance={"source": "web_discovery", "uri": parent},
                        actor="web_discovery",
                    )
                    result.graph_edges += 1
                except Exception as exc:
                    result.errors.append(f"graph edge {parent}: {type(exc).__name__}")

        if ingest_to_knowledge:
            from app.xninetzy.os.knowledge.ingestion import ingest_text

            for page in result.pages:
                if not page.text:
                    continue
                try:
                    ingested = ingest_text(
                        title=page.title or page.url,
                        text=f"Source URL: {page.url}\n\n{page.text}",
                        source_type="web_article",
                        uri=page.url,
                        metadata={"web_discovery_site": result.site_slug, "depth": page.depth},
                    )
                    if ingested.get("status") == "ingested":
                        result.knowledge_sources += 1
                except Exception as exc:
                    result.errors.append(f"knowledge {page.url}: {type(exc).__name__}")

        if capture_visual:
            from app.xninetzy.tools.ecosystem.pixelrag_tools import pixelrag_capture

            for page in result.pages[: max(0, settings.WEB_ANALYSIS_MAX_VISUAL_CAPTURES)]:
                try:
                    output = await pixelrag_capture.ainvoke(
                        {
                            "source": page.url,
                            "output_subdir": result.site_slug,
                            "backend": "cdp",
                        }
                    )
                    result.captures.append(str(output)[:500])
                except Exception as exc:
                    result.errors.append(f"pixelrag {page.url}: {type(exc).__name__}")

    def _save_result(self, result: WebDiscoveryResult) -> None:
        settings = get_settings()
        path = Path(settings.WEB_ANALYSIS_DATA_DIR) / "discoveries" / result.site_slug / "latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
