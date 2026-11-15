from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

XNINETZY_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(XNINETZY_ROOT))


@dataclass
class SourceSpec:
    source_id: str
    display_name: str
    login_url: str
    login_marker: str
    needs_login: bool = True
    cookie_domain_match: str = ""
    notes: str = ""


SOURCES: dict[str, SourceSpec] = {
    "kalibrr": SourceSpec(
        source_id="kalibrr",
        display_name="Kalibrr",
        login_url="https://www.kalibrr.com/login?redirectTo=%2Fid-ID%2Fjobs",
        login_marker="profile",
        cookie_domain_match="kalibrr",
        notes="Google OAuth. Redirects to jobseeker.kalibrr.com when logged in.",
    ),
    "glints": SourceSpec(
        source_id="glints",
        display_name="Glints",
        login_url="https://glints.com/id/signin",
        login_marker="profile",
        cookie_domain_match="glints",
        notes="Google OAuth. User menu appears in top nav when logged in.",
    ),
    "dealls": SourceSpec(
        source_id="dealls",
        display_name="Dealls",
        login_url="https://dealls.com/login",
        login_marker="",
        cookie_domain_match="dealls",
        notes="Email/password. URL may be deprecated; verify before use.",
    ),
    "jobstreet": SourceSpec(
        source_id="jobstreet",
        display_name="JobStreet Indonesia",
        login_url="https://id.jobstreet.com/id/login",
        login_marker="",
        cookie_domain_match="jobstreet",
        notes="SEEK Asia ToS restricts automated collection. Owner-gated browser only.",
    ),
}


PW_PROFILE = Path.home() / ".cache" / "ms-playwright-mcp" / "mcp-chrome-2f137e4"
STATE_DIR = Path.home() / ".local" / "share" / "xninetzy" / "auth" / "profiles" / "playwright-mcp-shared"
STATE_FILE = STATE_DIR / "storage_state.json"


async def phase1_oauth_login(sources: list[str], headed: bool = True) -> dict[str, bool]:
    from playwright.async_api import async_playwright

    print("\n=== Phase 1: OAuth login (owner present) ===")
    print("Headed browser will open for each site. Login manually, then close window.")

    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        page = await ctx.new_page()

        for sid in sources:
            spec = SOURCES.get(sid)
            if not spec:
                continue
            print(f"\n[{spec.display_name}] Opening {spec.login_url}")
            print("  -> Login manually (Google OAuth recommended).")
            print("  -> When done, navigate AWAY from login page (e.g., to /jobs).")
            print("  -> Then press Enter here to capture cookies and continue.")
            try:
                await page.goto(spec.login_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"  WARN: could not open login page: {e}")
            input(f"  Press Enter when [{sid}] login is complete...")
            await page.content()
            cookies = await ctx.cookies()
            relevant = [c for c in cookies if spec.cookie_domain_match in c.get("domain", "")]
            print(f"  Captured {len(relevant)} cookies for {spec.cookie_domain_match}")
            results[sid] = len(relevant) > 0

        all_cookies = await ctx.cookies()
        origins = []
        save_storage_state(all_cookies, origins)
        print(f"\n[OK] Saved {len(all_cookies)} cookies to {STATE_FILE}")

        await browser.close()
    return results


