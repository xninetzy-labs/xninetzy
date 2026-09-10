from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.config import get_settings


def vault_path() -> Path:
    settings = get_settings()
    mounted_path = Path(settings.OBSIDIAN_VAULT_PATH).expanduser()
    if mounted_path.exists():
        return mounted_path.resolve()

    # Local development runs outside Docker, so use the host vault directly.
    return Path(settings.OBSIDIAN_VAULT_HOST_PATH).expanduser().resolve()
