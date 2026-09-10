from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.notes.organization_service import ObsidianOrganizationService
from app.xninetzy.os.notes.template_service import TemplateService


def _configure(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "container"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(vault))
    monkeypatch.setenv("OBSIDIAN_BACKUP_BEFORE_WRITE", "true")
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "db.sqlite3"))
    get_settings.cache_clear()
    init_db()
    return vault


def test_template_paths_use_canonical_folders(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    daily_path, _ = TemplateService().daily_note("2026-08-02")
    learning_path, _ = TemplateService().learning_note("Data Analytics")
    project_path, _ = TemplateService().project_note("Xninetzy OS")
    task_path, _ = TemplateService().task_note("Write docs")

    assert daily_path == "Daily/2026/2026-08-02.md"
    assert learning_path == "Learning/Notes/data-analytics.md"
    assert project_path == "Projects/xninetzy-os/README.md"
    assert task_path == "Life/Tasks/write-docs.md"
    get_settings.cache_clear()


def test_preview_and_apply_migrates_legacy_note_and_links(monkeypatch, tmp_path):
    vault = _configure(monkeypatch, tmp_path)
    (vault / "Daily").mkdir()
    (vault / "Daily" / "2026-08-02.md").write_text("# Daily\n", encoding="utf-8")
    (vault / "Reference.md").write_text("See [[Daily/2026-08-02]].\n", encoding="utf-8")

    service = ObsidianOrganizationService()
    preview = service.preview()
    move = next(item for item in preview["moves"] if item["source"] == "Daily/2026-08-02.md")
    result = service.apply({"moves": [move]})

    target = vault / "Daily" / "2026" / "2026-08-02.md"
    assert target.exists()
    assert not (vault / "Daily" / "2026-08-02.md").exists()
    assert result["applied"]
    assert "Daily/2026/2026-08-02" in (vault / "Reference.md").read_text(encoding="utf-8")
    assert (vault / ".backup").exists()
    get_settings.cache_clear()


def test_structure_and_moc_are_idempotent(monkeypatch, tmp_path):
    vault = _configure(monkeypatch, tmp_path)
    service = ObsidianOrganizationService()
    first = service.ensure_structure()
    second = service.ensure_structure()
    service.refresh_mocs()
    service.refresh_mocs()

    assert first["created"]
    assert second["created"] == []
    assert (vault / "Home.md").exists()
    assert (vault / "Learning" / "MOCs" / "Index.md").exists()
    assert service.verify()["healthy"]
    get_settings.cache_clear()
