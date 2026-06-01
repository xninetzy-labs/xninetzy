from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


class ChatStore:
    def get_recent(self, chat_id: str, limit: int | None = None) -> list[BaseMessage]:
        limit = limit or get_settings().CHAT_HISTORY_LIMIT
        init_db()
        with connect() as conn:
            rows = conn.execute(
                "SELECT role, content, tool_name FROM chat_messages "
                "WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

        messages: list[BaseMessage] = []
        for row in reversed(rows):
            role, content = row["role"], row["content"]
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        return messages

    def save_messages(self, chat_id: str, messages: list[BaseMessage]) -> None:
        init_db()
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        rows = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
                content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                rows.append((chat_id, role, content, None, now))
            elif isinstance(msg, AIMessage):
                role = "assistant"
                content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                rows.append((chat_id, role, content, None, now))

        if not rows:
            return
        with connect() as conn:
            conn.executemany(
                "INSERT INTO chat_messages (chat_id, role, content, tool_name, created_at) VALUES (?,?,?,?,?)",
                rows,
            )

    def clear(self, chat_id: str) -> None:
        init_db()
        with connect() as conn:
            conn.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
