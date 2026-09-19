from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class InvocableResult:
    payload: Any
    latency_ms: int
    error: str | None = None
    metadata: dict[str, Any] | None = None


class InvocableError(RuntimeError):
    pass


class Invocable(ABC):
    provider_id: str

    @abstractmethod
    def invoke(self, capability: str, args: tuple[tuple[str, Any], ...]) -> InvocableResult:
        raise NotImplementedError

    @abstractmethod
    def is_healthy(self) -> bool:
        raise NotImplementedError


_INVOCABLE_REGISTRY: dict[str, Invocable] = {}


def register_invokable(provider_id: str, invocable: Invocable) -> None:
    if not provider_id or not provider_id.strip():
        raise ValueError("provider_id required for registration")
    if not isinstance(invocable, Invocable):
        raise TypeError("invocable must subclass Invocable")
    _INVOCABLE_REGISTRY[provider_id] = invocable


def resolve_invokable(provider_id: str) -> Invocable | None:
    return _INVOCABLE_REGISTRY.get(provider_id)


def unregister_invokable(provider_id: str) -> bool:
    return _INVOCABLE_REGISTRY.pop(provider_id, None) is not None


def clear_invokable_registry() -> None:
    _INVOCABLE_REGISTRY.clear()


def registered_invokable_ids() -> tuple[str, ...]:
    return tuple(sorted(_INVOCABLE_REGISTRY))
