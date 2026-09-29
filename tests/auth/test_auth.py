from __future__ import annotations

from xninetzy.os.auth.oauth.pkce import PKCEChallenge, generate_pkce, verify_pkce
from xninetzy.os.auth.oauth.providers import (
    build_authorization_url,
    get_provider,
    list_providers,
)
from xninetzy.os.auth.policies.redaction import redact_payload, redact_text
from xninetzy.os.auth.policies.url_policy import (
    URLBlockedError,
    assert_safe_url,
    is_blocked_scheme,
    is_private_address,
)
from xninetzy.os.auth.providers.adapters import (
    get_provider_adapter,
    list_provider_adapters,
)
from xninetzy.os.auth.sessions.state import (
    AuthSessionStatus,
    create_session,
    get_session,
    is_valid_transition,
    list_sessions,
    new_state_token,
    transition,
)


def test_pkce_round_trip() -> None:
    challenge: PKCEChallenge = generate_pkce()
    assert len(challenge.code_verifier) > 40
    assert challenge.code_challenge_method == "S256"
    assert verify_pkce(challenge.code_verifier, challenge.code_challenge)
    assert not verify_pkce("wrong", challenge.code_challenge)
    assert not verify_pkce(challenge.code_verifier, "wrong", method="plain")


def test_session_state_machine_blocks_invalid_transitions() -> None:
    assert is_valid_transition(AuthSessionStatus.CREATED, AuthSessionStatus.AUTHENTICATED) is False
    assert is_valid_transition(AuthSessionStatus.AUTHENTICATED, AuthSessionStatus.REVOKED) is True
    assert is_valid_transition(AuthSessionStatus.REVOKED, AuthSessionStatus.AUTHENTICATED) is False


def test_create_and_transition_session() -> None:
    record = create_session(
        owner="local-owner",
        provider="kaggle",
        account="default",
        method="oauth",
        scopes=("public", "private"),
        state_token=new_state_token(),
        pkce_verifier="abc",
        authorization_url="https://www.kaggle.com/oauth/authorize?x=1",
        ttl_seconds=120,
    )
    assert record.state is AuthSessionStatus.CREATED
    assert record.session_id.startswith("auth-")
    assert "public" in record.scopes
    advanced = transition(
        record.session_id,
        to=AuthSessionStatus.WAITING_FOR_USER,
    )
    assert advanced is not None and advanced.state is AuthSessionStatus.WAITING_FOR_USER
    again = transition(record.session_id, to=AuthSessionStatus.AUTHENTICATED)
    assert again is not None and again.state is AuthSessionStatus.AUTHENTICATED


def test_invalid_transition_is_noop() -> None:
    record = create_session(
        owner="local-owner",
        provider="kaggle",
        account="default",
        method="oauth",
    )
    advanced = transition(record.session_id, to=AuthSessionStatus.AUTHENTICATED)
    assert advanced is not None
    assert advanced.state is AuthSessionStatus.CREATED


def test_list_and_get_session() -> None:
    record = create_session(
        owner="local-owner",
        provider="kaggle",
        account="default",
        method="browser",
    )
    fetched = get_session(record.session_id)
    assert fetched is not None and fetched.session_id == record.session_id
    rows = list_sessions(owner="local-owner", provider="kaggle")
    assert any(r.session_id == record.session_id for r in rows)


def test_secret_store_round_trip_and_revoke() -> None:
    from xninetzy.os.auth.secrets.store import SecretStore

    store = SecretStore()
    ref = SecretStore.generate_credential_ref("kaggle", "default")
    meta = store.set(ref, "value", provider="kaggle", account="default")
    assert meta.credential_ref == ref
    assert store.exists(ref)
    assert store.get_bytes(ref) == b"value"
    assert store.revoke(ref) is True
    assert store.get_bytes(ref) is None


def test_oauth_provider_list_contains_google() -> None:
    providers = list_providers()
    assert any(p.provider_id == "google" for p in providers)
    google = get_provider("google")
    assert google is not None
    assert "openid" in google.default_scopes


def test_build_authorization_url_validates_against_policy() -> None:
    google = get_provider("google")
    assert google is not None
    url = build_authorization_url(
        google,
        state="abc",
        code_challenge="xyz",
        scopes=("openid", "email"),
        client_id_override="test-client",
    )
    assert "accounts.google.com" in url
    assert "code_challenge=xyz" in url
    assert "code_challenge_method=S256" in url


