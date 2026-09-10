from __future__ import annotations

import pytest

from app.xninetzy.os.academic.hebat import tools as hebat_tools
from app.xninetzy.tools.errors import (
    ERROR_CODE_PATTERN,
    ToolErrorCode,
    parse_tool_error,
    tool_error,
)


def test_tool_error_formats_contract():
    text = tool_error(ToolErrorCode.NOT_FOUND, "Token `X` tidak valid.")
    assert text == "❌ [NOT_FOUND] Token `X` tidak valid."
    assert parse_tool_error(text) == ("NOT_FOUND", "Token `X` tidak valid.")


def test_tool_error_appends_valid_values():
    text = tool_error(
        ToolErrorCode.INVALID_INPUT, "Format salah.", valid_values=[".pdf", ".docx"]
    )
    assert "[INVALID_INPUT]" in text
    assert "Nilai valid: .pdf, .docx." in text


def test_tool_error_accepts_plain_string_code():
    text = tool_error("SERVER_ERROR", "Kegagalan tak terduga.")
    assert text.startswith("❌ [SERVER_ERROR] ")


def test_pattern_matches_every_enum_member():
    for member in ToolErrorCode:
        assert ERROR_CODE_PATTERN.search(f"x [{member.value}] y")


def test_parse_tool_error_returns_none_for_plain_text():
    assert parse_tool_error("Semua berjalan normal.") is None


@pytest.mark.asyncio
async def test_prepare_submission_missing_file_is_not_found_error():
    result = await hebat_tools.hebat_prepare_submission_from_whatsapp_file.ainvoke(
        {
            "chat_id": "chat-test",
            "local_file_path": "/tmp/tidak-ada-9f3a.pdf",
            "assignment_query": "apa saja",
        }
    )
    parsed = parse_tool_error(result)
    assert parsed is not None
    assert parsed[0] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_prepare_submission_non_pdf_is_invalid_input_with_valid_values(
    tmp_path,
):
    file = tmp_path / "tugas.txt"
    file.write_text("bukan pdf")

    result = await hebat_tools.hebat_prepare_submission_from_whatsapp_file.ainvoke(
        {
            "chat_id": "chat-test",
            "local_file_path": str(file),
            "assignment_query": "apa saja",
        }
    )
    code, message = parse_tool_error(result)
    assert code == "INVALID_INPUT"
    assert ".pdf" in message


@pytest.mark.asyncio
async def test_upload_submission_unknown_token_is_not_found_error():
    from app.xninetzy.os.academic.hebat import storage

    result = await hebat_tools.hebat_upload_submission.ainvoke(
        {"chat_id": "chat-test", "confirmation_token": "HBT-TIDAKADA"}
    )
    assert storage.get_submission_by_token("HBT-TIDAKADA") is None
    code, _ = parse_tool_error(result)
    assert code == "NOT_FOUND"
