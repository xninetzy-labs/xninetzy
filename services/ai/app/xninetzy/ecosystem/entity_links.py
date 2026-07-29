from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect


def ensure_entity_link(
    *,
    source_type: str,
    source_id: str | int,
    relation: str,
    target_type: str,
    target_id: str | int,
    chat_id: str | None = None,
    metadata: dict | None = None,
) -> bool:
    """Create an installation-global entity link once; chat_id records origin."""
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        result = conn.execute(
            """
            INSERT OR IGNORE INTO entity_links
              (chat_id, source_type, source_id, relation, target_type, target_id,
               metadata_json, created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                chat_id,
                source_type,
                str(source_id),
                relation,
                target_type,
                str(target_id),
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
            ),
        )
    return result.rowcount > 0
