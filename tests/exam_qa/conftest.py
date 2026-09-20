from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.db.migrations import run_migrations


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "exam_qa.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    yield db_file