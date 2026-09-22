from __future__ import annotations

import re


_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"ya29\.[A-Za-z0-9_\-]{16,}"),
    re.compile(r"xox[abps]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"access_token[\"'=:\s]+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"refresh_token[\"'=:\s]+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"id_token[\"'=:\s]+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"client_secret[\"'=:\s]+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"Set-Cookie:\s*[^\r\n]+", re.IGNORECASE),
    re.compile(r"Authorization:\s*[^\r\n]+", re.IGNORECASE),
)

_REDACTION = "[REDACTED]"


def redact_text(text: str) -> str:
    if not text:
        return text
    for pattern in _PATTERNS:
        text = pattern.sub(_REDACTION, text)
    return text


def redact_payload(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_payload(v) for v in value]
    if isinstance(value, tuple):
        return tuple(redact_payload(v) for v in value)
    return value


__all__ = ["redact_payload", "redact_text"]
