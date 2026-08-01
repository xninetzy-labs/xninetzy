from __future__ import annotations

import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

from app.xninetzy.os.web_analysis.security import has_sensitive_query


@dataclass(frozen=True)
class SiteDefinition:
    slug: str
    name: str
    base_url: str
    public_paths: tuple[str, ...]
    authenticated_paths: tuple[str, ...]
    login_path: str
    protection_flags: tuple[str, ...] = ()
    dynamic: bool = False

    @property
    def hostname(self) -> str:
        return (urlsplit(self.base_url).hostname or "").lower()

    @property
    def port(self) -> int:
        parsed = urlsplit(self.base_url)
        return parsed.port or 443

    def absolute_url(self, path: str) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))


SITES: dict[str, SiteDefinition] = {
    "hebat": SiteDefinition(
        slug="hebat",
        name="HEBAT (Moodle UNAIR)",
        base_url="https://hebat.elearning.unair.ac.id",
        public_paths=("/hebat-v2/",),
        authenticated_paths=("/my/courses.php", "/grade/report/overview/index.php"),
        login_path="/login/index.php",
    ),
    "mahasiswa": SiteDefinition(
        slug="mahasiswa",
        name="Cybercampus Mahasiswa UNAIR",
        base_url="https://mahasiswa.unair.ac.id",
        public_paths=("/",),
        authenticated_paths=("/",),
        login_path="/",
        protection_flags=(
            "Submit KRS adalah aksi kompetitif dan dilindungi human verification. "
            "Sistem hanya boleh membaca status slot dan mengirim notifikasi; klik/submit tetap manual.",
        ),
    ),
}

ALIASES = {
    "hebat.elearning.unair.ac.id": "hebat",
    "mahasiswa.unair.ac.id": "mahasiswa",
    "portal": "mahasiswa",
    "cybercampus": "mahasiswa",
}


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _validate_public_host(hostname: str) -> None:
    normalized = hostname.casefold().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain"}:
        raise ValueError("Host internal tidak diizinkan.")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(normalized, None)}
    except socket.gaierror as exc:
        raise ValueError("Host publik tidak dapat diresolusi.") from exc
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise ValueError("URL harus menunjuk host publik.")


def _canonical_seed_url(url: str) -> tuple[str, str, int]:
    parsed = urlsplit(url.strip())
    if parsed.scheme.casefold() != "https" or not parsed.hostname:
        raise ValueError("URL sumber harus memakai HTTPS dan memiliki host.")
    if parsed.username or parsed.password:
        raise ValueError("URL dengan credential inline tidak diizinkan.")
    port = parsed.port or 443
    if port != 443:
        raise ValueError("Port non-HTTPS tidak diizinkan.")
    if has_sensitive_query(url):
        raise ValueError("Query credential atau token tidak diizinkan.")
    _validate_public_host(parsed.hostname)
    path = parsed.path or "/"
    canonical = urlunsplit(
        ("https", parsed.hostname.casefold(), path, parsed.query, "")
    )
    return canonical, parsed.hostname.casefold(), port


def site_from_url(url: str) -> SiteDefinition:
    canonical, hostname, port = _canonical_seed_url(url)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    path = urlsplit(canonical).path or "/"
    return SiteDefinition(
        slug=f"public-{digest}",
        name=f"Public web: {hostname}",
        base_url=f"https://{hostname}",
        public_paths=(path,),
        authenticated_paths=(),
        login_path=path,
        protection_flags=(
            "Public discovery bersifat GET/HEAD-only dan berhenti saat human verification terdeteksi.",
            "Aksi mutasi, credential, token, dan query sensitif tidak pernah dijalankan atau disimpan.",
        ),
        dynamic=True,
    )


def get_site(site_slug: str) -> SiteDefinition:
    normalized = site_slug.strip().lower()
    normalized = ALIASES.get(normalized, normalized)
    if normalized in SITES:
        return SITES[normalized]
    if normalized.startswith(("https://", "http://")):
        return site_from_url(site_slug)
    allowed = ", ".join(sorted(SITES))
    raise ValueError(
        f"Site tidak diizinkan: {site_slug!r}. Gunakan preset ({allowed}) "
        "atau URL HTTPS publik."
    )


def is_allowed_url(site: SiteDefinition, url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme.casefold() != "https" or (parsed.hostname or "").casefold() != site.hostname:
        return False
    try:
        return (parsed.port or 443) == site.port
    except ValueError:
        return False
