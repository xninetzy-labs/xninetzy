from __future__ import annotations

import pytest

from xninetzy.os.security.guards import (
    SecurityError,
    _host_is_private,
    redact_secrets,
    safe_fetch,
)


def test_redact_strips_openai_key() -> None:
    text = "Token: sk-abcdefghijklmnop12345xyz"
    assert "sk-" not in redact_secrets(text)
    assert "[REDACTED]" in redact_secrets(text)


def test_redact_strips_github_token() -> None:
    text = "ghp_abc123def456ghi789jkl012mno345pqr678"
    assert redact_secrets(text) == "[REDACTED]"


def test_redact_strips_anthropic_key() -> None:
    text = "sk-ant-api03-abcdefghijklmnop12345"
    assert "sk-ant" not in redact_secrets(text)


def test_redact_preserves_clean_text() -> None:
    text = "no secrets in this text at all"
    assert redact_secrets(text) == text


def test_redact_strips_private_key_block() -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nfoo\n-----END RSA PRIVATE KEY-----"
    out = redact_secrets(text)
    assert "BEGIN" not in out or "REDACTED" in out


def test_host_is_private_localhost() -> None:
    assert _host_is_private("127.0.0.1") is True
    assert _host_is_private("localhost") is True
    assert _host_is_private("0.0.0.0") is True


def test_host_is_private_rfc1918() -> None:
    assert _host_is_private("10.1.2.3") is True
    assert _host_is_private("192.168.1.1") is True
    assert _host_is_private("172.16.0.1") is True


def test_host_is_private_public() -> None:
    assert _host_is_private("example.com") is False
    assert _host_is_private("8.8.8.8") is False


@pytest.mark.asyncio
async def test_safe_fetch_blocks_invalid_scheme() -> None:
    with pytest.raises(SecurityError) as exc:
        await safe_fetch("file:///etc/passwd")
    assert exc.value.code == "INVALID_SCHEME"


@pytest.mark.asyncio
async def test_safe_fetch_blocks_localhost_by_default() -> None:
    with pytest.raises(SecurityError) as exc:
        await safe_fetch("http://127.0.0.1:8080/admin")
    assert exc.value.code == "SSRF_BLOCKED"
