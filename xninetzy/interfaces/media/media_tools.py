from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from xninetzy.core.logging import logging
from xninetzy.interfaces.media.document_parser import parse_document
from xninetzy.interfaces.media.image_parser import parse_image
from xninetzy.interfaces.media.media_store import (
    get_media_item,
    save_media_item,
)

logger = logging.getLogger(__name__)

_PREVIEW_CHARS = 4000
_PROMPT_MEDIA_CHARS = 12000


class MediaUnavailableError(RuntimeError):
    """Raised when media_store does not have the requested media item.

    Replaces the legacy ``WaToolError`` raised when the WhatsApp MCP could not
    download media. With the MCP-only pivot the local file must already exist
    in :mod:`media_store` (populated by the MCP client that uploaded it).
    """


def _effective_media(metadata: dict | None) -> dict:
    data = metadata or {}
    media = data.get("media") or {}
    if media.get("hasMedia"):
        return media
    quoted = data.get("quotedMedia") or {}
    return quoted if quoted.get("hasMedia") else {}


def _resolve_local(chat_id: str, message_id: str) -> dict:
    """Resolve ``(chat_id, message_id)`` to a media_store row.

    Returns the stored metadata dict (including ``local_path`` and
    ``mime_type``) so callers can run the appropriate parser. Raises
    :class:`MediaUnavailableError` when the lookup misses — the MCP client is
    responsible for populating ``media_store`` before invoking these tools.
    """
    if not message_id:
        raise MediaUnavailableError(
            "Pesan tidak memiliki message_id; media tidak bisa ditemukan."
        )
    stored = get_media_item(message_id)
    if not stored or not stored.get("local_path"):
        raise MediaUnavailableError(
            f"Media untuk message_id={message_id} belum tersedia di media_store. "
            "Upload file via MCP dulu, lalu panggil ulang."
        )
    local = Path(stored["local_path"])
    if not local.is_file():
        raise MediaUnavailableError(
            f"File media {local} tidak ada di disk; minta upload ulang."
        )
    stored.setdefault("chat_id", chat_id)
    stored.setdefault("message_id", message_id)
    return stored


