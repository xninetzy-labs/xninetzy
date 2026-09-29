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


def _coerce_ip(host: str):
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    if host.isdigit():
        value = int(host)
        if 0 <= value <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
            try:
                return ipaddress.ip_address(value)
            except ValueError:
                return None
    if host.startswith("0x"):
        try:
            value = int(host, 16)
        except ValueError:
            return None
        if 0 <= value <= 0xFFFFFFFF:
            return ipaddress.ip_address(value)
    return None


def is_private_address(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().strip("[]")
    if not host:
        return True
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        return True
    ip = _coerce_ip(host)
    if ip is None:
        return False
    if getattr(ip, "version", None) == 6 and getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


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
