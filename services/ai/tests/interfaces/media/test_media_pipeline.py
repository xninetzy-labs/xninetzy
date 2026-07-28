from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest

from app.xninetzy.interfaces.media import media_tools
from app.xninetzy.interfaces.whatsapp.client import WaToolError


@pytest.mark.asyncio
async def test_download_media_falls_back_to_mcp_content(monkeypatch, tmp_path):
    raw = b"isi dokumen dari whatsapp"

    async def fake_download(chat_id, message_id):
        return {
            "ok": True,
            "local_path": "/path/tidak/terlihat/file.txt",
            "filename": "catatan.txt",
            "mime_type": "text/plain",
        }

    async def fake_content(chat_id, message_id):
        return {
            "ok": True,
            "content_base64": base64.b64encode(raw).decode("ascii"),
            "filename": "../../catatan.txt",
            "mime_type": "text/plain",
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    monkeypatch.setattr(media_tools, "download_media_message", fake_download)
    monkeypatch.setattr(media_tools, "get_media_content", fake_content)
    monkeypatch.setattr(media_tools, "_media_cache_root", lambda: tmp_path)

    downloaded = await media_tools._download_media("628@s.whatsapp.net", "MSG-1")
    local_path = Path(downloaded["local_path"])
    assert local_path.is_file()
    assert local_path.read_bytes() == raw
    assert tmp_path in local_path.parents
    assert "content_base64" not in downloaded


def test_materialize_rejects_wrong_checksum(tmp_path, monkeypatch):
    raw = b"trusted bytes"
    monkeypatch.setattr(media_tools, "_media_cache_root", lambda: tmp_path)

    with pytest.raises(WaToolError, match="Checksum"):
        media_tools._materialize_media_content(
            "chat",
            "message",
            {
                "content_base64": base64.b64encode(raw).decode("ascii"),
                "filename": "file.txt",
                "size_bytes": len(raw),
                "sha256": "0" * 64,
            },
        )


@pytest.mark.asyncio
async def test_build_media_prompt_context_reads_quoted_document(monkeypatch):
    async def fake_read(chat_id, message_id):
        assert chat_id == "group@g.us"
        assert message_id == "QUOTED-1"
        return {"text": "Isi penting dari PDF.", "error": None}

    monkeypatch.setattr(media_tools, "_read_document", fake_read)
    context = await media_tools.build_media_prompt_context(
        "group@g.us",
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
