from __future__ import annotations

import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.logging import logging
from app.db.sqlite import connect, init_db

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


_TYPE_KW = {
    "learning_profile": ("belajar", "learning", "study", "kuliah", "materi", "paham"),
    "preference": ("suka", "prefer", "lebih suka", "jangan", "biasanya", "selalu"),
    "project_context": ("project", "proyek", "lagi ngerjain", "sedang membuat", "repo"),
    "goal": ("goal", "target", "pengen", "ingin", "mau capai"),
    "deadline": ("deadline", "due", "tenggat", "submit"),
    "habit": ("habit", "kebiasaan", "rutin", "tiap hari"),
}


def classify_memory(content: str) -> str:
    c = content.lower()
    for mtype, kws in _TYPE_KW.items():
        if any(k in c for k in kws):
            return mtype
    return "preference"


def add_memory(
    user_id: str,
    content: str,
    memory_type: str | None = None,
    title: str | None = None,
    importance: float = 0.5,
    source: str = "whatsapp",
    source_message_id: str | None = None,
) -> dict:
    init_db()
    now = _now()
    mt = memory_type or classify_memory(content)
    mid = uuid.uuid4().hex[:12]
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO memories
              (memory_id, user_id, memory_type, scope, title, content, importance,
               confidence, source, source_message_id, tags_json, metadata_json,
               is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
            """,
            (mid, user_id, mt, "personal", (title or content.strip()[:60]), content.strip(),
             importance, 0.8, source, source_message_id, "[]", "{}", now, now),
        )
        return {"id": int(cur.lastrowid), "memory_id": mid, "memory_type": mt, "content": content.strip()}


def list_memories(user_id: str, active_only: bool = True, limit: int = 50) -> list[dict]:
    init_db()
    sql = "SELECT * FROM memories WHERE user_id=?"
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY importance DESC, id DESC LIMIT ?"
    with connect() as conn:
        rows = conn.execute(sql, (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def update_memory(user_id: str, memory_pk: int, content: str) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE memories SET content=?, updated_at=? WHERE id=? AND user_id=?",
            (content.strip(), _now(), memory_pk, user_id),
        )
        return cur.rowcount > 0


def forget_memory(user_id: str, memory_pk: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE memories SET is_active=0, updated_at=? WHERE id=? AND user_id=?",
            (_now(), memory_pk, user_id),
        )
        return cur.rowcount > 0


def _cosine(a: list[float], b: list[float]) -> float:
    import numpy as np

    va, vb = np.array(a, dtype="float32"), np.array(b, dtype="float32")
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(va.dot(vb) / (na * nb))


def search_memories(user_id: str, query: str, limit: int = 5) -> list[dict]:
    """Semantic search over active memories (embedding cosine), substring fallback."""
    rows = list_memories(user_id, active_only=True, limit=200)
    if not rows:
        return []
    try:
        from app.knowledge.embeddings import embed_query, embed_texts

        q = embed_query(query)
        embs = embed_texts([r["content"] for r in rows])
        scored = sorted(
            ((_cosine(q, e), r) for e, r in zip(embs, rows)),
            key=lambda x: x[0],
            reverse=True,
        )
        out = [{**r, "score": round(s, 3)} for s, r in scored[:limit] if s > 0.05]
        if out:
            return out
    except Exception as exc:  # pragma: no cover - fallback path
        logger.warning("memory semantic search failed, using substring: %s", exc)
    needle = query.lower()
    return [r for r in rows if needle in r["content"].lower()][:limit]


def format_memories_for_prompt(memories: list[dict]) -> str:
    if not memories:
        return ""
    lines = [f"• [{m['memory_type']}] {m['content']}" for m in memories]
    return "\n[Memory tentang user — pakai jika relevan]\n" + "\n".join(lines) + "\n"
