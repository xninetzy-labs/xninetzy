from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AuthStatus = Literal[
    "public",
    "authenticated",
    "auth_required",
    "human_verification_required",
    "configuration_required",
    "error",
]


class EndpointRecord(BaseModel):
    """Sanitized GET/HEAD endpoint metadata; query values are never persisted."""

    method: Literal["GET", "HEAD"]
    path: str
    query_keys: list[str] = Field(default_factory=list)
    status: int | None = None
    content_type: str | None = None


class ModuleRecord(BaseModel):
    name: str
    path: str
    classification: Literal[
        "read_only",
        "monitor_only",
        "contains_action",
        "confirmation_required",
    ] = "read_only"
    selectors: list[str] = Field(default_factory=list)
    field_names: list[str] = Field(default_factory=list)
    structure_hash: str
    analyzed_at: str


class SiteAnalysis(BaseModel):
    schema_version: int = 1
    site_slug: str
    site_name: str
    base_url: str
    analyzed_at: str
    auth_status: AuthStatus
    modules: list[ModuleRecord] = Field(default_factory=list)
    endpoints: list[EndpointRecord] = Field(default_factory=list)
    protection_flags: list[str] = Field(default_factory=list)
    login_notes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    status: Literal[
        "completed",
        "cache_fresh",
        "human_verification_required",
        "configuration_required",
        "busy",
        "failed",
    ]
    site_slug: str
    analysis_path: str | None = None
    pages_analyzed: int = 0
    auth_status: AuthStatus = "public"
    message: str
