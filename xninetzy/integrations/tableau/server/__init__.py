from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    ArtifactRecord,
    PublishResult,
    PublishTarget,
    _stable_hash,
)


_REDACT_KEYS = frozenset({"token_secret", "password", "credentials", "personal_access_token_secret"})


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k in _REDACT_KEYS:
            out[k] = "***REDACTED***"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out


def _import_tsc() -> tuple[Any, Any, Any]:
    try:
        import tableauserverclient as TSC  # type: ignore[import-not-found]
    except ImportError as exc:
        raise TableauIntegrationError(
            "TABLEAU_DEPENDENCY_MISSING: tableauserverclient not installed",
            code="TABLEAU_DEPENDENCY_MISSING",
        ) from exc
    return TSC, TSC.Server, TSC.PersonalAccessTokenAuth


def tsc_available() -> bool:
    try:
        import tableauserverclient  # type: ignore[import-not-found]  # noqa: F401
        return True
    except ImportError:
        return False


def _retry(
    fn: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    on_codes: tuple[str, ...] = ("PUBLISH_RATE_LIMITED", "PUBLISH_TIMEOUT"),
) -> Any:
    last_exc: BaseException | None = None
    for idx in range(attempts):
        try:
            return fn()
        except TableauIntegrationError as exc:
            last_exc = exc
            if exc.code not in on_codes:
                raise
            if idx + 1 >= attempts:
                raise
            time.sleep(base_delay * (2 ** idx))
    if last_exc is not None:
        raise last_exc
    return None


def _require_creds(target: PublishTarget) -> None:
    if not target.token_name or not target.token_secret:
        raise TableauIntegrationError(
            "PUBLISH_AUTH_REQUIRED: token_name and token_secret required",
            code="PUBLISH_AUTH_REQUIRED",
        )


def _require_tsc() -> tuple[Any, Any, Any]:
    if not tsc_available():
        raise TableauIntegrationError(
            "TABLEAU_DEPENDENCY_MISSING: tableauserverclient not installed",
            code="TABLEAU_DEPENDENCY_MISSING",
        )
    return _import_tsc()


def _classify_publish_error(message: str) -> str:
    lower = message.lower()
    if "permission" in lower or "403" in lower:
        return "PUBLISH_PERMISSION_DENIED"
    if "401" in lower or "auth" in lower:
        return "PUBLISH_AUTH_REQUIRED"
    if "rate" in lower or "429" in lower:
        return "PUBLISH_RATE_LIMITED"
    if "timeout" in lower or "timed out" in lower:
        return "PUBLISH_TIMEOUT"
    return "PUBLISH_FAILED"


def _resolve_project(
    server: Any,
    TSC: Any,
    target: PublishTarget,
    project_id: str,
) -> Any:
    try:
        if project_id:
            return server.projects.get_by_id(project_id)
        all_projects = list(TSC.Pager(server.projects.get()))
        matched = next((p for p in all_projects if p.name == target.project), None)
        if matched is not None:
            return matched
        created = TSC.ProjectItem(name=target.project)
        server.projects.create(created)
        return created
    except Exception as exc:
        raise TableauIntegrationError(
            f"PUBLISH_PERMISSION_DENIED: {exc}",
            code="PUBLISH_PERMISSION_DENIED",
        ) from exc


def publish_workbook(
    workbook_path: str | Path,
    target: PublishTarget,
    *,
    project_id: str = "",
    mode: str = "Append",
    attempts: int = 3,
) -> PublishResult:
    p = Path(workbook_path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"ARTIFACT_NOT_FOUND: workbook not found at {p}",
            code="ARTIFACT_NOT_FOUND",
        )
    _require_creds(target)
    TSC, ServerCls, AuthCls = _require_tsc()

    auth_ctx: dict[str, Any] = {"auth": None, "server": None}

    def _sign_in() -> tuple[Any, Any]:
        try:
            auth = AuthCls(target.token_name, target.token_secret, target.site_id or "")
            server = ServerCls(target.server_url, use_server_version=False)
            server.auth.sign_in(auth)
            auth_ctx["auth"] = auth
            auth_ctx["server"] = server
            return auth, server
        except Exception as exc:
            raise TableauIntegrationError(
                f"PUBLISH_AUTH_REQUIRED: {exc}",
                code="PUBLISH_AUTH_REQUIRED",
            ) from exc

    def _sign_out() -> None:
        server = auth_ctx.get("server")
        if server is not None:
            try:
                server.auth.sign_out()
            except Exception:
                pass

    def _do_publish() -> PublishResult:
        _auth, server = _sign_in()
        project = _resolve_project(server, TSC, target, project_id)
        try:
            wb_item = TSC.WorkbookItem(name=p.stem, project_id=project.id if project else "")
            publish_mode = getattr(TSC.WorkbookPublishRequest, "Mode", None)
            mode_value = getattr(publish_mode, mode, None) if publish_mode else None
            if mode_value is None:
                mode_value = mode
            publish_request = TSC.WorkbookPublishRequest(
                wb_item, str(p), mode=mode_value, skip_connection_check=True
            )
            server.workbooks.publish(publish_request)
            workbook_id = getattr(wb_item, "id", "") or ""
            workbook_url = (
                f"{target.server_url.rstrip('/')}/workbooks/{workbook_id}"
                if workbook_id
                else ""
            )
            return PublishResult(
                workbook_id=workbook_id,
                workbook_url=workbook_url,
                status="pending",
            )
        except TableauIntegrationError:
            raise
        except Exception as exc:
            code = _classify_publish_error(str(exc))
            raise TableauIntegrationError(
                f"{code}: {exc}", code=code
            ) from exc

    try:
        return _retry(_do_publish, attempts=attempts)
    finally:
        _sign_out()


