from __future__ import annotations

from datetime import datetime, timezone

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.providers import LLMProfile, resolve_profile
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db


def _ensure_tables() -> None:
    init_db()
    run_migrations()


def get_preference(user_id: str) -> dict[str, str] | None:
    _ensure_tables()
    with connect() as conn:
        row = conn.execute(
            "SELECT user_id, chat_provider, chat_model, coding_agent "
            "FROM ai_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def save_preference(
    user_id: str,
    *,
    chat_provider: str | None = None,
    chat_model: str | None = None,
    coding_agent: str | None = None,
) -> dict[str, str]:
    current = get_preference(user_id) or {}
    settings = get_settings()
    provider = (
        chat_provider or current.get("chat_provider") or settings.LLM_DEFAULT_PROVIDER
    )
    model = chat_model or current.get("chat_model") or resolve_profile(provider).model
    agent = coding_agent or current.get("coding_agent") or settings.CODING_AGENT_DEFAULT
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ai_preferences
                (user_id, chat_provider, chat_model, coding_agent, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_provider = excluded.chat_provider,
                chat_model = excluded.chat_model,
                coding_agent = excluded.coding_agent,
                updated_at = excluded.updated_at
            """,
            (user_id, provider, model, agent, now),
        )
    return {
        "user_id": user_id,
        "chat_provider": provider,
        "chat_model": model,
        "coding_agent": agent,
    }


def resolve_user_profile(user_id: str) -> LLMProfile:
    preference = get_preference(user_id)
    if preference:
        try:
            return resolve_profile(
                preference["chat_provider"], preference["chat_model"]
            )
        except ValueError:
            pass
    return resolve_profile()
