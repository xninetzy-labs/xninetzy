from __future__ import annotations

from pydantic import BaseModel, SecretStr

from app.xninetzy.core.config import Settings, get_settings


class CampusCredentialError(RuntimeError):
    pass


class CampusCredentials(BaseModel):
    username: str
    password: SecretStr
    source: str


def resolve_campus_credentials(
    source: str = "hebat", settings: Settings | None = None
) -> CampusCredentials:
    normalized = source.strip().lower()
    if normalized != "hebat":
        raise CampusCredentialError(f"Credential source tidak didukung: {source}")
    current = settings or get_settings()
    username = current.HEBAT_USERNAME.strip()
    password = current.HEBAT_PASSWORD
    if not username or not password:
        raise CampusCredentialError(
            "HEBAT_USERNAME dan HEBAT_PASSWORD belum dikonfigurasi."
        )
    return CampusCredentials(
        username=username,
        password=SecretStr(password),
        source="hebat",
    )
