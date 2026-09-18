from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class SourceCategory(StrEnum):
    PAPER = "paper"
    CODE = "code"
    DATASET = "dataset"
    NEWS = "news"
    COMPANY = "company"
    MODEL = "model"
    BENCHMARK = "benchmark"
    SECURITY = "security"
    PATENT = "patent"
    ECONOMICS = "economics"
    GEOGRAPHIC = "geographic"
    ENTITY = "entity"
    GENERAL = "general"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class RateLimit:
    requests_per_minute: int
    burst: int = 1


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_base_seconds: float = 0.5
    backoff_max_seconds: float = 8.0


@dataclass(frozen=True)
class CircuitBreaker:
    failure_threshold: int = 5
    open_duration_seconds: float = 60.0


@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    source: str
    source_type: str
    published_at: str | None
    updated_at: str | None
    author: str | None
    snippet: str
    content: str | None
    language: str
    license: str | None
    retrieved_at: str
    confidence: float
    primary_source: bool
    citation: str | None
    identifiers: dict[str, str] = field(default_factory=dict)


def make_retrieved_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_idempotency_key(*parts: object) -> str:
    joined = "|".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:32]


class SourceAdapter(ABC):
    id: str
    category: SourceCategory
    base_url: str
    requires_api_key: bool
    rate_limit: RateLimit
    retry: RetryPolicy
    circuit_breaker: CircuitBreaker

    @abstractmethod
    async def search(
        self, query: str, limit: int = 10, **kwargs: object
    ) -> list[SourceRecord]:
        ...

    @abstractmethod
    async def fetch(self, identifier: str) -> SourceRecord | None:
        ...

    @abstractmethod
    async def health(self) -> HealthStatus:
        ...
