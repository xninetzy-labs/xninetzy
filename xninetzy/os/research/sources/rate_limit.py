from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from xninetzy.os.research.sources.base import CircuitBreaker, RetryPolicy


@dataclass
class _Bucket:
    window_start: float = 0.0
    count: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@dataclass
class _BreakerState:
    failure_count: int = 0
    open_until: float = 0.0
    state: str = "closed"


class RateLimiter:
    def __init__(self, requests_per_minute: int, burst: int = 1) -> None:
        self._rpm = max(1, requests_per_minute)
        self._burst = max(1, burst)
        self._bucket = _Bucket()

    async def acquire(self) -> None:
        async with self._bucket.lock:
            now = time.monotonic()
            if now - self._bucket.window_start >= 60.0:
                self._bucket.window_start = now
                self._bucket.count = 0
            if self._bucket.count >= self._rpm:
                sleep_for = 60.0 - (now - self._bucket.window_start)
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
                self._bucket.window_start = time.monotonic()
                self._bucket.count = 0
            self._bucket.count += 1


class CircuitBreakerGuard:
    def __init__(self, breaker: CircuitBreaker) -> None:
        self._breaker = breaker
        self._state = _BreakerState()
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            if self._state.state == "open":
                if now >= self._state.open_until:
                    self._state.state = "half_open"
                    return True
                return False
            return True

    async def record_success(self) -> None:
        async with self._lock:
            self._state.failure_count = 0
            self._state.state = "closed"
            self._state.open_until = 0.0

    async def record_failure(self) -> None:
        async with self._lock:
            self._state.failure_count += 1
            if (
                self._state.state == "half_open"
                or self._state.failure_count >= self._breaker.failure_threshold
            ):
                self._state.state = "open"
                self._state.open_until = (
                    time.monotonic() + self._breaker.open_duration_seconds
                )


async def retry_async(
    policy: RetryPolicy, operation: object, *args: object, **kwargs: object
) -> object:
    attempt = 0
    delay = policy.backoff_base_seconds
    while True:
        attempt += 1
        try:
            result = await operation(*args, **kwargs)
            return result
        except Exception:
            if attempt >= policy.max_attempts:
                raise
            await asyncio.sleep(min(delay, policy.backoff_max_seconds))
            delay *= 2
