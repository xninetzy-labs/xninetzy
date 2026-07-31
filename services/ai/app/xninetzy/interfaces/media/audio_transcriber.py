"""Transcribe WhatsApp audio via an OpenAI-compatible transcription API.

Transcription is provider-independent and bounded by a 120s timeout. Only a
local cached file is read; media bytes stay in the AI service and are never
sent anywhere but the configured transcription endpoint.
"""
from __future__ import annotations

from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTS = {
    ".ogg",
    ".opus",
    ".mp3",
    ".m4a",
    ".mp4",
    ".wav",
    ".webm",
    ".amr",
    ".aac",
    ".flac",
    ".oga",
}

_MIME_EXT = {
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/webm": ".webm",
    "audio/amr": ".amr",
    "audio/flac": ".flac",
    "audio/oga": ".oga",
    "video/mp4": ".mp4",
    "video/ogg": ".ogg",
}


def _error(message: str) -> dict:
    return {
        "text": "",
        "char_count": 0,
        "kind": "audio_transcript",
        "error": message,
    }


def _resolve_ext(path: Path, mime_type: str | None, filename: str | None) -> str:
    for candidate in (path.suffix, Path(filename or "").suffix):
        if candidate and candidate.lower() in SUPPORTED_AUDIO_EXTS:
            return candidate.lower()
    if mime_type:
        return _MIME_EXT.get(mime_type.split(";")[0].strip().lower(), "")
    return ""


async def transcribe_audio(
    path: str,
    mime_type: str | None = None,
    filename: str | None = None,
) -> dict:
    """Transcribe an audio file into text.

    Returns ``{text, char_count, kind, error}``. ``error`` is None on success.
    """
    settings = get_settings()
    if not settings.AUDIO_TRANSCRIPTION_ENABLED:
        return _error("Transkripsi audio dinonaktifkan.")
    if not settings.OPENAI_API_KEY:
        return _error("OPENAI_API_KEY belum dikonfigurasi untuk transkripsi audio.")

    source = Path(path)
    if not source.exists() or not source.is_file():
        return _error(f"File tidak ditemukan: {filename or source.name}")
    if not _resolve_ext(source, mime_type, filename):
        return _error(
            f"Tipe audio belum didukung (mime={mime_type}, name={filename or source.name})"
        )

    display_name = filename or source.name
    try:
        import httpx
    except ImportError:
        return _error("Library httpx belum terinstall untuk transkripsi audio.")

    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    files = {"file": (display_name, open(source, "rb"), mime_type or "audio/ogg")}
    data = {"model": settings.AUDIO_TRANSCRIPTION_MODEL}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
        if response.status_code != 200:
            logger.warning(
                "Audio transcription failed (status=%s): %s",
                response.status_code,
                response.text[:500],
            )
            return _error(
                f"Transkripsi audio gagal (status {response.status_code}). "
                "Coba lagi nanti atau periksa konfigurasi provider."
            )
        payload = response.json()
    except Exception as exc:  # pragma: no cover - defensive around network calls
        logger.warning("Audio transcription error: %s", exc)
        return _error(f"Transkripsi audio gagal: {exc}")

    text = str(payload.get("text") or "").strip()
    if not text:
        return _error("Audio terbaca tetapi transkripsi tidak mengembalikan teks.")
    return {
        "text": text,
        "char_count": len(text),
        "kind": "audio_transcript",
        "error": None,
    }
