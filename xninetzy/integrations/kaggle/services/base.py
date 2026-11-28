from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.auth_adapter import KaggleAuthContext, resolve_kaggle_auth
from xninetzy.integrations.kaggle.backend import KaggleBackendError, OpResult, Operation


@dataclass(frozen=True, slots=True)
class KaggleOperationResult:
    status: str
    operation: str
    payload: dict[str, Any] | None
    auth_used: str
    cache_hit: bool = False
    warnings: tuple[str, ...] = ()


def envelope(
    status: str,
    operation: str,
    auth: KaggleAuthContext,
    payload: dict[str, Any] | None = None,
    warnings: tuple[str, ...] = (),
) -> KaggleOperationResult:
    return KaggleOperationResult(
        status=status,
        operation=operation,
        payload=payload,
        auth_used=auth.source,
        warnings=warnings,
    )


def backend_failure(operation: str, auth: KaggleAuthContext, exc: KaggleBackendError) -> KaggleOperationResult:
    return envelope("error", operation, auth, {"error": exc.to_dict()})


def op_failure(operation: str, auth: KaggleAuthContext, result: OpResult) -> KaggleOperationResult:
    status = "not_accessible" if result.status_code in (403, 404) else "error"
    return envelope(status, operation, auth, {"error": result.error_dict()})


def run_operations(
    operation: str,
    owner: str,
    account: str,
    operations: Sequence[Operation],
    timeout: int | None = None,
) -> tuple[KaggleAuthContext, list[OpResult] | None, KaggleOperationResult | None]:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated:
        return auth, None, envelope("auth_required", operation, auth)
    try:
        results = backend_module.get_backend().run(operations, bearer_token=auth.bearer_token, timeout=timeout)
    except KaggleBackendError as exc:
        return auth, None, backend_failure(operation, auth, exc)
    return auth, results, None


__all__ = [
    "KaggleOperationResult",
    "backend_failure",
    "envelope",
    "op_failure",
    "run_operations",
]
