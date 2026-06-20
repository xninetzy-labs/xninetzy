from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.config import get_settings


def vault_path() -> Path:
    return Path(get_settings().OBSIDIAN_VAULT_PATH).resolve()