def save_storage_state(cookies: list[dict], origins: list[dict]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.chmod(0o700)
    state = {"cookies": cookies, "origins": origins}
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.chmod(0o600)
    tmp.replace(STATE_FILE)


async def phase2_scrape(
    sources: list[str], keyword: str, location: str, work_mode: str, max_results: int,
) -> dict[str, dict]:
    print("\n=== Phase 2: Scrape via xninetzy ===")

    import importlib
    import xninetzy.os.auth.browser.gateway as gateway_mod
    importlib.reload(gateway_mod)
    from xninetzy.os.research.sources import kalibrr, glints, dealls, jobstreet_id as jsid

    adapter_map = {
        "kalibrr": kalibrr.KalibrrAdapter,
        "glints": glints.GlintsAdapter,
        "dealls": dealls.DeallsAdapter,
        "jobstreet": jsid.JobstreetIDAdapter,
    }

    url_map = {
        "kalibrr": kalibrr.KalibrrAdapter().build_search_url(keyword),
        "glints": (
            f"https://glints.com/id/opportunities/jobs/explore"
            f"?keyword={keyword}&country=ID&locationName={location.replace(' ', '+')}"
            f"&jobTypes=INTERNSHIP&workArrangementOptions=HYBRID"
        ),
        "dealls": dealls.DeallsAdapter().build_search_url(keyword),
        "jobstreet": f"https://id.jobstreet.com/id/job-search?keywords={keyword}&location=Indonesia",
    }

    from xninetzy.os.auth.browser.gateway import launch_local_browser, close_local_browser, _OPEN_HANDLES
    from xninetzy.os.research.sources.browser_session import GatewayBrowserSession as _GBS

    canonical_session_id = "oauth-workflow"
    canonical_owner = "oauth-flow"
    await launch_local_browser(
        session_id=canonical_session_id,
        owner=canonical_owner,
        headless=True,
    )
    shared_session = _GBS(owner=canonical_owner)
    shared_session._session_id = canonical_session_id
    shared_session._handle = _OPEN_HANDLES[canonical_session_id]
    shared_session._page = shared_session._handle["context"].pages[0] if shared_session._handle["context"].pages else None

    results = {}
    try:
        for sid in sources:
            if sid not in adapter_map:
                continue
            print(f"\n[{sid}] scraping...")
            import xninetzy.os.research.sources.browser_session as bs
            bs._SHARED_SESSION = shared_session
            adapter = adapter_map[sid]()
            adapter._session = shared_session
            url = url_map[sid]
            try:
                html = await adapter._fetch_html(url)
                title = html.split("<title>")[1].split("</title>")[0][:80] if "<title>" in html else "?"
                is_blocked = any(
                    x in title.lower()
                    for x in ["firewall", "not available", "just a moment", "login", "log-in", "sign in", "masuk"]
                )
                has_jobs = any(
                    x in html.lower()
                    for x in ["jobcard", "opportunityscard", "k-list-item", "job-card", "deallscard", "/loker/", "job-article"]
                )
                jobs = adapter.parse_jobs(html, query=keyword, limit=max_results) if has_jobs else []
                results[sid] = {
                    "url": url,
                    "title": title,
                    "html_len": len(html),
                    "blocked": is_blocked,
                    "has_jobs": has_jobs,
                    "jobs_found": len(jobs),
                    "jobs_sample": [
                        {
                            "title": j.title,
                            "company": j.author,
                            "url": j.url,
                            "snippet": (j.snippet or "")[:120],
                        }
                        for j in jobs[:5]
                    ],
                }
                print(f"  title={title[:60]}")
                print(f"  html_len={len(html)} blocked={is_blocked} has_jobs={has_jobs}")
                print(f"  jobs_extracted={len(jobs)}")
            except Exception as exc:
                results[sid] = {"url": url, "error": str(exc)[:200]}
                print(f"  ERROR: {exc}")
    finally:
        await close_local_browser(session_id=canonical_session_id)

    return results


def cookies_age_hours(source_id: str) -> float | None:
    if not STATE_FILE.exists():
        return None
    data = json.loads(STATE_FILE.read_text())
    src = SOURCES.get(source_id)
    if not src:
        return None
    relevant = [
        c for c in data.get("cookies", [])
        if src.cookie_domain_match in c.get("domain", "")
    ]
    if not relevant:
        return None
    return (time.time() - STATE_FILE.stat().st_mtime) / 3600


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OAuth + scrape workflow")
    p.add_argument("--sources", default="kalibrr,glints,dealls,jobstreet")
    p.add_argument("--keyword", default="intern")
    p.add_argument("--location", default="Surabaya")
    p.add_argument("--work-mode", default="hybrid", choices=["any", "remote", "hybrid", "onsite"])
    p.add_argument("--max-results", type=int, default=30)
    p.add_argument("--login-only", action="store_true")
    p.add_argument("--scrape-only", action="store_true")
    p.add_argument("--headed", action="store_true", default=True)
    p.add_argument("--status", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    if args.status:
        print("=== Cookie status ===")
        for sid in sources:
            if sid not in SOURCES:
                print(f"  [{sid}] unknown source")
                continue
            age = cookies_age_hours(sid)
            if age is None:
                print(f"  [{SOURCES[sid].display_name}] no cookies")
            else:
                fresh = age < 24
                print(f"  [{SOURCES[sid].display_name}] age={age:.1f}h {'FRESH' if fresh else 'STALE'}")
        return 0

    if not args.scrape_only:
        results = asyncio.run(phase1_oauth_login(sources, headed=args.headed))
        failed = [sid for sid, ok in results.items() if not ok]
        if failed:
            print(f"\nWARN: No cookies captured for: {failed}")
            print("  Re-run script and complete login manually for those sites.")

    if not args.login_only:
        results = asyncio.run(phase2_scrape(
            sources, args.keyword, args.location, args.work_mode, args.max_results
        ))
        print("\n=== Summary ===")
        for sid, r in results.items():
            if "error" in r:
                print(f"  [{sid}] ERROR: {r['error']}")
            else:
                status = "[OK]" if r.get("has_jobs") and not r.get("blocked") else "[FAIL]"
                print(f"  {status} [{sid}] title={r.get('title','')[:40]} jobs={r.get('jobs_found',0)}")
        out = Path("/tmp/kilo/oauth_workflow_result.json")
        out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\nFull results saved to: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
