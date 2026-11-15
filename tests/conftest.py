from __future__ import annotations

import os
import sys
import tempfile
import atexit
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLAZ_API_KEY", "test-flaz-key")
os.environ.setdefault("FLAZ_BASE_URL", "https://ai.flaz.id/v1")
os.environ.setdefault("FLAZ_MODEL", "deepseek-v4-pro")
_test_state = tempfile.TemporaryDirectory(prefix="xninetzy-pytest-")
atexit.register(_test_state.cleanup)
_test_root = Path(_test_state.name)
os.environ["MCP_RUNTIME_MODE"] = "container"
os.environ["SQLITE_PATH"] = str(_test_root / "tests.sqlite3")
for _setting in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
    os.environ.pop(_setting, None)
for _setting in (
    "DATA_DIR", "OUTPUT_DIR", "BACKUP_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR",
    "UNTRACKED_OUTPUT_DIR", "HEBAT_DATA_DIR", "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_HOST_PATH",
    "OBSIDIAN_VAULT_PATH", "VECTOR_DATA_DIR", "GRAPH_VECTOR_DATA_DIR", "WEB_ANALYSIS_DATA_DIR",
    "VIDEO_OUTPUT_DIR", "XNINETZY_SKILLS_DIR",
):
    os.environ[_setting] = str(_test_root / _setting.lower())
for _setting in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED", "LIGHTNING_ENABLED",
                 "NEO4J_ENABLED", "NEO4J_AUTOSTART_ENABLED", "EXTERNAL_MCP_ENABLED", "OS_SCHEDULER_ENABLED"):
    os.environ[_setting] = "false"


def pytest_configure():
    # Do not let deployment .env select owner stores/providers during collection
    # or tests. Individual tests may explicitly configure their own fixtures.
    from xninetzy.core.config import Settings, get_settings
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
