from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from xninetzy.os.security.guards import redact_secrets

SEVERITY_ORDER: dict[str, int] = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
_SEVERITY_ALIASES: dict[str, str] = {
    "error": "high",
    "warning": "medium",
    "warn": "medium",
    "moderate": "medium",
    "negligible": "low",
    "minor": "low",
    "informational": "info",
    "unknown": "medium",
    "": "medium",
}
EVIDENCE_LIMIT = 300


def normalize_severity(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in SEVERITY_ORDER:
        return text
    return _SEVERITY_ALIASES.get(text, "medium")


def fingerprint_for(tool: str, rule: str, asset: str, location: str, line: int) -> str:
    raw = f"{tool}|{rule}|{asset}|{location}|{line}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def hash_prefix(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:8]


@dataclass(slots=True)
class ScanHit:
    tool: str
    rule: str
    severity: str
    asset: str
    location: str
    line: int
    fingerprint: str
    evidence: str
    category: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_correlate_input(self) -> dict[str, Any]:
        where = f"{self.location}:{self.line}" if self.line else self.location
        return {
            "scanner": self.tool,
            "asset": self.asset,
            "location": where,
            "category": self.category,
            "severity": self.severity,
            "title": self.rule,
            "confidence": 0.7,
            "evidence": self.evidence,
        }


def make_hit(
    *,
    tool: str,
    rule: str,
    severity: Any,
    asset: str,
    location: str = "",
    line: int = 0,
    evidence: str = "",
    category: str = "",
    extra: dict[str, Any] | None = None,
) -> ScanHit:
    clean_rule = str(rule or "unknown")
    clean_asset = str(asset or location or "unknown")
    clean_location = str(location or asset or "")
    safe_evidence = redact_secrets(str(evidence or ""))[:EVIDENCE_LIMIT]
    return ScanHit(
        tool=tool,
        rule=clean_rule,
        severity=normalize_severity(severity),
        asset=clean_asset,
        location=clean_location,
        line=int(line or 0),
        fingerprint=fingerprint_for(tool, clean_rule, clean_asset, clean_location, int(line or 0)),
        evidence=safe_evidence,
        category=category or clean_rule,
        extra=dict(extra or {}),
    )


def canonical_advisory(ids: list[str]) -> str:
    cleaned = [str(i).strip() for i in ids if str(i).strip()]
    cves = sorted(i for i in cleaned if i.upper().startswith("CVE-"))
    if cves:
        return cves[0].upper()
    return cleaned[0] if cleaned else "unknown-advisory"


_SENSITIVE_KEYS = frozenset({"Code", "Secret", "Match", "lines", "Lines", "StringMatched", "snippet"})


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items() if k not in _SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, str):
        return redact_secrets(value)
    return value


def sanitize_raw_output(text: str) -> str:
    if not text or not text.strip():
        return text
    try:
        parsed = json.loads(text)
    except ValueError:
        return redact_secrets(text)
    return json.dumps(_scrub(parsed), ensure_ascii=False)
