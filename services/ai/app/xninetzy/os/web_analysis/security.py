from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlsplit

from app.xninetzy.os.web_analysis.models import EndpointRecord


SAFE_METHODS = frozenset({"GET", "HEAD"})
_HUMAN_VERIFICATION_PATTERNS = (
    "captcha",
    "g-recaptcha",
    "h-captcha",
    "hcaptcha",
    "cf-turnstile",
    "human verification",
    "verifikasi manusia",
    "saya bukan robot",
)
_SENSITIVE_QUERY_KEY = re.compile(
    r"(?:token|key|secret|password|passwd|session|sesskey|auth|code|signature|credential)",
    re.IGNORECASE,
)


def is_safe_request_method(method: str) -> bool:
    return method.upper() in SAFE_METHODS


def detect_human_verification(html: str, url: str = "") -> bool:
    haystack = f"{url}\n{html}".lower()
    return any(pattern in haystack for pattern in _HUMAN_VERIFICATION_PATTERNS)


def looks_like_login(html: str, url: str = "") -> bool:
    lowered = html.lower()
    return (
        "/login" in url.lower()
        or ("type=\"password\"" in lowered or "type='password'" in lowered)
        or "name=\"password\"" in lowered
        or "name='password'" in lowered
    )


def has_sensitive_query(url: str) -> bool:
    return any(
        _SENSITIVE_QUERY_KEY.search(key)
        for key, _value in parse_qsl(urlsplit(url).query, keep_blank_values=True)
    )


def sanitize_endpoint(method: str, url: str, status: int | None, content_type: str | None) -> EndpointRecord | None:
    normalized_method = method.upper()
    if normalized_method not in SAFE_METHODS:
        return None
    parsed = urlsplit(url)
    query_keys = sorted(
        {
            key
            for key, _value in parse_qsl(parsed.query, keep_blank_values=True)
            if key and not _SENSITIVE_QUERY_KEY.search(key)
        }
    )
    return EndpointRecord(
        method=normalized_method,
        path=parsed.path or "/",
        query_keys=query_keys,
        status=status,
        content_type=(content_type or "").split(";", 1)[0] or None,
    )