async def _read_document(chat_id: str, message_id: str) -> dict:
    """Parse a document already present in media_store.

    The pivot removed WhatsApp download: the MCP client uploads the file and
    populates ``media_store`` with a ``local_path``. This helper only reads.
    """
    stored = _resolve_local(chat_id, message_id)
    parsed = parse_document(
        stored["local_path"],
        mime_type=stored.get("mime_type"),
        filename=stored.get("file_name"),
    )
    parsed["_meta"] = stored
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="document",
                mime_type=stored.get("mime_type"),
                file_name=stored.get("file_name"),
                local_path=stored["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


async def _read_image(chat_id: str, message_id: str) -> dict:
    """Run OCR over an image already present in media_store."""
    stored = _resolve_local(chat_id, message_id)
    parsed = parse_image(
        stored["local_path"],
        mime_type=stored.get("mime_type"),
        filename=stored.get("file_name"),
    )
    parsed["_meta"] = stored
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="image",
                mime_type=stored.get("mime_type"),
                file_name=stored.get("file_name"),
                local_path=stored["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


async def _read_audio(chat_id: str, message_id: str) -> dict:
    """Transcribe an audio file already present in media_store."""
    stored = _resolve_local(chat_id, message_id)
    from xninetzy.interfaces.media.audio_transcriber import transcribe_audio

    parsed = await transcribe_audio(
        stored["local_path"],
        mime_type=stored.get("mime_type"),
        filename=stored.get("file_name"),
    )
    parsed["_meta"] = stored
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="audio",
                mime_type=stored.get("mime_type"),
                file_name=stored.get("file_name"),
                local_path=stored["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


async def build_media_prompt_context(
    chat_id: str, metadata: dict | None, max_chars: int = _PROMPT_MEDIA_CHARS
) -> str:
    """Extract attached/quoted media before the LLM runs."""
    media = _effective_media(metadata)
    if not media.get("hasMedia"):
        return ""
    media_type = media.get("mediaType")
    message_id = media.get("messageId") or (metadata or {}).get("messageId")
    filename = media.get("filename") or media_type or "media"
    if not message_id:
        return "\n[Media Extraction Error]\nMedia tidak memiliki message_id.\n"
    if media_type not in {"document", "image", "audio"}:
        return (
            "\n[Media Extraction]\n"
            f"Nama: {filename}\nTipe: {media_type or '-'}\n"
            "Video belum didukung. Hanya document, image, dan audio yang dapat dibaca.\n"
        )

    try:
        if media_type == "document":
            parsed = await _read_document(chat_id, message_id)
        elif media_type == "image":
            parsed = await _read_image(chat_id, message_id)
        else:
            parsed = await _read_audio(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"\n[Media Extraction Error]\nNama: {filename}\nError: {exc}\n"
    if parsed.get("error"):
        return (
            f"\n[Media Extraction Error]\nNama: {filename}\nError: {parsed['error']}\n"
        )

    text = str(parsed.get("text") or "")
    preview = text[:max_chars]
    truncated = len(text) > max_chars
    source = {
        "document": "document text",
        "image": "image OCR text",
        "audio": "audio transcription",
    }.get(media_type, "extracted text")
    return (
        "\n[Media Extracted]\n"
        f"Nama: {filename}\nTipe sumber: {source}\n"
        f"Panjang: {len(text)} karakter\n"
        "Jawab pertanyaan user berdasarkan isi hasil ekstraksi berikut. "
        "Jangan mengarang bagian yang tidak terbaca.\n"
        "---\n"
        f"{preview}"
        + ("\n...[hasil ekstraksi dipotong]" if truncated else "")
        + "\n---\n"
    )


@tool
async def media_read_document(
    chat_id: str, message_id: str, max_chars: int = _PREVIEW_CHARS
) -> str:
    """Baca isi dokumen (pdf/docx/txt/md/csv/json/xlsx/pptx) yang sudah ada di media_store.

    Panggil ini SEBELUM menjawab kalau user mengirim file dan bertanya tentang isinya.
    Gunakan chat_id dari konteks dan message_id dari media context.

    Args:
        chat_id: Chat identifier (dari context).
        message_id: ID pesan berisi file (lihat media_store).
        max_chars: Batas panjang teks yang dikembalikan.
    """
    try:
        parsed = await _read_document(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    text = parsed["text"]
    name = parsed["_meta"].get("filename") or "dokumen"
    head = text[:max_chars]
    suffix = "\n\n_[teks dipotong]_" if len(text) > max_chars else ""
    return f"*Isi {name}* ({parsed['kind']}, {parsed['char_count']} char)\n\n{head}{suffix}"


@tool
async def media_read_image(
    chat_id: str, message_id: str, max_chars: int = _PREVIEW_CHARS
) -> str:
    """Baca teks pada image/screenshot yang sudah ada di media_store (OCR).

    Args:
        chat_id: Chat identifier (dari context).
        message_id: ID pesan image (lihat media_store).
        max_chars: Batas panjang hasil OCR.
    """
    try:
        parsed = await _read_image(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    name = parsed["_meta"].get("filename") or "image"
    text = parsed["text"]
    preview = text[:max_chars]
    suffix = "\n\n_[teks OCR dipotong]_" if len(text) > max_chars else ""
    return (
        f"*Teks dari {name}* ({parsed['width']}x{parsed['height']}, "
        f"{parsed['char_count']} char)\n\n{preview}{suffix}"
    )


@tool
async def media_read_audio(
    chat_id: str, message_id: str, max_chars: int = _PREVIEW_CHARS
) -> str:
    """Baca transkripsi audio/voice note yang sudah ada di media_store.

    Panggil ini SEBELUM menjawab kalau user mengirim audio dan bertanya
    tentang isinya. Gunakan chat_id dari konteks dan message_id dari media.

    Args:
        chat_id: Chat identifier (dari context).
        message_id: ID pesan audio (lihat media_store).
        max_chars: Batas panjang teks yang dikembalikan.
    """
    try:
        parsed = await _read_audio(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    name = parsed["_meta"].get("filename") or "audio"
    text = parsed["text"]
    preview = text[:max_chars]
    suffix = "\n\n_[transkripsi dipotong]_" if len(text) > max_chars else ""
    return f"*Transkripsi {name}* ({parsed['char_count']} char)\n\n{preview}{suffix}"


@tool
def media_info(metadata: dict | None = None) -> str:
    """Tampilkan info media pada pesan saat ini tanpa mengunduh isinya."""
    media = _effective_media(metadata)
    if not media.get("hasMedia"):
        return "Tidak ada media di pesan ini."
    return (
        "*Media Info*\n"
        f"• Tipe: {media.get('mediaType') or '-'}\n"
        f"• Nama: {media.get('filename') or '-'}\n"
        f"• Mime: {media.get('mimetype') or '-'}\n"
        f"• Ukuran: {int(media.get('fileLength') or 0)} byte\n"
        f"• Caption: {media.get('caption') or '-'}"
    )


@tool
async def analyze_media(chat_id: str = "system", metadata: dict | None = None) -> str:
    """Analisis dokumen atau image yang dikirim/dikutip user."""
    media = _effective_media(metadata)
    if not media.get("hasMedia"):
        return "Tidak ada media di pesan ini. Kirim file lalu beri caption `/analyze-media`."
    media_type = media.get("mediaType")
    message_id = media.get("messageId") or (metadata or {}).get("messageId")
    if not message_id:
        return "Media tidak punya message_id yang bisa dipakai untuk mengunduh."
    if media_type not in {"document", "image", "audio"}:
        return (
            "Fitur ini mendukung dokumen, image OCR, dan transkripsi audio. "
            f"Media `{media_type}` belum didukung."
        )
    try:
        if media_type == "document":
            parsed = await _read_document(chat_id, message_id)
        elif media_type == "image":
            parsed = await _read_image(chat_id, message_id)
        else:
            parsed = await _read_audio(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    name = parsed["_meta"].get("filename") or media_type
    preview = parsed["text"][:1500]
    label = {
        "document": "File Parsed",
        "image": "Image OCR",
        "audio": "Audio Transcript",
    }.get(media_type, "Media Parsed")
    return (
        f"*{label}*\n"
        f"Nama: {name}\n"
        f"Tipe: {parsed['kind']} | Panjang teks: {parsed['char_count']} char\n\n"
        f"*Cuplikan*\n{preview}"
        + ("\n\n_[teks dipotong]_" if parsed["char_count"] > 1500 else "")
        + "\n\nMau aku ringkas, jawab pertanyaan tentang isinya, atau simpan ke knowledge? "
        "Untuk simpan balas `ingest file`."
    )


@tool
async def media_ingest_to_knowledge(
    chat_id: str, message_id: str, title: str = ""
) -> str:
    """Simpan isi dokumen yang sudah ada di media_store ke knowledge base (FAISS).

    Catatan: untuk file besar/privat, minta approval admin dulu via HITL.

    Args:
        chat_id: Chat identifier (dari context).
        message_id: ID pesan berisi file (lihat media_store).
        title: Judul sumber (default: nama file).
    """
    try:
        parsed = await _read_document(chat_id, message_id)
    except MediaUnavailableError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    from xninetzy.os.knowledge.ingestion import ingest_text

    source_title = title or parsed["_meta"].get("filename") or "Dokumen"
    result = ingest_text(source_title, parsed["text"], source_type="document")
    if result.get("status") == "already_exists":
        return f"ℹ️ *{source_title}* sudah ada di knowledge base."
    return (
        f"✅ Disimpan ke knowledge:\n*{source_title}*\n"
        f"{result.get('chunks', 0)} chunk | ID: `{result.get('source_id', '?')}`"
    )
