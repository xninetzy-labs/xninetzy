from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PROVIDER_MOCK: str = "mock"
PROVIDER_LOCAL: str = "local"

VALID_PROVIDERS: frozenset[str] = frozenset({PROVIDER_MOCK, PROVIDER_LOCAL})


@dataclass(frozen=True, slots=True)
class ExamProvider:
    provider_id: str
    display_name: str
    offline_only: bool
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


_PROVIDERS: dict[str, ExamProvider] = {
    PROVIDER_MOCK: ExamProvider(
        provider_id=PROVIDER_MOCK,
        display_name="Mock Provider",
        offline_only=True,
        capabilities=("answer:dictionary", "evaluate:exact"),
    ),
    PROVIDER_LOCAL: ExamProvider(
        provider_id=PROVIDER_LOCAL,
        display_name="Local Heuristic Provider",
        offline_only=True,
        capabilities=("answer:heuristic", "evaluate:keyword"),
    ),
}


def resolve_provider(provider_id: str) -> ExamProvider:
    if provider_id not in _PROVIDERS:
        raise ValueError(
            f"unknown provider {provider_id!r}; valid: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[provider_id]


def list_providers() -> tuple[ExamProvider, ...]:
    return tuple(_PROVIDERS[p] for p in sorted(_PROVIDERS))