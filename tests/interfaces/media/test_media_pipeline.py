from __future__ import annotations

import pytest

from xninetzy.interfaces.media import media_tools


@pytest.mark.asyncio
async def test_resolve_local_uses_media_store(monkeypatch, tmp_path):
    payload_path = tmp_path / "doc.txt"
    payload_path.write_text("isi dokumen", encoding="utf-8")
    stored = {
        "media_id": "MSG-1",
        "local_path": str(payload_path),
        "mime_type": "text/plain",
        "file_name": "doc.txt",
    }

    monkeypatch.setattr(media_tools, "get_media_item", lambda message_id: stored)

    resolved = media_tools._resolve_local("62800", "MSG-1")
    assert resolved["local_path"] == str(payload_path)
    assert resolved["mime_type"] == "text/plain"
    assert resolved["file_name"] == "doc.txt"


def test_resolve_local_raises_when_missing(monkeypatch):
    monkeypatch.setattr(media_tools, "get_media_item", lambda message_id: None)

    with pytest.raises(media_tools.MediaUnavailableError, match="belum tersedia"):
        media_tools._resolve_local("62800", "MSG-1")


def test_resolve_local_raises_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        media_tools,
        "get_media_item",
        lambda message_id: {
            "media_id": "MSG-1",
            "local_path": str(tmp_path / "absent.bin"),
            "mime_type": None,
            "file_name": "absent.bin",
        },
    )

    with pytest.raises(media_tools.MediaUnavailableError, match="tidak ada di disk"):
        media_tools._resolve_local("62800", "MSG-1")


def test_resolve_local_requires_message_id(monkeypatch):
    with pytest.raises(media_tools.MediaUnavailableError, match="message_id"):
        media_tools._resolve_local("62800", "")


@pytest.mark.asyncio
async def test_read_document_uses_stored_local_path(monkeypatch, tmp_path):
    payload_path = tmp_path / "doc.txt"
    payload_path.write_text("hello world", encoding="utf-8")
    parsed = {
        "text": "hello world",
        "kind": "text",
        "char_count": 11,
        "error": None,
    }

    monkeypatch.setattr(
        media_tools,
        "_resolve_local",
        lambda chat_id, message_id: {
            "media_id": message_id,
            "local_path": str(payload_path),
            "mime_type": "text/plain",
            "file_name": "doc.txt",
        },
    )
    monkeypatch.setattr(
        media_tools, "parse_document", lambda *args, **kwargs: dict(parsed)
    )

    saved: list[dict] = []

    def fake_save(**kwargs):
        saved.append(kwargs)

    monkeypatch.setattr(media_tools, "save_media_item", fake_save)

    result = await media_tools._read_document("62800", "MSG-1")
    assert result["text"] == "hello world"
    assert result["_meta"]["local_path"] == str(payload_path)
    assert saved and saved[0]["local_path"] == str(payload_path)
    assert saved[0]["media_type"] == "document"


@pytest.mark.asyncio
async def test_build_media_prompt_context_reads_quoted_document(monkeypatch):
    async def fake_read(chat_id, message_id):
        assert chat_id == "group@group.local"
        assert message_id == "QUOTED-1"
        return {"text": "Isi penting dari PDF.", "error": None, "_meta": {}}

    monkeypatch.setattr(media_tools, "_read_document", fake_read)
    context = await media_tools.build_media_prompt_context(
        "group@group.local",
        {
            "quotedMedia": {
                "hasMedia": True,
                "mediaType": "document",
                "messageId": "QUOTED-1",
                "filename": "materi.pdf",
            }
        },
    )

    assert "[Media Extracted]" in context
    assert "materi.pdf" in context
    assert "Isi penting dari PDF." in context
