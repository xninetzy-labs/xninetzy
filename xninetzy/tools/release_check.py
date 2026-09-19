from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import Any

from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.registry import get_all_tools


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "evidence": self.evidence,
        }


def check_tool_registry() -> CheckResult:
    tools = get_all_tools()
    bad_risk: list[str] = []
    missing_idem: list[tuple[str, str]] = []
    for tool in tools:
        manifest = manifest_for(tool.name)
        if manifest.risk.value not in {"read", "draft", "write", "final"}:
            bad_risk.append(tool.name)
        if manifest.risk.value in {"write", "final"} and not manifest.requires_idempotency:
            missing_idem.append((tool.name, manifest.risk.value))
    status = "PASS"
    detail = f"{len(tools)} tools classified"
    evidence = [f"tool_count={len(tools)}", f"bad_risk={len(bad_risk)}", f"missing_idempotency={len(missing_idem)}"]
    if bad_risk or missing_idem:
        status = "BLOCKED"
        detail = f"{len(bad_risk)} unknown risk, {len(missing_idem)} missing idempotency"
    return CheckResult(
        name="tool_registry",
        status=status,
        detail=detail,
        evidence=evidence,
    )


_SECRET_HINT_PATTERNS = (
    r"sk-[A-Za-z0-9]{16,}",
    r"sk-ant-[A-Za-z0-9_\-]{16,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{40,}",
    r"AIza[A-Za-z0-9_\-]{30,}",
    r"AKIA[0-9A-Z]{16}",
)


def check_secret_redaction_module() -> CheckResult:
    try:
        from xninetzy.os.security.guards import redact_secrets
    except ImportError as exc:
        return CheckResult(
            name="secret_redaction",
            status="BLOCKED",
            detail=f"redact_secrets unavailable: {exc}",
        )
    samples = [
        "sk-abcdefghijklmnop12345",
        "ghp_abc123def456ghi789jkl012mno345pqr678",
        "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    ]
    leaks = [s for s in samples if any(re.search(p, redact_secrets(s)) for p in _SECRET_HINT_PATTERNS)]
    status = "PASS" if not leaks else "BLOCKED"
    return CheckResult(
        name="secret_redaction",
        status=status,
        detail=f"{len(samples) - len(leaks)}/{len(samples)} sample secrets redacted",
        evidence=[f"sample={s[:10]}..." for s in samples] + [f"leak={s[:10]}..." for s in leaks],
    )


def check_safe_fetch_guard() -> CheckResult:
    try:
        from xninetzy.os.security.guards import safe_fetch
    except ImportError as exc:
        return CheckResult(
            name="safe_fetch",
            status="BLOCKED",
            detail=f"safe_fetch unavailable: {exc}",
        )
    import asyncio

    async def _probe() -> list[str]:
        failures: list[str] = []
        for url, expected_code in [
            ("file:///etc/passwd", "INVALID_SCHEME"),
            ("http://127.0.0.1:9/admin", "SSRF_BLOCKED"),
            ("http://localhost/admin", "SSRF_BLOCKED"),
        ]:
            try:
                await safe_fetch(url)
            except Exception as exc:
                actual = getattr(exc, "code", None) or exc.__class__.__name__
                if actual != expected_code:
                    failures.append(f"{url} -> {actual} (expected {expected_code})")
            else:
                failures.append(f"{url} -> no exception (expected {expected_code})")
        return failures

    failures = asyncio.run(_probe())
    status = "PASS" if not failures else "BLOCKED"
    return CheckResult(
        name="safe_fetch",
        status=status,
        detail=f"{3 - len(failures)}/3 SSRF guard scenarios blocked",
        evidence=failures or ["file:// blocked", "127.0.0.1 blocked", "localhost blocked"],
    )


def check_transport_config() -> CheckResult:
    from xninetzy.core.config import get_settings

    settings = get_settings()
    transport = (settings.XNINETZY_MCP_TRANSPORT or "stdio").strip().lower()
    host = (settings.XNINETZY_MCP_HTTP_HOST or "127.0.0.1").strip()
    issues: list[str] = []
    if transport not in {"stdio", "streamable-http"}:
        issues.append(f"transport invalid: {transport!r}")
    if transport == "streamable-http" and host and host not in {"127.0.0.1", "::1"}:
        issues.append(f"http host non-loopback: {host!r} (auth required)")
    status = "PASS" if not issues else "WARN"
    return CheckResult(
        name="transport_config",
        status=status,
        detail=f"transport={transport} host={host}",
        evidence=issues or ["loopback by default"],
    )


def check_sdk_pin() -> CheckResult:
    try:
        from importlib.metadata import version
        resolved = version("mcp")
    except Exception as exc:
        return CheckResult(
            name="sdk_pin",
            status="BLOCKED",
            detail=f"mcp metadata unavailable: {exc}",
        )
    try:
        major = int(resolved.split(".")[0])
    except (ValueError, IndexError):
        return CheckResult(
            name="sdk_pin",
            status="BLOCKED",
            detail=f"unparseable mcp version: {resolved!r}",
        )
    status = "PASS" if major == 1 else "WARN"
    return CheckResult(
        name="sdk_pin",
        status=status,
        detail=f"mcp resolved={resolved}",
        evidence=["Phase 2: stay on SDK v1.x"] if status == "PASS" else ["v2.x detected; Phase 2 should be revisited"],
    )


_CANONICAL_FINAL_TOOLS = (
    "hebat_upload_submission",
    "portal_krs_war_arm",
    "qa_fill_kuesioner",
)


def check_canonical_final_tools() -> CheckResult:
    tools = get_all_tools()
    actual = tuple(sorted(
        tool.name for tool in tools
        if manifest_for(tool.name).risk.value == "final"
    ))
    expected = tuple(sorted(_CANONICAL_FINAL_TOOLS))
    if actual == expected:
        return CheckResult(
            name="canonical_final_tools",
            status="PASS",
            detail=f"{len(actual)} FINAL tools match canonical set",
            evidence=[f"final={list(actual)}"],
        )
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    return CheckResult(
        name="canonical_final_tools",
        status="BLOCKED",
        detail=f"FINAL set drift: missing={missing}, extra={extra}",
        evidence=[f"expected={list(expected)}", f"actual={list(actual)}"],
    )


def run_release_checks() -> list[CheckResult]:
    return [
        check_tool_registry(),
        check_secret_redaction_module(),
        check_safe_fetch_guard(),
        check_transport_config(),
        check_sdk_pin(),
        check_canonical_final_tools(),
    ]
