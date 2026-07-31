"""Offline tests for WhatsApp audio transcription (HTTP call mocked)."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from app.xninetzy.interfaces.media import audio_transcriber


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


def _settings(**overrides) -> SimpleNamespace:
    values = {
        "AUDIO_TRANSCRIPTION_ENABLED": True,
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_BASE_URL": "https://api.openai.com/v1/",
        "AUDIO_TRANSCRIPTION_MODEL": "whisper-1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_transcribe_audio_success(monkeypatch, tmp_path):
    audio_file = tmp_path / "voice.mp3"
    audio_file.write_bytes(b"fake audio bytes")
    captured = {}

    async def fake_post(self, url, headers=None, files=None, data=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["files"] = files
        captured["data"] = data
        return _FakeResponse(200, {"text": "Halo ini voice note."})

    monkeypatch.setattr(audio_transcriber, "get_settings", lambda: _settings())
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await audio_transcriber.transcribe_audio(
        str(audio_file), mime_type=None, filename="voice.mp3"
    )

    assert result["error"] is None
    assert result["kind"] == "audio_transcript"
    assert result["text"] == "Halo ini voice note."
    assert result["char_count"] == len("Halo ini voice note.")
    assert captured["url"] == "https://api.openai.com/v1/audio/transcriptions"
    assert captured["headers"] == {"Authorization": "Bearer sk-test"}
    assert captured["data"] == {"model": "whisper-1"}
    name, handle, mime = captured["files"]["file"]
    assert name == "voice.mp3"
    assert mime == "audio/ogg"


@pytest.mark.asyncio
async def test_transcribe_audio_disabled(monkeypatch):
    monkeypatch.setattr(
        audio_transcriber,
        "get_settings",
        lambda: _settings(AUDIO_TRANSCRIPTION_ENABLED=False),
    )

    result = await audio_transcriber.transcribe_audio("/tmp/voice.mp3")

    assert result["error"] == "Transkripsi audio dinonaktifkan."
    assert result["text"] == ""
    assert result["char_count"] == 0


@pytest.mark.asyncio
async def test_transcribe_audio_missing_api_key(monkeypatch):
    monkeypatch.setattr(
        audio_transcriber,
        "get_settings",
        lambda: _settings(OPENAI_API_KEY=""),
    )

    result = await audio_transcriber.transcribe_audio("/tmp/voice.mp3")

    assert result["error"] == "OPENAI_API_KEY belum dikonfigurasi untuk transkripsi audio."
    assert result["text"] == ""


@pytest.mark.asyncio
async def test_transcribe_audio_unsupported_extension(monkeypatch, tmp_path):
    unsupported = tmp_path / "note.xyz"
    unsupported.write_bytes(b"data")
    monkeypatch.setattr(audio_transcriber, "get_settings", lambda: _settings())

    result = await audio_transcriber.transcribe_audio(str(unsupported))

    assert "belum didukung" in result["error"]
    assert result["text"] == ""


@pytest.mark.asyncio
async def test_transcribe_audio_non_200_returns_friendly_error(monkeypatch, tmp_path):
    audio_file = tmp_path / "voice.mp3"
    audio_file.write_bytes(b"fake audio bytes")

    async def fake_post(self, url, headers=None, files=None, data=None):
        return _FakeResponse(500, text="server error")

    monkeypatch.setattr(audio_transcriber, "get_settings", lambda: _settings())
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await audio_transcriber.transcribe_audio(
        str(audio_file), mime_type="audio/mpeg", filename="voice.mp3"
    )

    assert "status 500" in result["error"]
    assert result["text"] == ""
