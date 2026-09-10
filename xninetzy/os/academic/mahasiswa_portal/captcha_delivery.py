from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.types import ImageContent, TextContent

from app.xninetzy.core.config import get_settings
from app.xninetzy.interfaces.whatsapp.client import WaToolError, call_wa_tool


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


def _wa_healthcheck(timeout_seconds: float) -> bool:
    settings = get_settings()
    base = settings.WA_MCP_BASE_URL.rstrip("/")
    headers = {}
    if settings.WA_MCP_API_KEY:
        headers["Authorization"] = f"Bearer {settings.WA_MCP_API_KEY}"
    request = urllib.request.Request(f"{base}/health", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    return bool(data.get("status") == "ok" and data.get("socket_ready"))


async def _wa_send_image(jid: str, envelope: CaptchaEnvelope) -> None:
    source = base64.b64encode(envelope.png_bytes).decode("ascii")
    caption = (
        f"Login {envelope.label}\n\n"
        f"Balas: {envelope.reply_command}\n"
        f"Berlaku sampai: {envelope.expires_at}\n\n"
        "CAPTCHA harus dijawab manual oleh owner."
    )
    await call_wa_tool(
        "send_image", {"jid": jid, "source": source, "caption": caption}
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


async def deliver_captcha(
    envelope: CaptchaEnvelope,
    *,
    wa_jid: str | None,
    wa_preferred: bool = True,
    auto_open: bool = True,
    captcha_dir: str = "/tmp/opencode",
    wa_timeout_seconds: float = 8.0,
) -> CaptchaDeliveryResult:
    text = (
        f"CAPTCHA {envelope.label} untuk challenge `{envelope.challenge_id}`.\n"
        f"Balas: {envelope.reply_command}\n"
        f"Berlaku sampai: {envelope.expires_at}\n\n"
        "CAPTCHA harus dijawab manual oleh owner."
    )
    wa_error: str | None = None
    if wa_preferred and wa_jid:
        healthy = await asyncio.to_thread(_wa_healthcheck, wa_timeout_seconds)
        if healthy:
            try:
                await _wa_send_image(wa_jid, envelope)
                return CaptchaDeliveryResult(
                    delivered_via="whatsapp",
                    text=text,
                    error=None,
                )
            except WaToolError as exc:
                wa_error = str(exc)
        else:
            wa_error = "WA MCP tidak siap (healthcheck gagal)"
    else:
        wa_error = "WA tidak dipilih atau target owner belum dikonfigurasi"
    png_path = _save_png(envelope, captcha_dir)
    if auto_open:
        _open_local(png_path)
    local_hint = f"\n\nPNG lokal: {png_path}"
    blocks = build_mcp_blocks(envelope, text + local_hint)
    return CaptchaDeliveryResult(
        delivered_via="mcp_image",
        text=text + local_hint,
        blocks=blocks,
        png_path=png_path,
        error=wa_error,
    )