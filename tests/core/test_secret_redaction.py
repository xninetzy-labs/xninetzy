from __future__ import annotations

import pytest

from xninetzy.core.security import redact_secrets, sanitize_tool_output

REDACTED = "[REDACTED]"

_BODY = "abcdefghijklmnopqrstuvwxyz012345"


def _tok(prefix: str, body: str = _BODY) -> str:
    return prefix + body


SECRETS = [
    ("stripe_live", _tok("sk_live_")),
    ("stripe_test", _tok("sk_test_")),
    ("stripe_restricted", _tok("rk_live_")),
    ("stripe_webhook", _tok("whsec_")),
    ("huggingface", _tok("hf_")),
    ("google_oauth", "ya29." + _BODY),
    ("gitlab_pat", "glpat-" + _BODY),
    ("slack_app", "xapp-1-A0123456789-" + _BODY),
    ("slack_bot", "xoxb-1234567890-" + _BODY),
    ("openai", "sk-" + _BODY),
    ("anthropic", "sk-ant-" + _BODY),
    ("github_pat", "ghp_" + _BODY),
    ("aws_akid", "AKIA" + "ABCDEFGHIJKLMNOP"),
    ("google_api", "AIza" + _BODY),
    ("jwt", "eyJ" + _BODY + ".eyJ" + _BODY + "." + _BODY),
    ("bearer", "Authorization: Bearer " + _BODY),
]


@pytest.mark.parametrize("label,secret", SECRETS)
def test_secret_is_redacted(label, secret):
    out = redact_secrets(f"prefix {secret} suffix")
    assert REDACTED in out, label
    needle = secret.split(".")[-1] if label == "jwt" else secret
    assert needle not in out, label


def test_pem_private_key_block_redacted():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEabc\n-----END RSA PRIVATE KEY-----"
    out = redact_secrets(text)
    assert "BEGIN RSA PRIVATE KEY" not in out


def test_plain_text_is_untouched():
    text = "the quick brown fox jumps over 12345 lazy dogs (cmid 1725)"
    assert redact_secrets(text) == text


def test_sanitize_tool_output_redacts_nested_secret():
    secret = _tok("sk_live_")
    payload = {"config": {"token": secret}, "ok": True}
    cleaned = sanitize_tool_output(payload)
    assert secret not in str(cleaned)
    assert cleaned["ok"] is True
