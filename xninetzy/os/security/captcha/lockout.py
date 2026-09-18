from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


@dataclass
class _State:
    failures: list[float] = field(default_factory=list)
    cooldown_until: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_state = _State()


def _now_monotonic() -> float:
    return time.monotonic()


async def should_allow_ocr() -> bool:
    settings = get_settings()
    if not settings.XNINETZY_CAPTCHA_OCR_ENABLED:
        return False
    async with _state.lock:
        if _state.cooldown_until > _now_monotonic():
            return False
        window = settings.XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS
        threshold = settings.XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD
        cutoff = _now_monotonic() - window
        _state.failures = [t for t in _state.failures if t >= cutoff]
        if len(_state.failures) >= threshold:
            cooldown = settings.XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS
            _state.cooldown_until = _now_monotonic() + cooldown
            logger.warning(
                "captcha OCR lockout triggered: %d failures within %ds; cooldown %ds",
                len(_state.failures),
                window,
                cooldown,
            )
            return False
        return True


async def record_failure() -> None:
    async with _state.lock:
        _state.failures.append(_now_monotonic())


async def record_success() -> None:
    async with _state.lock:
        _state.failures.clear()
        _state.cooldown_until = 0.0


def status_snapshot() -> dict[str, object]:
    settings = get_settings()
    return {
        "ocr_enabled": settings.XNINETZY_CAPTCHA_OCR_ENABLED,
        "min_confidence": settings.XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE,
        "lockout_threshold": settings.XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD,
        "lockout_window_seconds": settings.XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS,
        "cooldown_seconds": settings.XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS,
        "current_failures_in_window": len(_state.failures),
        "cooldown_until_iso": (
            datetime.fromtimestamp(_state.cooldown_until, tz=timezone.utc).isoformat()
            if _state.cooldown_until > _now_monotonic()
            else None
        ),
    }
