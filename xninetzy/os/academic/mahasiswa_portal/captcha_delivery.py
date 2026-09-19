from __future__ import annotations

import asyncio
import base64
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.types import ImageContent, TextContent

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaptchaEnvelope:
    png_bytes: bytes
    challenge_id: str
    expires_at: str
    site_slug: str = "uacc"
    label: str = "UACC"
    reply_command: str = ""


@dataclass
class CaptchaDeliveryResult:
    delivered_via: str
    text: str
    blocks: list[TextContent | ImageContent] | None = None
    png_path: str | None = None
    error: str | None = None


def build_envelope(
    challenge: dict[str, Any],
    png_bytes: bytes,
    site_slug: str = "uacc",
    label: str = "UACC",
) -> CaptchaEnvelope:
    reply_command = (
        f"/uacc-captcha {challenge['challenge_id']} JAWABAN"
        if site_slug == "uacc"
        else f"/captcha {challenge['challenge_id']} JAWABAN"
    )
    return CaptchaEnvelope(
        png_bytes=png_bytes,
        challenge_id=challenge["challenge_id"],
        expires_at=str(challenge["expires_at"]),
        site_slug=site_slug,
        label=label,
        reply_command=reply_command,
    )


def _save_png(envelope: CaptchaEnvelope, captcha_dir: str) -> str:
    directory = Path(captcha_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"uacc_captcha_{envelope.challenge_id}.png"
    path.write_bytes(envelope.png_bytes)
    return str(path)


def _open_local(png_path: str) -> None:
    try:
        subprocess.Popen(
            ["xdg-open", png_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def build_mcp_blocks(
    envelope: CaptchaEnvelope, text: str
) -> list[TextContent | ImageContent]:
    blocks: list[TextContent | ImageContent] = [
        TextContent(type="text", text=text)
    ]
    blocks.append(
        ImageContent(
            type="image",
            data=base64.b64encode(envelope.png_bytes).decode("ascii"),
            mimeType="image/png",
        )
    )
    return blocks


async def _persist_captcha_inbox(
    envelope: CaptchaEnvelope, text: str, owner_chat_id: str
) -> bool:
    """Persist a CAPTCHA notification to the owner inbox (best-effort)."""
    try:
        from xninetzy.os.inbox.service import capture_item

        full_text = (
            f"{text}\n\n"
            f"Challenge ID: {envelope.challenge_id}\n"
            f"Reply: {envelope.reply_command}\n"
            f"PNG saved at: see event metadata"
        )
        capture_item(full_text, kind="note", chat_id=owner_chat_id)
        return True
    except Exception as exc:
        logger.warning("CAPTCHA inbox notification failed: %s", exc)
        return False


async def deliver_captcha(
    envelope: CaptchaEnvelope,
    *,
    owner_chat_id: str | None = None,
    captcha_dir: str = "/tmp/opencode",
) -> CaptchaDeliveryResult:
    """Deliver a CAPTCHA challenge to the owner.

    The pivot to MCP-only removed  delivery: the envelope is now
    persisted to the owner inbox (with image data attached in MCP blocks
    when available). The CAPTCHA PNG is also saved locally so an interactive
    client can render it.
    """
    text = (
        f"CAPTCHA {envelope.label} untuk challenge `{envelope.challenge_id}`.\n"
        f"Balas: {envelope.reply_command}\n"
        f"Berlaku sampai: {envelope.expires_at}\n\n"
        "CAPTCHA harus dijawab manual oleh owner."
    )

    owner_id = owner_chat_id or get_settings().OWNER_CHAT_ID.strip() or "owner"
    png_path = _save_png(envelope, captcha_dir)
    try:
        await asyncio.to_thread(_open_local, png_path)
    except Exception:
        pass

    local_hint = f"\n\nPNG lokal: {png_path}"
    full_text = text + local_hint
    inbox_ok = await _persist_captcha_inbox(envelope, full_text, owner_id)
    blocks = build_mcp_blocks(envelope, full_text)

    return CaptchaDeliveryResult(
        delivered_via="owner_inbox" if inbox_ok else "mcp_image",
        text=full_text,
        blocks=blocks,
        png_path=png_path,
        error=None if inbox_ok else "owner_inbox unavailable; PNG saved locally",
    )
