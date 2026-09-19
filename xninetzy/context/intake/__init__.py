from __future__ import annotations

from xninetzy.context.intake.classify import (
    ClassificationEvidence,
    ClassificationResult,
    RepoKind,
    classify_layout,
    detect_docker_indicator,
    detect_mcp_server,
    detect_npm_package,
    detect_python_package,
    detect_rest_api,
)
from xninetzy.context.intake.layout import (
    LAYOUT_FILE_CAPABILITIES,
    LAYOUT_FILE_MANIFEST_DOCKER,
    LAYOUT_FILE_MANIFEST_NPM,
    LAYOUT_FILE_MANIFEST_PYTHON,
    LAYOUT_FILE_README,
    RepoLayout,
    collect_layout,
)
from xninetzy.context.intake.register import (
    IntakeRegistrationResult,
    promote_provider_tier,
    register_from_classification,
)
from xninetzy.context.intake.urls import (
    URLKind,
    canonicalize_github_url,
    detect_url_kind,
    parse_github_url,
    parse_local_path,
    sha256_hex,
)

PACKAGE_MARKER: str = "xninetzy.context.intake"

__all__ = [
    "ClassificationEvidence",
    "ClassificationResult",
    "IntakeRegistrationResult",
    "LAYOUT_FILE_CAPABILITIES",
    "LAYOUT_FILE_MANIFEST_DOCKER",
    "LAYOUT_FILE_MANIFEST_NPM",
    "LAYOUT_FILE_MANIFEST_PYTHON",
    "LAYOUT_FILE_README",
    "PACKAGE_MARKER",
    "RepoKind",
    "RepoLayout",
    "URLKind",
    "canonicalize_github_url",
    "classify_layout",
    "collect_layout",
    "detect_docker_indicator",
    "detect_mcp_server",
    "detect_npm_package",
    "detect_python_package",
    "detect_rest_api",
    "detect_url_kind",
    "parse_github_url",
    "parse_local_path",
    "promote_provider_tier",
    "register_from_classification",
    "sha256_hex",
]
