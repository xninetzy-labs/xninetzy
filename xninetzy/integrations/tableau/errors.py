from __future__ import annotations


_TABLEAU_ERROR_CODES = frozenset({
    "TABLEAU_DEPENDENCY_MISSING",
    "INVALID_DATASET",
    "INVALID_SCHEMA",
    "HYPER_CREATION_FAILED",
    "HYPER_VALIDATION_FAILED",
    "DATASOURCE_DUPLICATE",
    "WORKBOOK_INVALID",
    "WORKSHEET_INVALID",
    "DASHBOARD_INVALID",
    "ARTIFACT_NOT_FOUND",
    "ARTIFACT_PATH_DENIED",
    "PUBLISH_AUTH_REQUIRED",
    "PUBLISH_PERMISSION_DENIED",
    "PUBLISH_FAILED",
    "PUBLISH_RATE_LIMITED",
    "PUBLISH_TIMEOUT",
    "REFRESH_FAILED",
    "POLICY_BLOCKED",
    "HITL_REQUIRED",
    "PROVIDER_ERROR",
    "VALIDATION_ERROR",
    "DS_SOURCE_ERROR",
    "VIZ_TYPE_ERROR",
    "WORKSHEET_CONFLICT",
    "TWB_DANGLING_DASHBOARD_REF",
    "TWB_WINDOWS_PATH",
})


class TableauIntegrationError(Exception):
    def __init__(self, message: str = "", code: str = "VALIDATION_ERROR") -> None:
        normalized = str(code).upper().strip()
        final_code = normalized if normalized in _TABLEAU_ERROR_CODES else "VALIDATION_ERROR"
        if message:
            cleaned = str(message)
            if ":" in cleaned:
                head, rest = cleaned.split(":", 1)
                prefix = head.strip().upper()
                if prefix in _TABLEAU_ERROR_CODES and prefix != "VALIDATION_ERROR":
                    final_code = prefix
                    cleaned = rest.lstrip()
            message = cleaned
        super().__init__(message)
        self.code = final_code

    def to_dict(self) -> dict[str, str]:
        return {"error": self.code, "message": str(self)}


def tableau_error_response(exc: BaseException) -> dict[str, str]:
    if isinstance(exc, TableauIntegrationError):
        return exc.to_dict()
    return {"error": "PROVIDER_ERROR", "message": str(exc)}


__all__ = ["TableauIntegrationError", "tableau_error_response", "TABLEAU_ERROR_CODES"]


_TABLEAU_ERROR_CODES_LOCAL = _TABLEAU_ERROR_CODES
__all__ += ["_TABLEAU_ERROR_CODES_LOCAL"]
