from pydantic import SecretStr

from app.xninetzy.core.config import Settings
from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
    CampusCredentialError,
    resolve_campus_credentials,
)


def test_campus_credentials_reuse_hebat_without_plaintext_repr():
    settings = Settings(HEBAT_USERNAME="student", HEBAT_PASSWORD="private-value")

    credentials = resolve_campus_credentials("hebat", settings)

    assert credentials.username == "student"
    assert isinstance(credentials.password, SecretStr)
    assert credentials.password.get_secret_value() == "private-value"
    assert "private-value" not in repr(credentials)


def test_campus_credentials_fail_closed_when_missing():
    settings = Settings(HEBAT_USERNAME="", HEBAT_PASSWORD="")

    try:
        resolve_campus_credentials("hebat", settings)
    except CampusCredentialError as exc:
        assert "belum dikonfigurasi" in str(exc)
    else:
        raise AssertionError("Missing credentials should fail closed")
