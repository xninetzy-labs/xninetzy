from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from xninetzy.db.sqlite import connect, init_db


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_table() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_secret_store (
                credential_ref TEXT PRIMARY KEY,
                ciphertext BLOB NOT NULL,
                key_version INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                revoked_at TEXT
            )
            """
        )


def _derive_master_key(env_var: str = "XNINETZY_AUTH_MASTER_KEY", fallback_seed: str = "xninetzy-local-owner") -> bytes:
    raw = os.environ.get(env_var, "").strip()
    if raw:
        return hashlib.sha256(raw.encode("utf-8")).digest()
    seed_path = Path.home() / ".local" / "share" / "xninetzy" / "auth-master.key"
    if seed_path.is_file():
        return hashlib.sha256(seed_path.read_bytes()).digest()
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_bytes(os.urandom(32))
    try:
        os.chmod(seed_path, 0o600)
    except OSError:
        pass
    return hashlib.sha256(seed_path.read_bytes()).digest()


def _fernet(key: bytes) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(key))


@dataclass(frozen=True, slots=True)
class CredentialMetadata:
    credential_ref: str
    provider: str
    account: str
    key_version: int
    created_at: str
    updated_at: str
    expires_at: str | None
    revoked_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "credential_ref": self.credential_ref,
            "provider": self.provider,
            "account": self.account,
            "key_version": self.key_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
        }


def _row_to_metadata(row: Any) -> CredentialMetadata:
    metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
    return CredentialMetadata(
        credential_ref=row["credential_ref"],
        provider=metadata.get("provider", ""),
        account=metadata.get("account", ""),
        key_version=int(row["key_version"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
    )


class SecretStore:
    """Fernet-encrypted credential storage.

    Values are never returned to callers in plain text. Operations return
    opaque ``credential_ref`` identifiers; the raw bytes are stored under
    ``auth_secret_store`` and decrypted only by the trusted adapter that
    needs them (e.g. an HTTP client wrapper).
    """

    KEY_VERSION = 1

    def __init__(self, master_key: bytes | None = None) -> None:
        self._key = master_key if master_key is not None else _derive_master_key()
        self._fernet = _fernet(self._key)

    @staticmethod
    def generate_credential_ref(provider: str, account: str) -> str:
        digest = hashlib.sha256(
            f"{provider}:{account}:{os.urandom(8).hex()}".encode("utf-8")
        ).hexdigest()[:24]
        return f"cred-{provider}-{digest}"

    def set(
        self,
        credential_ref: str,
        value: bytes | str,
        *,
        provider: str,
        account: str,
        expires_at: str | None = None,
    ) -> CredentialMetadata:
        _ensure_table()
        plaintext = value.encode("utf-8") if isinstance(value, str) else value
        ciphertext = self._fernet.encrypt(plaintext)
        now = _utcnow()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_secret_store
                    (credential_ref, ciphertext, key_version, metadata_json,
                     created_at, updated_at, expires_at, revoked_at)
                VALUES (?,?,?,?,?,?,?,NULL)
                ON CONFLICT(credential_ref) DO UPDATE SET
                    ciphertext=excluded.ciphertext,
                    key_version=excluded.key_version,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at,
                    expires_at=excluded.expires_at
                """,
                (
                    credential_ref,
                    ciphertext,
                    self.KEY_VERSION,
                    json.dumps({"provider": provider, "account": account}, sort_keys=True),
                    now,
                    now,
                    expires_at,
                ),
            )
            row = conn.execute(
                "SELECT * FROM auth_secret_store WHERE credential_ref=?",
                (credential_ref,),
            ).fetchone()
        assert row is not None
        return _row_to_metadata(row)

    def get_metadata(self, credential_ref: str) -> CredentialMetadata | None:
        _ensure_table()
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM auth_secret_store WHERE credential_ref=?",
                (credential_ref,),
            ).fetchone()
        return _row_to_metadata(row) if row else None

    def get_bytes(self, credential_ref: str) -> bytes | None:
        _ensure_table()
        with connect() as conn:
            row = conn.execute(
                "SELECT ciphertext, revoked_at FROM auth_secret_store WHERE credential_ref=?",
                (credential_ref,),
            ).fetchone()
        if row is None or row["revoked_at"] is not None:
            return None
        try:
            return self._fernet.decrypt(bytes(row["ciphertext"]))
        except InvalidToken:
            return None

    def exists(self, credential_ref: str) -> bool:
        return self.get_metadata(credential_ref) is not None

    def revoke(self, credential_ref: str) -> bool:
        _ensure_table()
        with connect() as conn:
            cur = conn.execute(
                "UPDATE auth_secret_store SET revoked_at=?, updated_at=? "
                "WHERE credential_ref=? AND revoked_at IS NULL",
                (_utcnow(), _utcnow(), credential_ref),
            )
            return cur.rowcount > 0

    def delete(self, credential_ref: str) -> bool:
        _ensure_table()
        with connect() as conn:
            cur = conn.execute(
                "DELETE FROM auth_secret_store WHERE credential_ref=?",
                (credential_ref,),
            )
            return cur.rowcount > 0


_DEFAULT_STORE: SecretStore | None = None


def default_secret_store() -> SecretStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = SecretStore()
    return _DEFAULT_STORE


def hmac_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


__all__ = [
    "CredentialMetadata",
    "SecretStore",
    "default_secret_store",
    "hmac_compare",
]
