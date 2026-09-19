from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_READ_ONLY,
    SideEffectClass,
    classify_side_effect,
)


MAX_ARGS_BYTES: int = 64 * 1024


@dataclass(frozen=True, slots=True)
class InvocationRequest:
    request_id: str
    intent: str
    capability: str
    context_key: str
    query: str
    args: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    side_effect: str | None = None
    idempotency_key: str | None = None
    approval_id: int | None = None
    min_trust_tier: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InvocationContext:
    request: InvocationRequest
    side_effect_class: SideEffectClass
    args_bytes: int
    args_hash: str


@dataclass(frozen=True, slots=True)
class InvocationResult:
    request_id: str
    provider_id: str
    capability: str
    outcome: str
    latency_ms: int | None
    payload: Any = None
    error: str | None = None
    audited: bool = False


def _approx_args_size(args: tuple[tuple[str, Any], ...]) -> int:
    total = 0
    for key, value in args:
        total += len(str(key).encode("utf-8"))
        total += len(repr(value).encode("utf-8"))
        total += 4
    return total


def _args_hash(args: tuple[tuple[str, Any], ...]) -> str:
    import hashlib
    parts: list[str] = []
    for key, value in args:
        parts.append(f"{key}={value!r}")
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def validate_invocation_request(request: InvocationRequest) -> None:
    if not request.request_id or not request.request_id.strip():
        raise ValueError("request_id required")
    if not request.capability or not request.capability.strip():
        raise ValueError("capability required")
    if not request.context_key or not request.context_key.strip():
        raise ValueError("context_key required")
    if not request.intent or not request.intent.strip():
        raise ValueError("intent required")
    if request.query is None:
        raise ValueError("query must be a string (use '' for non-NL capabilities)")
    side_effect_name = (
        request.side_effect if request.side_effect is not None else SIDE_EFFECT_READ_ONLY
    )
    cls = classify_side_effect(side_effect_name)
    if cls.requires_idempotency_key and not request.idempotency_key:
        raise ValueError(
            f"side_effect={cls.name} requires idempotency_key"
        )
    size = _approx_args_size(request.args)
    if size > MAX_ARGS_BYTES:
        raise ValueError(
            f"args too large: {size} bytes (max {MAX_ARGS_BYTES})"
        )


def build_invocation_context(request: InvocationRequest) -> InvocationContext:
    validate_invocation_request(request)
    cls = classify_side_effect(request.side_effect)
    return InvocationContext(
        request=request,
        side_effect_class=cls,
        args_bytes=_approx_args_size(request.args),
        args_hash=_args_hash(request.args),
    )


def is_writing_side_effect(name: str | None) -> bool:
    cls = classify_side_effect(name)
    return cls.name in (
        SIDE_EFFECT_IDEMPOTENT_WRITE,
        SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        SIDE_EFFECT_EXTERNAL,
        SIDE_EFFECT_IRREVERSIBLE,
    )
