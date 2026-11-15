from __future__ import annotations

import re
import json
import string
from typing import Any


CHAT_ID_PATTERN = re.compile(
    r"(?P<local>[A-Za-z0-9][A-Za-z0-9._:\-]*)@"
    r"(?P<domain>chat\.local|group\.local|broadcast|newsletter)\b",
    re.IGNORECASE,
)


JID_PATTERN = CHAT_ID_PATTERN
_CHAT_DOMAIN_MARKER = re.compile(
    r"@(?:chat\.local|group\.local|broadcast|newsletter)\b", re.IGNORECASE
)
_LOCAL_CHARS = frozenset(string.ascii_letters + string.digits + "._:-")
_LOCAL_START = frozenset(string.ascii_letters + string.digits)


_SECRET_PATTERNS: tuple[str, ...] = (
    r"sk-ant-[A-Za-z0-9_\-]{16,}",
    r"sk-[A-Za-z0-9_\-]{16,}",
    r"ghp_[A-Za-z0-9]{16,}",
    r"gho_[A-Za-z0-9]{16,}",
    r"ghs_[A-Za-z0-9]{16,}",
    r"github_pat_[A-Za-z0-9_]{16,}",
    r"xox[abpsr]-[A-Za-z0-9\-]{10,}",
    r"xapp-[0-9]-[A-Za-z0-9\-]{10,}",
    r"AIza[A-Za-z0-9_\-]{16,}",
    r"ya29\.[A-Za-z0-9_\-]{20,}",
    r"AKIA[0-9A-Z]{12,}",
    r"(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,}",
    r"whsec_[A-Za-z0-9]{16,}",
    r"hf_[A-Za-z0-9]{16,}",
    r"glpat-[A-Za-z0-9_\-]{16,}",
    r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
    r"[Bb]earer\s+[A-Za-z0-9._\-]{20,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)
_SECRET_RE = re.compile("|".join(f"(?:{p})" for p in _SECRET_PATTERNS))
_REDACTION = "[REDACTED]"


def _mask_local(local: str) -> str:
    digits = "".join(ch for ch in local.split(":", 1)[0] if ch.isdigit())
    if len(digits) < 6:
        return "[redacted]"
    return f"{digits[:4]}{'*' * (len(digits) - 6)}{digits[-2:]}"


def redact_chat_ids_in_text(text: str) -> str:
    """Mask chat identifiers inside arbitrary tool output text."""
    # Search the fixed domain first, then walk its local token once. Searching
    # a greedy local pattern at every offset was quadratic on unrelated tokens.
    parts: list[str] = []
    cursor = 0
    for marker in _CHAT_DOMAIN_MARKER.finditer(text):
        end_local = marker.start()
        start_local = end_local
        while start_local > cursor and text[start_local - 1] in _LOCAL_CHARS:
            start_local -= 1
        while start_local < end_local and text[start_local] not in _LOCAL_START:
            start_local += 1
        if start_local == end_local:
            continue
        parts.extend((text[cursor:start_local], _mask_local(text[start_local:end_local]), marker.group()))
        cursor = marker.end()
    parts.append(text[cursor:])
    return "".join(parts)


def redact_jids_in_text(text: str) -> str:
    """Backwards-compatible alias for redact_chat_ids_in_text."""
    return redact_chat_ids_in_text(text)


def redact_secrets(text: str) -> str:
    """Strip known cloud / VCS secret patterns from any text payload."""
    if not text:
        return text
    text = _SECRET_RE.sub(_REDACTION, text)
    return re.sub(r"(?i)\b(password|passwd|api_key|access_token|refresh_token|client_secret)\s*[:=]\s*[^\s,;]+",
                  lambda match: match.group(1) + "=" + _REDACTION, text)


def sanitize_tool_output(value: Any) -> Any:
    """Recursively redact chat identifiers AND known secrets from tool output."""
    if isinstance(value, str):
        if value.lstrip().startswith(("{", "[")):
            try:
                structured = json.loads(value)
            except (ValueError, TypeError):
                pass
            else:
                if isinstance(structured, (dict, list)):
                    return json.dumps(sanitize_tool_output(structured), ensure_ascii=False)
        return redact_secrets(redact_chat_ids_in_text(value))
    if isinstance(value, dict):
        sensitive = {"password", "passwd", "api_key", "apikey", "token", "secret", "access_token", "refresh_token",
                     "authorization", "cookie", "cookies", "session_token", "private_key", "client_secret"}
        return {key: (_REDACTION if str(key).lower().replace("-", "_") in sensitive else sanitize_tool_output(item))
                for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_tool_output(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_tool_output(item) for item in value)
    return value


TRUSTED_CONTEXT_DROPPED_KEYS = frozenset(
    {"chat_id", "sender_id", "sender_name", "chat_type", "group_name"}
)


def strip_trusted_context(value: Any) -> Any:
    """Drop trusted-context keys from dict outputs that would leak server identity."""
    if isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            structured = json.loads(value)
        except (TypeError, ValueError):
            return value
        if isinstance(structured, (dict, list)):
            return json.dumps(strip_trusted_context(structured), ensure_ascii=False)
    if isinstance(value, dict):
        cleaned = {
            key: strip_trusted_context(item)
            for key, item in value.items()
            if key not in TRUSTED_CONTEXT_DROPPED_KEYS
        }
        return cleaned
    if isinstance(value, list):
        return [strip_trusted_context(item) for item in value]
    if isinstance(value, tuple):
        return tuple(strip_trusted_context(item) for item in value)
    return value