def list_workbooks(
    target: PublishTarget,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    _require_creds(target)
    TSC, ServerCls, AuthCls = _require_tsc()

    try:
        auth = AuthCls(target.token_name, target.token_secret, target.site_id or "")
        server = ServerCls(target.server_url, use_server_version=False)
        server.auth.sign_in(auth)
    except Exception as exc:
        raise TableauIntegrationError(
            f"PUBLISH_AUTH_REQUIRED: {exc}",
            code="PUBLISH_AUTH_REQUIRED",
        ) from exc

    try:
        items: list[dict[str, Any]] = []
        for wb in TSC.Pager(server.workbooks.list(), limit=limit):
            items.append(
                {
                    "id": wb.id,
                    "name": wb.name,
                    "project_id": wb.project_id,
                    "size": getattr(wb, "size", 0),
                    "created_at": getattr(wb, "created_at", ""),
                    "updated_at": getattr(wb, "updated_at", ""),
                }
            )
        return {
            "target": _redact(target.safe_dict()),
            "count": len(items),
            "items": items,
        }
    except TableauIntegrationError:
        raise
    except Exception as exc:
        code = _classify_publish_error(str(exc))
        raise TableauIntegrationError(f"{code}: {exc}", code=code) from exc
    finally:
        try:
            server.auth.sign_out()
        except Exception:
            pass


def refresh_workbook(
    workbook_id: str,
    target: PublishTarget,
    *,
    attempts: int = 3,
) -> PublishResult:
    if not workbook_id:
        raise TableauIntegrationError(
            "PROVIDER_ERROR: workbook_id required",
            code="PROVIDER_ERROR",
        )
    _require_creds(target)
    _require_tsc()

    def _do_refresh() -> PublishResult:
        try:
            TSC, ServerCls, AuthCls = _import_tsc()
            auth = AuthCls(target.token_name, target.token_secret, target.site_id or "")
            server = ServerCls(target.server_url, use_server_version=False)
            server.auth.sign_in(auth)
            wb_item = server.workbooks.get_by_id(workbook_id)
            server.workbooks.refresh(wb_item)
            server.auth.sign_out()
            return PublishResult(
                workbook_id=workbook_id,
                workbook_url=f"{target.server_url.rstrip('/')}/workbooks/{workbook_id}",
                status="refreshing",
            )
        except TableauIntegrationError:
            raise
        except Exception as exc:
            code = _classify_publish_error(str(exc))
            if code == "PUBLISH_FAILED":
                code = "REFRESH_FAILED"
            raise TableauIntegrationError(f"{code}: {exc}", code=code) from exc

    return _retry(_do_refresh, attempts=attempts)


def artifact_record(
    artifact_id: str,
    path: str,
    kind: str,
    *,
    schema_hash: str = "",
    workbook_id: str = "",
    validation: str = "",
    state: str = "GENERATING",
) -> ArtifactRecord:
    resolved_id = artifact_id or _stable_hash(("artifact", path, kind))
    return ArtifactRecord(
        artifact_id=resolved_id,
        path=path,
        kind=kind,
        schema_hash=schema_hash,
        workbook_id=workbook_id,
        validation=validation,
        state=state,
    )


__all__ = [
    "publish_workbook",
    "list_workbooks",
    "refresh_workbook",
    "tsc_available",
    "artifact_record",
]
