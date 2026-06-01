from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DEEPSEEK_API_KEY", "test")
os.environ.setdefault("SQLITE_PATH", "/tmp/xninetzy-pytest.sqlite3")
