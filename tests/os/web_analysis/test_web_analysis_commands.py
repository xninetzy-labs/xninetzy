from app.xninetzy.ecosystem.command_router import (
    parse_captcha_reply,
    parse_command,
)
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
    assert parse_command("/uacc-login") == ("uacc_login_start", {})
    assert parse_command("/uacc-captcha abc_123 A1-2") == (
        "uacc_login_submit_captcha",
        {"challenge_id": "abc_123", "captcha_answer": "A1-2"},
    )
    assert parse_command("/uacc-login-cancel abc_123") == (
        "uacc_login_cancel",
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
        {"site_slug": "hebat", "authenticated": True},
    )
    assert parse_command("/web-discover 2 https://example.com/learning") == (
        "web_discover",
        {"source_url": "https://example.com/learning", "depth": 2},
    )
    assert parse_command("/web-refresh mahasiswa") == (
        "web_analysis_refresh",
        {"site_slug": "mahasiswa", "authenticated": True},
    )
    assert parse_command("/web-analysis uacc") == (
        "web_analysis_status",
        {"site_slug": "uacc"},
    )
    assert parse_command("/web-refresh uacc") == (
        "web_analysis_refresh",
        {"site_slug": "uacc", "authenticated": True},
    )


def test_new_tools_registered():
    names = get_tool_names()
    assert "web_analysis_status" in names
    assert "web_analysis_refresh" in names
    assert "web_analysis_catalog" in names
    assert "web_discover" in names
    assert "web_fetch" in names
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
    assert "uacc_info" in names
    assert "uacc_login_start" in names
    assert "uacc_login_submit_captcha" in names
    assert "uacc_login_cancel" in names
    assert "uacc_session_status" in names
    assert "uacc_logout" in names


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


def test_web_catalog_command():
    assert parse_command("/web-pages qa") == ("web_analysis_catalog", {"site_slug": "qa"})
    assert parse_command("/web-pages uacc") == ("web_analysis_catalog", {"site_slug": "uacc"})


def test_captcha_reply_routes_uacc_when_replying_to_uacc_caption():
    metadata = {
        "isReplyToBot": True,
        "quotedMessageText": (
            "Login UACC\n\nBalas: /uacc-captcha D0wr0fxxBGpG-HHh JAWABAN\n"
            "Berlaku sampai: 2026-08-05T07:54:36+00:00\n\n"
            "CAPTCHA harus dijawab manual oleh owner."
        ),
    }
    assert parse_captcha_reply("31", metadata) == (
        "uacc_login_submit_captcha",
        {"challenge_id": "D0wr0fxxBGpG-HHh", "captcha_answer": "31"},
    )


def test_captcha_reply_routes_cyber_when_replying_to_cyber_caption():
    metadata = {
        "isReplyToBot": True,
        "quotedMessageText": (
            "Login Cyber Campus\n\nBalas: /captcha abc_123 JAWABAN\n"
            "Berlaku sampai: 2026-08-05T00:00:00+00:00\n\n"
            "CAPTCHA harus dijawab manual oleh owner."
        ),
    }
    assert parse_captcha_reply("50", metadata) == (
        "portal_login_submit_captcha",
        {"challenge_id": "abc_123", "captcha_answer": "50"},
    )


def test_captcha_reply_ignored_without_reply_or_caption():
    uacc_caption = {"isReplyToBot": True, "quotedMessageText": "Login UACC\nBalas: /uacc-captcha abc JAWABAN"}
    assert parse_captcha_reply("31", {}) == (None, {})
    assert parse_captcha_reply("31", {"isReplyToBot": True, "quotedMessageText": "Reminder tugas besok"}) == (None, {})
    assert parse_captcha_reply("31", {"isReplyToBot": True, "quotedMessageText": "Cyber Campus"}) == (None, {})
    assert parse_captcha_reply("ini bukan angka", uacc_caption) == (None, {})
