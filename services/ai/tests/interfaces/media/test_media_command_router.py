import pytest

from app.xninetzy.ecosystem.command_router import parse_command


def test_media_info_command():
    assert parse_command("/media-info") == ("media_info", {})


def test_analyze_media_command():
    assert parse_command("/analyze-media") == ("analyze_media", {})


def test_media_info_no_media_returns_message():
    from app.xninetzy.interfaces.media.media_tools import media_info

    out = media_info.invoke({"metadata": {}})
    assert "Tidak ada media" in out


def test_media_info_with_media():
    from app.xninetzy.interfaces.media.media_tools import media_info

    md = {"media": {"hasMedia": True, "mediaType": "document",
                    "filename": "bab1.pdf", "mimetype": "application/pdf", "fileLength": 1234}}
    out = media_info.invoke({"metadata": md})
    assert "bab1.pdf" in out
    assert "document" in out


@pytest.mark.asyncio
async def test_analyze_media_no_media():
    from app.xninetzy.interfaces.media.media_tools import analyze_media

    out = await analyze_media.ainvoke({"chat_id": "c", "metadata": {}})
    assert "Tidak ada media" in out


@pytest.mark.asyncio
async def test_analyze_media_image_uses_ocr(monkeypatch):
    from app.xninetzy.interfaces.media import media_tools

    md = {"media": {"hasMedia": True, "mediaType": "image", "messageId": "m1"}}

    async def fake_read_image(chat_id, message_id):
        assert (chat_id, message_id) == ("c", "m1")
        return {
            "text": "OCR berhasil",
            "char_count": 12,
            "kind": "image_ocr",
            "width": 100,
            "height": 50,
            "error": None,
            "_meta": {"filename": "screen.png"},
        }

    monkeypatch.setattr(media_tools, "_read_image", fake_read_image)
    out = await media_tools.analyze_media.ainvoke({"chat_id": "c", "metadata": md})
    assert "Image OCR" in out
    assert "OCR berhasil" in out


def test_media_info_supports_quoted_media():
    from app.xninetzy.interfaces.media.media_tools import media_info

    md = {
        "quotedMedia": {
            "hasMedia": True,
            "mediaType": "document",
            "messageId": "quoted-1",
            "filename": "quoted.pdf",
        }
    }
    out = media_info.invoke({"metadata": md})
    assert "quoted.pdf" in out


def test_media_tools_registered():
    from app.xninetzy.tools.registry import get_tool_names

    names = get_tool_names()
    for t in (
        "media_read_document",
        "media_read_image",
        "media_info",
        "analyze_media",
        "media_ingest_to_knowledge",
    ):
        assert t in names
