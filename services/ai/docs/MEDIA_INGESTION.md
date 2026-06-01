# Media → Document → Answer (WhatsApp)

Status: ✅ documents working · ❌ image OCR / audio transcript (next slices).

## Goal
User sends a file on WhatsApp (with a caption/question). The AI reads the file's
text and answers from it — and can optionally save it to the knowledge base.

## Flow
```
WhatsApp file (+ caption)
 -> wa-enggine caches message + can download via MCP `download_media_message`
 -> AI payload carries metadata.media {hasMedia, mediaType, filename, mimetype, messageId}
 -> agent sees [Media Attached] block in system prompt
 -> agent calls media_read_document(chat_id, message_id)
      -> MCP download_media_message -> local path
      -> parse_document() -> text
      -> record in media_items
 -> agent answers from the text
 -> (optional) media_ingest_to_knowledge -> FAISS knowledge source
```

## Files
- `app/media/document_parser.py` — `parse_document(path, mime_type, filename)` →
  `{text, char_count, kind, error}`. Supports pdf/txt/md/csv/json (always) and
  docx/xlsx/pptx (if the optional libs are installed; graceful error otherwise).
  PDF reuses `tools/hebat/pdf_reader.py` (pypdf).
- `app/media/media_store.py` — `save_media_item` / `get_media_item` (`media_items` table).
- `app/media/media_tools.py` — tools:
  - `media_read_document(chat_id, message_id)` — agent-facing read.
  - `media_info(metadata)` — show media metadata (`/media-info`).
  - `analyze_media(chat_id, metadata)` — parse + summarize (`/analyze-media`).
  - `media_ingest_to_knowledge(chat_id, message_id, title)` — save to FAISS.

## WhatsApp commands
- `/media-info` — info about the attached media.
- `/analyze-media` — parse + summarize the attached document (send the file with
  caption `/analyze-media`).
- Or just send a file with a question; the agent reads it automatically.

## Dependencies
- `pypdf` (already), stdlib for txt/md/csv/json.
- `python-docx`, `openpyxl`, `python-pptx` added to `pyproject.toml` (Docker).
  Locally optional — missing libs produce a clear "install X" message, not a crash.

## Limitations
- Quoted media (replying to someone else's file) is not forwarded by wa-enggine
  yet — only the file on the *current* message is read.
- Images and audio are not handled in this slice.
- `media_ingest_to_knowledge` ingests directly; for large/private files the agent
  is instructed (prompt) to request HITL approval first.

## Verify (terminal)
Unit/route tests:
```
DEEPSEEK_API_KEY=test SQLITE_PATH=/tmp/t.sqlite3 \
  uv run --with pytest --with pytest-asyncio python -m pytest -q -o asyncio_mode=auto \
  tests/test_media_document_parser.py tests/test_media_command_router.py
```
Real end-to-end (downloads a real PDF, parses, drives the tool) was validated
2026-06-02: parsed 9,362 chars from a 251 KB PDF and `media_read_document`
returned the content.
```
