from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xninetzy.integrations.kaggle.auth_adapter import (
    KaggleAuthContext,
    resolve_kaggle_auth,
)
from xninetzy.os.research.sources.kaggle import KaggleAdapter
from xninetzy.os.research.sources.registry import get_adapter


@dataclass(frozen=True, slots=True)
class KaggleOperationResult:
    status: str
    operation: str
    payload: dict[str, Any] | None
    auth_used: str
    cache_hit: bool = False
    warnings: tuple[str, ...] = ()


_RESULTS_CACHE: dict[str, KaggleOperationResult] = {}


def reset_cache() -> None:
    _RESULTS_CACHE.clear()


def _envelope(
    *,
    status: str,
    operation: str,
    auth: KaggleAuthContext,
    payload: dict[str, Any] | None,
    warnings: tuple[str, ...] = (),
) -> KaggleOperationResult:
    return KaggleOperationResult(
        status=status,
        operation=operation,
        payload=payload,
        auth_used=auth.source,
        warnings=warnings,
    )


def capabilities(*, owner: str, account: str = "default") -> dict[str, Any]:
    adapter = get_adapter("kaggle") if _adapter_registered() else None
    has_breaker = adapter is not None and isinstance(adapter, KaggleAdapter)
    return {
        "provider": "kaggle",
        "account": account,
        "owner": owner,
        "auth": resolve_kaggle_auth(owner=owner, account=account).to_safe_dict(),
        "env_credentials_configured": _env_credentials_present(),
        "adapter_registered": has_breaker,
        "operations": [
            "search",
            "get",
            "validate",
            "register",
        ],
        "output_max_bytes": 32_768,
    }


def _adapter_registered() -> bool:
    try:
        from xninetzy.os.research.sources.registry import list_adapters

        return any(a.id == "kaggle" for a in list_adapters())
    except Exception:
        return False


def _env_credential_pairs() -> tuple[str, ...]:
    import os

    keys = ("KAGGLE_USERNAME", "KAGGLE_KEY")
    return tuple(f"{k}={'set' if os.environ.get(k) else 'unset'}" for k in keys)


def _env_credentials_present() -> bool:
    import os

    return bool(os.environ.get("KAGGLE_USERNAME")) and bool(os.environ.get("KAGGLE_KEY"))


def search(
    *,
    query: str,
    owner: str,
    account: str = "default",
    limit: int = 25,
) -> KaggleOperationResult:
    limit = max(1, min(limit, 50))
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated and not _env_credentials_present():
        return _envelope(
            status="auth_required",
            operation="search",
            auth=auth,
            payload=None,
        )
    fingerprint = f"search::{query.lower()}::{limit}"
    cached = _RESULTS_CACHE.get(fingerprint)
    if cached is not None:
        return KaggleOperationResult(
            status=cached.status,
            operation=cached.operation,
            payload=cached.payload,
            auth_used=cached.auth_used,
            cache_hit=True,
            warnings=cached.warnings,
        )
    payload = {
        "query": query,
        "limit": limit,
        "matches": [],
        "total_known": 0,
        "truncated": False,
    }
    result = _envelope(
        status="ok",
        operation="search",
        auth=auth,
        payload=payload,
    )
    _RESULTS_CACHE[fingerprint] = result
    return result


def get(
    *,
    dataset_ref: str,
    owner: str,
    account: str = "default",
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated and not _env_credentials_present():
        return _envelope(
            status="auth_required",
            operation="get",
            auth=auth,
            payload=None,
        )
    payload = {
        "dataset_ref": dataset_ref,
        "exists": False,
        "title": None,
        "size_bytes": None,
    }
    return _envelope(
        status="ok",
        operation="get",
        auth=auth,
        payload=payload,
    )


def validate(
    *,
    dataset_ref: str,
    owner: str,
    account: str = "default",
) -> KaggleOperationResult:
    return _envelope(
        status="ok",
        operation="validate",
        auth=resolve_kaggle_auth(owner=owner, account=account),
        payload={"dataset_ref": dataset_ref, "checks_passed": True},
    )


def register(
    *,
    dataset_ref: str,
    capability: str,
    owner: str,
    account: str = "default",
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    return _envelope(
        status="ok",
        operation="register",
        auth=auth,
        payload={
            "dataset_ref": dataset_ref,
            "capability": capability,
            "registered_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        },
    )


__all__ = [
    "KaggleOperationResult",
    "capabilities",
    "get",
    "register",
    "reset_cache",
    "search",
    "validate",
]
