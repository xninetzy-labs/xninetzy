from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.xninetzy.os.web_analysis.session_manager import EncryptedProfileStore


class SnapshotManager:
    """Encrypted local-owner academic data cache, separate from structural Markdown."""

    def __init__(self, root: str | Path | None = None, key: str | None = None) -> None:
        self.store = EncryptedProfileStore("snapshots", root=root, key=key)

    def save(
        self,
        site_slug: str,
        module: str,
        items: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> Path:
        return self.store.save(
            profile_id,
            site_slug,
            f"snapshot-{module}",
            {
                "schema_version": 1,
                "module": module,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "items": items,
            },
        )

    def load(
        self,
        site_slug: str,
        module: str,
        ttl_minutes: int | None = None,
        profile_id: str | None = None,
    ) -> dict[str, Any] | None:
        value = self.store.load(profile_id, site_slug, f"snapshot-{module}")
        if not value or ttl_minutes is None:
            return value
        captured = datetime.fromisoformat(str(value["captured_at"]).replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - captured >= timedelta(minutes=ttl_minutes):
            return None
        return value
