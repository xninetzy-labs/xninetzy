"""Input normalization for WhatsApp / API / media payloads."""
from __future__ import annotations

from typing import Any

from app.xninetzy.context.packet import ContextPacket, Source


def normalize(payload: dict[str, Any], source: Source = "api") -> ContextPacket:
    """Turn a raw interface payload into a ContextPacket.

    Tolerant of the common field shapes used across interfaces (text/message/body).
    """
    text = (
        payload.get("text")
        or payload.get("message")
        or payload.get("body")
        or ""
    ).strip()
    return ContextPacket(
        text=text,
        chat_id=payload.get("chat_id") or payload.get("jid"),
        source=source,
        attachments=list(payload.get("attachments") or []),
        metadata={k: v for k, v in payload.items() if k not in {"text", "message", "body"}},
    )
