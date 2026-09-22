from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


_BLOCKED_SCHEMES: frozenset[str] = frozenset(
    {"javascript", "data", "file", "chrome", "about", "vbscript"}
)


class URLBlockedError(ValueError):
    pass


def is_blocked_scheme(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme.lower() in _BLOCKED_SCHEMES


def is_private_address(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return True
    if host in {"localhost", "localhost.localdomain"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def is_allowed_origin(url: str, allowed_origins: tuple[str, ...]) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    for origin in allowed_origins:
        o = origin.lower().lstrip(".")
        if host == o or host.endswith("." + o):
            return True
    return False


def assert_safe_url(url: str, allowed_origins: tuple[str, ...] = ()) -> None:
    if not url:
        raise URLBlockedError("empty url")
    if is_blocked_scheme(url):
        raise URLBlockedError(f"scheme blocked: {url}")
    if is_private_address(url):
        raise URLBlockedError(f"private/loopback address blocked: {url}")
    if allowed_origins and not is_allowed_origin(url, allowed_origins):
        raise URLBlockedError(f"origin not in allowlist: {url}")


__all__ = [
    "URLBlockedError",
    "assert_safe_url",
    "is_allowed_origin",
    "is_blocked_scheme",
    "is_private_address",
]
