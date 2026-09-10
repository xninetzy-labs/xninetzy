from __future__ import annotations

import secrets

from fastapi import Header, HTTPException

from app.xninetzy.core.config import get_settings


async def require_api_key(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    key = settings.AI_API_KEY
    if not key:
        if settings.AI_API_AUTH_REQUIRED:
            raise HTTPException(status_code=503, detail="AI API key is not configured")
        return
    provided = authorization or ""
    if not secrets.compare_digest(provided, f"Bearer {key}"):
        raise HTTPException(status_code=401, detail="Invalid API key")
