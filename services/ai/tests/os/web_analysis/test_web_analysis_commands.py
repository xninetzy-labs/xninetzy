from app.xninetzy.ecosystem.command_router import parse_command
from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.models import SiteAnalysis
from app.xninetzy.tools.registry import get_tool_names


def test_local_portal_slash_commands():
    assert parse_command("/cyber-login") == ("portal_login_start", {})
    assert parse_command("/captcha abc_123 A1-2") == (
        "portal_login_submit_captcha",
        {"challenge_id": "abc_123", "captcha_answer": "A1-2"},
    )
    assert parse_command("/cyber-login-cancel abc_123") == (
        "portal_login_cancel",
        {"challenge_id": "abc_123"},
    )
    assert parse_command("/jadwal") == ("portal_schedule", {})
    assert parse_command("/nilai") == (
        "portal_grades",
        {"academic_period": "latest"},
    )
    assert parse_command("/grade-token grade_123 12345") == (
        "__portal_grade_token_submit",
        {"challenge_id": "grade_123", "token": "12345"},
    )
    assert parse_command("/portalinfo") == ("portal_info", {})
    assert parse_command("/portal-nav") == ("portal_navigation", {})
    assert parse_command("/krs-capabilities") == ("portal_krs_capabilities", {})
    assert parse_command("/krs-watcher") == ("portal_krs_watcher_status", {})
    assert parse_command("/web-analysis mahasiswa") == (
        "web_analysis_status",
        {"site_slug": "mahasiswa"},
    )
    assert parse_command("/web-refresh hebat") == (
        "web_analysis_refresh",
        {"site_slug": "hebat", "authenticated": False},
    )
    assert parse_command("/web-refresh mahasiswa") == (
        "web_analysis_refresh",
        {"site_slug": "mahasiswa", "authenticated": True},
    )


def test_new_tools_registered():
    names = get_tool_names()
    assert "web_analysis_status" in names
    assert "web_analysis_refresh" in names
    assert "portal_info" in names
    assert "portal_navigation" in names
    assert "portal_krs_capabilities" in names
    assert "portal_schedule" in names
    assert "portal_grades" in names
    assert "__portal_grade_token_submit" not in names
    assert "portal_krs_watcher_status" in names
    assert "portal_login_start" in names
    assert "portal_login_submit_captcha" in names
    assert "portal_login_cancel" in names
    assert "portal_session_status" in names
    assert "portal_logout" in names


def test_authenticated_crawl_does_not_reuse_public_or_challenge_cache():
    def cached(auth_status):
        return SiteAnalysis(
            site_slug="mahasiswa",
            site_name="Cyber Campus",
            base_url="https://mahasiswa.unair.ac.id",
            analyzed_at="2026-07-29T00:00:00+00:00",
            auth_status=auth_status,
        )

    assert AnalyzerService._cache_satisfies_request(
        cached("authenticated"), True
    )
    assert not AnalyzerService._cache_satisfies_request(
        cached("human_verification_required"), True
    )
    assert not AnalyzerService._cache_satisfies_request(
        cached("public"), True
    )
    assert AnalyzerService._cache_satisfies_request(cached("public"), False)


def test_academic_links_are_prioritized_for_bounded_crawl():
    links = [
        ("https://mahasiswa.unair.ac.id/perpustakaan", "Buku"),
        ("https://mahasiswa.unair.ac.id/krs", "Rencana Studi"),
        ("https://mahasiswa.unair.ac.id/nilai", "Nilai Akademik"),
    ]

    ordered = sorted(
        links,
        key=lambda item: AnalyzerService._link_priority(item[0], item[1]),
    )

    assert [item[0] for item in ordered[:2]] == [
        "https://mahasiswa.unair.ac.id/krs",
        "https://mahasiswa.unair.ac.id/nilai",
    ]
