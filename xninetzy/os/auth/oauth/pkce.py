from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PKCEChallenge:
    code_verifier: str
    code_challenge: str
    code_challenge_method: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code_verifier": self.code_verifier,
            "code_challenge": self.code_challenge,
            "code_challenge_method": self.code_challenge_method,
        }


def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_pkce() -> PKCEChallenge:
    """Generate PKCE S256 challenge per RFC 7636."""
    verifier = _b64url_no_pad(secrets.token_bytes(32))
    challenge = _b64url_no_pad(hashlib.sha256(verifier.encode("ascii")).digest())
    return PKCEChallenge(
        code_verifier=verifier,
        code_challenge=challenge,
        code_challenge_method="S256",
    )


def verify_pkce(verifier: str, challenge: str, method: str = "S256") -> bool:
    if method.upper() != "S256":
        return False
    expected = _b64url_no_pad(hashlib.sha256(verifier.encode("ascii")).digest())
    return secrets.compare_digest(expected, challenge)


__all__ = ["PKCEChallenge", "generate_pkce", "verify_pkce"]
