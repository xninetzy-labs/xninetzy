from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.sites import get_site


class SessionEncryptionUnavailable(RuntimeError):
    pass


class SessionDecryptionError(RuntimeError):
    pass


class EncryptedProfileStore:
    """Encrypted JSON store for the single local owner profile."""

    def __init__(self, namespace: str, root: str | Path | None = None, key: str | None = None) -> None:
        settings = get_settings()
        self.root = Path(root or settings.WEB_ANALYSIS_DATA_DIR) / namespace
        self._key_text = key if key is not None else settings.WEB_ANALYSIS_ENCRYPTION_KEY
        self._fernet, self._hmac_key = self._build_crypto(self._key_text)

    @staticmethod
    def _build_crypto(key_text: str) -> tuple[Fernet, bytes]:
        if not key_text:
            raise SessionEncryptionUnavailable(
                "WEB_ANALYSIS_ENCRYPTION_KEY belum diisi; penyimpanan session ditolak (fail closed)."
            )
        try:
            raw = base64.urlsafe_b64decode(key_text.encode("ascii"))
            if len(raw) != 32:
                raise ValueError("invalid key length")
            return Fernet(key_text.encode("ascii")), raw
        except Exception as exc:
            raise SessionEncryptionUnavailable(
                "WEB_ANALYSIS_ENCRYPTION_KEY bukan Fernet key yang valid."
            ) from exc

    def _path(self, profile_id: str | None, site_slug: str, kind: str) -> Path:
        profile = profile_id or get_settings().WEB_ANALYSIS_PROFILE_ID
        if not profile:
            raise ValueError("WEB_ANALYSIS_PROFILE_ID wajib diisi")
        site = get_site(site_slug)
        digest = hmac.new(self._hmac_key, profile.encode("utf-8"), hashlib.sha256).hexdigest()
        safe_kind = "".join(char for char in kind if char.isalnum() or char in "-_")
        if not safe_kind:
            raise ValueError("kind tidak valid")
        return self.root / site.slug / f"{digest}.{safe_kind}.enc"

    def save(self, profile_id: str | None, site_slug: str, kind: str, payload: dict[str, Any]) -> Path:
        serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        max_bytes = get_settings().WEB_ANALYSIS_MAX_ENCRYPTED_JSON_BYTES
        if len(serialized) > max_bytes:
            raise ValueError(f"Payload terlalu besar ({len(serialized)} > {max_bytes} bytes)")
        path = self._path(profile_id, site_slug, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(self._fernet.encrypt(serialized))
        os.chmod(temp, 0o600)
        temp.replace(path)
        return path

    def load(self, profile_id: str | None, site_slug: str, kind: str) -> dict[str, Any] | None:
        path = self._path(profile_id, site_slug, kind)
        if not path.exists():
            return None
        try:
            decrypted = self._fernet.decrypt(path.read_bytes())
            value = json.loads(decrypted)
        except (InvalidToken, json.JSONDecodeError) as exc:
            raise SessionDecryptionError("Session tidak dapat didekripsi; key salah atau file rusak.") from exc
        if not isinstance(value, dict):
            raise SessionDecryptionError("Encrypted JSON root harus object.")
        return value

    def exists(self, profile_id: str | None, site_slug: str, kind: str) -> bool:
        return self._path(profile_id, site_slug, kind).exists()

    def delete(self, profile_id: str | None, site_slug: str, kind: str) -> bool:
        path = self._path(profile_id, site_slug, kind)
        existed = path.exists()
        path.unlink(missing_ok=True)
        return existed


class SessionManager:
    def __init__(self, root: str | Path | None = None, key: str | None = None) -> None:
        self.store = EncryptedProfileStore("sessions", root=root, key=key)

    def save_storage_state(
        self,
        site_slug: str,
        storage_state: dict[str, Any],
        profile_id: str | None = None,
    ) -> Path:
        if not isinstance(storage_state.get("cookies", []), list):
            raise ValueError("storage_state.cookies harus list")
        if not isinstance(storage_state.get("origins", []), list):
            raise ValueError("storage_state.origins harus list")
        envelope = {
            "schema_version": 1,
            "site_slug": get_site(site_slug).slug,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "storage_state": storage_state,
        }
        return self.store.save(profile_id, site_slug, "storage-state", envelope)

    def load_storage_state(
        self,
        site_slug: str,
        profile_id: str | None = None,
    ) -> dict[str, Any] | None:
        envelope = self.store.load(profile_id, site_slug, "storage-state")
        if not envelope:
            return None
        storage_state = envelope.get("storage_state")
        if not isinstance(storage_state, dict):
            raise SessionDecryptionError("Envelope session tidak valid.")
        return storage_state

    def has_session(self, site_slug: str, profile_id: str | None = None) -> bool:
        return self.store.exists(profile_id, site_slug, "storage-state")

    def clear_session(self, site_slug: str, profile_id: str | None = None) -> bool:
        return self.store.delete(profile_id, site_slug, "storage-state")

    @staticmethod
    def manual_login_required(site_slug: str) -> dict[str, str]:
        site = get_site(site_slug)
        return {
            "status": "manual_login_required",
            "site": site.slug,
            "message": (
                "Login harus dilakukan manual lewat browser headed. CAPTCHA/OTP diselesaikan manusia; "
                "agent tidak mencoba solve atau submit otomatis."
            ),
        }
