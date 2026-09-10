from datetime import datetime, timedelta, timezone

import pytest

from app.xninetzy.os.web_analysis.cache_manager import AnalysisBusyError, AnalysisCacheManager
from app.xninetzy.os.web_analysis.models import ModuleRecord, SiteAnalysis
from app.xninetzy.os.web_analysis.selectors_registry import extract_module_structure


def _analysis(timestamp: str) -> SiteAnalysis:
    return SiteAnalysis(
        site_slug="mahasiswa",
        site_name="Cybercampus Mahasiswa UNAIR",
        base_url="https://mahasiswa.unair.ac.id",
        analyzed_at=timestamp,
        auth_status="human_verification_required",
        modules=[
            ModuleRecord(
                name="krs_availability",
                path="/krs",
                classification="monitor_only",
                selectors=["table"],
                field_names=[],
                structure_hash="a" * 64,
                analyzed_at=timestamp,
            )
        ],
        protection_flags=["Submit KRS hanya read/notify; tidak boleh submit otomatis."],
    )


def test_cache_writes_json_and_privacy_safe_markdown(tmp_path):
    cache = AnalysisCacheManager(root=tmp_path)
    now = datetime.now(timezone.utc).isoformat()
    path = cache.save(_analysis(now))
    markdown = path.read_text(encoding="utf-8")
    assert path.stat().st_mode & 0o777 == 0o644
    assert "DO NOT AUTOMATE" in markdown
    assert "data akademik owner disimpan terpisah dan terenkripsi" in markdown
    assert "Submit KRS hanya read/notify" in markdown
    assert cache.load("mahasiswa").modules[0].classification == "monitor_only"
    assert cache.is_stale("mahasiswa") is False


def test_cache_staleness_and_lease(tmp_path):
    cache = AnalysisCacheManager(root=tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    cache.save(_analysis(old))
    assert cache.is_stale("mahasiswa", ttl_days=14) is True
    with cache.lease("mahasiswa"):
        with pytest.raises(AnalysisBusyError):
            with cache.lease("mahasiswa"):
                pass


def test_structure_extractor_keeps_names_not_values():
    html = """
    <main><form><input name="username" value="secret-user">
    <input name="password" value="secret-pass"></form>
    <table><tr><td>APSI</td></tr></table></main>
    """
    module = extract_module_structure("https://mahasiswa.unair.ac.id/login", html)
    dumped = module.model_dump_json()
    assert module.name == "login"
    assert module.classification == "contains_action"
    assert module.field_names == ["password", "username"]
    assert "secret-user" not in dumped
    assert "secret-pass" not in dumped
    assert "APSI" not in dumped
