from __future__ import annotations

from fastapi import Header, HTTPException

from app.core.config import get_settings


async def require_api_key(authorization: str | None = Header(default=None)) -> None:
    key = get_settings().AI_API_KEY
    if not key:
        return
    if authorization != f"Bearer {key}":
        raise HTTPException(status_code=401, detail="Invalid API key")
