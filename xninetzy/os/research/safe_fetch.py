from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain", "application/json", "application/xml", "text/xml")
MAX_REDIRECTS = 3
DEFAULT_MAX_BYTES = 2_000_000
DEFAULT_TIMEOUT = 20


class UnsafeUrlError(ValueError):
    pass


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _validate_host(host: str) -> None:
    if not host:
        raise UnsafeUrlError("URL tanpa host tidak diizinkan")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as error:
        raise UnsafeUrlError(f"DNS gagal untuk host: {error}") from error
    resolved = {info[4][0] for info in infos}
    if not resolved:
        raise UnsafeUrlError("Host tidak dapat diresolusi")
    for ip in resolved:
        if not _is_public_ip(ip):
            raise UnsafeUrlError("Host mengarah ke alamat internal/privat")


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"Skema {parsed.scheme or '∅'} tidak diizinkan")
    _validate_host(parsed.hostname or "")
    return url


def _content_type_allowed(content_type: str) -> bool:
    base = (content_type or "").split(";", 1)[0].strip().lower()
    return base in ALLOWED_CONTENT_TYPES


async def safe_get(
    url: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    import httpx

    current = _validate_url(url)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            response = await client.get(
                current,
                headers={"User-Agent": "Xninetzy-Research/1.0", "Accept": "text/html,text/plain"},
            )
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise UnsafeUrlError("Redirect tanpa lokasi")
                current = _validate_url(str(response.url.join(location)))
                continue
            response.raise_for_status()
            if not _content_type_allowed(response.headers.get("content-type", "")):
                raise UnsafeUrlError("Tipe konten tidak diizinkan")
            body = response.content[:max_bytes]
            return body.decode(response.encoding or "utf-8", errors="replace")
    raise UnsafeUrlError("Terlalu banyak redirect")
