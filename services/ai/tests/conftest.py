from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLAZ_API_KEY", "test-flaz-key")
os.environ.setdefault("FLAZ_BASE_URL", "https://ai.flaz.id/v1")
os.environ.setdefault("FLAZ_MODEL", "deepseek-v4-pro")
os.environ.setdefault("SQLITE_PATH", "/tmp/xninetzy-pytest.sqlite3")
