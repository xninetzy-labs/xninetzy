from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit


@dataclass(frozen=True)
class SiteDefinition:
    slug: str
    name: str
    base_url: str
    public_paths: tuple[str, ...]
    authenticated_paths: tuple[str, ...]
    login_path: str
    protection_flags: tuple[str, ...] = ()

    @property
    def hostname(self) -> str:
        return (urlsplit(self.base_url).hostname or "").lower()

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


def get_site(site_slug: str) -> SiteDefinition:
    normalized = site_slug.strip().lower()
    normalized = ALIASES.get(normalized, normalized)
    try:
        return SITES[normalized]
    except KeyError as exc:
        allowed = ", ".join(sorted(SITES))
        raise ValueError(f"Site tidak diizinkan: {site_slug!r}. Pilihan: {allowed}") from exc


def is_allowed_url(site: SiteDefinition, url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() == site.hostname
