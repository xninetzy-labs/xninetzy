from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from xninetzy.tools.registry import get_all_tools, get_tool_names


def test_repo_file_outline_registered_with_manifest():
    names = get_tool_names()
    assert "repo_file_outline" in names
    from xninetzy.tools.manifest import manifest_for

    manifest = manifest_for("repo_file_outline")
    assert manifest.name == "repo_file_outline"
    assert manifest.feature_pack.value == "core"


def test_lightning_episode_get_registered_with_manifest():
    names = get_tool_names()
    assert "lightning_episode_get" in names
    from xninetzy.tools.manifest import manifest_for

    manifest = manifest_for("lightning_episode_get")
    assert manifest.name == "lightning_episode_get"
    assert manifest.feature_pack.value == "core"


def test_repo_file_outline_executes_on_python_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "out.db"))
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    target = tmp_path / "sample.py"
    target.write_text(
        'def alpha(x: int) -> int:\n    """double x"""\n    return x * 2\n\nclass Beta:\n    def __init__(self):\n        pass\n'
    )
    from xninetzy.tools.ecosystem.repo_tools import repo_file_outline

    out = repo_file_outline.invoke({"path": "sample.py", "root": str(tmp_path)})
    import json

    payload = json.loads(out)
    assert payload["found"] is True
    assert payload["symbol_count"] >= 2
    names = [s["name"] for s in payload["symbols"]]
    assert "alpha" in names
    assert "Beta" in names


def test_lightning_episode_get_returns_not_found_for_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "lg.db"))
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    from xninetzy.os.lightning.tools import lightning_episode_get

    out = lightning_episode_get.invoke({"episode_id": "E-missing", "sender_id": "owner-1"})
    import json

    payload = json.loads(out)
    assert payload["found"] is False
    assert payload["episode_id"] == "E-missing"


def test_lightning_episode_get_returns_existing_episode(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "lg.db"))
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    from xninetzy.os.lightning.rl import start_episode
    from xninetzy.os.lightning.tools import lightning_episode_get

    ep = start_episode(
        owner_scope="owner-1",
        interface="mcp",
        chat_id="chat-1",
        task_type="integration_test",
        strategy_id="baseline",
    )
    out = lightning_episode_get.invoke({"episode_id": ep["episode_id"], "sender_id": "owner-1"})
    import json

    payload = json.loads(out)
    assert payload["found"] is True
    assert payload["episode"]["task_type"] == "integration_test"


def test_tool_count_consistent_between_registry_paths():
    by_get_all = {t.name for t in get_all_tools()}
    by_names = set(get_tool_names())
    assert by_get_all == by_names
