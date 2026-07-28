from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.security import (
    detect_human_verification,
    has_sensitive_query,
    is_safe_request_method,
    sanitize_endpoint,
)
from app.xninetzy.os.web_analysis.sites import get_site, is_allowed_url


def test_only_get_and_head_are_safe():
    assert is_safe_request_method("GET") is True
    assert is_safe_request_method("head") is True
    assert is_safe_request_method("POST") is False
    assert is_safe_request_method("DELETE") is False


def test_human_verification_is_stop_signal():
    assert detect_human_verification('<img alt="captcha">') is True
    assert detect_human_verification('<div class="g-recaptcha"></div>') is True
    assert detect_human_verification("<main>Dashboard akademik</main>") is False


def test_endpoint_never_persists_values_or_sensitive_keys():
    endpoint = sanitize_endpoint(
        "GET",
        "https://mahasiswa.unair.ac.id/api/jadwal?semester=2026&token=secret&course=APSI",
        200,
        "application/json; charset=utf-8",
    )
    assert endpoint is not None
    assert endpoint.path == "/api/jadwal"
    assert endpoint.query_keys == ["course", "semester"]
    assert "2026" not in endpoint.model_dump_json()
    assert "secret" not in endpoint.model_dump_json()
    assert sanitize_endpoint("POST", "https://example.test/submit", 200, None) is None
    assert has_sensitive_query("https://example.test/page?id=1") is False
    assert has_sensitive_query("https://example.test/page?sesskey=secret") is True


def test_allowlist_and_mutating_paths_are_enforced():
    site = get_site("mahasiswa")
    assert is_allowed_url(site, "https://mahasiswa.unair.ac.id/") is True
    assert is_allowed_url(site, "https://evil.example/") is False
    assert AnalyzerService._safe_to_visit(site, "https://mahasiswa.unair.ac.id/jadwal") is True
    assert AnalyzerService._safe_to_visit(site, "https://mahasiswa.unair.ac.id/logout") is False
    assert AnalyzerService._safe_to_visit(site, "https://mahasiswa.unair.ac.id/krs?editsubmission=1") is False