def test_url_policy_blocks_dangerous_schemes() -> None:
    assert is_blocked_scheme("javascript:alert(1)")
    assert is_blocked_scheme("file:///etc/passwd")
    assert is_private_address("http://10.0.0.5/")
    assert is_private_address("http://localhost:8080/")
    try:
        assert_safe_url("javascript:alert(1)")
    except URLBlockedError:
        pass
    else:
        raise AssertionError("javascript: should be blocked")
    try:
        assert_safe_url("http://10.0.0.5/")
    except URLBlockedError:
        pass
    else:
        raise AssertionError("private ip should be blocked")
    assert_safe_url("https://www.kaggle.com/oauth/authorize")


def test_url_policy_enforces_origin_allowlist() -> None:
    try:
        assert_safe_url(
            "https://attacker.example.com/oauth/callback",
            allowed_origins=("kaggle.com",),
        )
    except URLBlockedError:
        pass
    else:
        raise AssertionError("non-allowlisted origin should be blocked")
    assert_safe_url(
        "https://www.kaggle.com/account/login",
        allowed_origins=("kaggle.com",),
    )


def test_redaction_removes_bearer_and_cookies() -> None:
    text = (
        "Authorization: Bearer abcdef1234567890abcdef\n"
        "access_token=gh_abcd1234567890abcd\n"
        "Set-Cookie: auth=xyz\n"
        "client_secret=topsecret1234567890\n"
    )
    out = redact_text(text)
    assert "Bearer" not in out
    assert "abcdef1234567890abcdef" not in out
    assert "gh_abcd1234567890abcd" not in out
    assert "Set-Cookie" not in out
    assert "topsecret1234567890" not in out


def test_redaction_payload_recurses() -> None:
    payload = {
        "headers": {"Authorization": "Bearer abcdef1234567890abcdef"},
        "ok": True,
    }
    redacted = redact_payload(payload)
    assert "abcdef1234567890abcdef" not in redacted["headers"]["Authorization"]
    assert redacted["ok"] is True


def test_provider_adapters_loaded() -> None:
    adapters = list_provider_adapters()
    names = {a.provider_id for a in adapters}
    assert {"kaggle", "google", "github"}.issubset(names)
    assert get_provider_adapter("kaggle") is not None
    assert get_provider_adapter("google") is not None


def test_hybrid_provider_metadata_exposed() -> None:
    by_id = {p.provider_id: p for p in list_providers()}
    assert by_id["kaggle"].preferred_method == "api_token"
    assert "api_token" in by_id["kaggle"].fallback_methods
    assert "oauth" in by_id["kaggle"].fallback_methods
    assert by_id["kaggle"].api_token_env == ("KAGGLE_USERNAME", "KAGGLE_KEY")
    adapters_by_id = {a.provider_id: a for a in list_provider_adapters()}
    for pid in ("kaggle", "google", "github"):
        assert adapters_by_id[pid].extra.get("hybrid") is True
        assert "primary_method" in adapters_by_id[pid].extra
        assert "fallback_methods" in adapters_by_id[pid].extra


def test_build_authorization_url_requires_client_id(monkeypatch) -> None:
    from xninetzy.os.auth.oauth.providers import OAuthConfigError

    monkeypatch.delenv("XNINETZY_KAGGLE_CLIENT_ID", raising=False)
    try:
        build_authorization_url(get_provider("kaggle"), state="abc")
    except OAuthConfigError as exc:
        assert "XNINETZY_KAGGLE_CLIENT_ID" in str(exc)
    else:
        raise AssertionError("expected OAuthConfigError")
    url = build_authorization_url(
        get_provider("kaggle"),
        state="abc",
        client_id_override="override-id",
    )
    assert "client_id=override-id" in url


def test_callback_server_binds_and_receives_code() -> None:
    import time
    import urllib.request

    from xninetzy.os.auth.oauth.callback_server import (
        callback_server_status,
        start_callback_server,
        stop_callback_server,
    )

    received: list[dict] = []

    async def handler(result):
        received.append(result.to_safe_dict())
        return {"status": "ok"}

    bound = start_callback_server(handler)
    try:
        assert callback_server_status()["running"] is True
        assert bound.redirect_uri.startswith("http://127.0.0.1:")
        url = bound.redirect_uri + "?code=fake&state=test-state"
        resp = urllib.request.urlopen(url, timeout=5)
        assert resp.status == 200
        time.sleep(0.5)
        assert received and received[0]["code"] == "fake"
        assert received[0]["state"] == "test-state"
    finally:
        stop_callback_server()
    assert callback_server_status()["running"] is False


def test_url_policy_blocks_encoded_loopback() -> None:
    assert is_private_address("http://2130706433/")
    assert is_private_address("http://0x7f000001/")
    assert is_private_address("http://[::ffff:127.0.0.1]/")


def test_url_policy_allows_encoded_public() -> None:
    import ipaddress

    public = int(ipaddress.ip_address("8.8.8.8"))
    assert not is_private_address(f"http://{public}/")
