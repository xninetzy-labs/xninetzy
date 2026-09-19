from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


MAX_FETCH_BYTES = 5 * 1024 * 1024
_FETCH_TIMEOUT_SECONDS = 10.0

_SECRET_PATTERNS: tuple[str, ...] = (
    r"sk-[A-Za-z0-9]{16,}",
    r"sk-ant-[A-Za-z0-9_\-]{16,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{40,}",
    r"xox[abps]-[A-Za-z0-9-]{10,}",
    r"AIza[A-Za-z0-9_\-]{30,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)
_REDACTION = "[REDACTED]"


class SecurityError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class _PrivateNetworks:
    networks: tuple = (
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("100.64.0.0/10"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.0.0.0/24"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("198.18.0.0/15"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    )


_PRIVATE_NETWORKS = _PrivateNetworks().networks


def _host_is_private(host: str) -> bool:
    if not host:
        return True
    lowered = host.lower().strip()
    if lowered == "localhost":
        return True
    try:
        addr = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return any(addr in net for net in _PRIVATE_NETWORKS)


def redact_secrets(text: str) -> str:
    if not text:
        return text
    out = text
    for pattern in _SECRET_PATTERNS:
        out = re.sub(pattern, _REDACTION, out)
    return out


async def safe_fetch(
    url: str,
    *,
    allow_private: bool = False,
    max_bytes: int = MAX_FETCH_BYTES,
    timeout_seconds: float = _FETCH_TIMEOUT_SECONDS,
) -> bytes:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SecurityError("INVALID_SCHEME", f"scheme must be http(s): {parsed.scheme}")
    host = parsed.hostname or ""
    if not allow_private and _host_is_private(host):
        raise SecurityError("SSRF_BLOCKED", f"host private/loopback: {host}")
    async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=False) as client:
        response = await client.get(url, follow_redirects=False)
    if len(response.content) > max_bytes:
        raise SecurityError("RESPONSE_TOO_LARGE", f"body > {max_bytes} bytes")
    if response.status_code >= 400:
        raise SecurityError(
            "HTTP_ERROR",
            f"status {response.status_code} for {parsed.hostname}",
        )
    return response.content
