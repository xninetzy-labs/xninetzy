import pytest

from app.ecosystem.command_router import parse_command


def test_media_info_command():
    assert parse_command("/media-info") == ("media_info", {})


def test_analyze_media_command():
    assert parse_command("/analyze-media") == ("analyze_media", {})


def test_media_info_no_media_returns_message():
    from app.media.media_tools import media_info

    out = media_info.invoke({"metadata": {}})
    assert "Tidak ada media" in out


def test_media_info_with_media():
    from app.media.media_tools import media_info

    md = {"media": {"hasMedia": True, "mediaType": "document",
                    "filename": "bab1.pdf", "mimetype": "application/pdf", "fileLength": 1234}}
    out = media_info.invoke({"metadata": md})
    assert "bab1.pdf" in out
    assert "document" in out


@pytest.mark.asyncio
async def test_analyze_media_no_media():
    from app.media.media_tools import analyze_media

    out = await analyze_media.ainvoke({"chat_id": "c", "metadata": {}})
    assert "Tidak ada media" in out


@pytest.mark.asyncio
async def test_analyze_media_unsupported_type():
    from app.media.media_tools import analyze_media

    md = {"media": {"hasMedia": True, "mediaType": "image", "messageId": "m1"}}
    out = await analyze_media.ainvoke({"chat_id": "c", "metadata": md})
    assert "belum didukung" in out.lower()


def test_media_tools_registered():
    from app.tools.registry import get_tool_names

    names = get_tool_names()
    for t in ("media_read_document", "media_info", "analyze_media", "media_ingest_to_knowledge"):
        assert t in names
