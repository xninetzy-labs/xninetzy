from __future__ import annotations

import base64
import binascii
import hashlib
import re
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.interfaces.media.document_parser import parse_document
from app.xninetzy.interfaces.media.image_parser import parse_image
from app.xninetzy.interfaces.media.media_store import save_media_item
from app.xninetzy.interfaces.whatsapp.client import (
    WaToolError,
    download_media_message,
    get_media_content,
)

logger = logging.getLogger(__name__)

_PREVIEW_CHARS = 4000
_PROMPT_MEDIA_CHARS = 12000


def _safe_segment(value: str | None, fallback: str) -> str:
    segment = re.sub(r"[^a-zA-Z0-9_.-]", "_", value or "").strip("._")
    return segment[:160] or fallback


def _media_cache_root() -> Path:
    preferred = Path(get_settings().DATA_DIR).expanduser() / "wa-media-cache"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "xninetzy-wa-media-cache"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _materialize_media_content(chat_id: str, message_id: str, payload: dict) -> dict:
    encoded = payload.get("content_base64")
    if not isinstance(encoded, str) or not encoded:
        raise WaToolError("WA MCP tidak mengembalikan konten media.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise WaToolError("Konten media dari WA MCP bukan base64 yang valid.") from exc

    max_bytes = get_settings().WA_MEDIA_MAX_BYTES
    if len(raw) > max_bytes:
        raise WaToolError(f"Media melebihi batas {max_bytes} byte.")
    declared_size = payload.get("size_bytes")
    if declared_size is not None and int(declared_size) != len(raw):
        raise WaToolError("Ukuran konten media tidak cocok dengan metadata WA.")
    expected_hash = str(payload.get("sha256") or "").lower()
    actual_hash = hashlib.sha256(raw).hexdigest()
    if expected_hash and expected_hash != actual_hash:
        raise WaToolError("Checksum konten media dari WA tidak cocok.")

    folder = (
        _media_cache_root()
        / _safe_segment(chat_id, "chat")
        / _safe_segment(message_id, "message")
    )
    folder.mkdir(parents=True, exist_ok=True)
    filename = _safe_segment(payload.get("filename"), f"{actual_hash[:16]}.bin")
    target = folder / filename
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(target)
    result = {key: value for key, value in payload.items() if key != "content_base64"}
    result["local_path"] = str(target)
    result["size_bytes"] = len(raw)
    result["sha256"] = actual_hash
    return result


def _effective_media(metadata: dict | None) -> dict:
    data = metadata or {}
    media = data.get("media") or {}
    if media.get("hasMedia"):
        return media
    quoted = data.get("quotedMedia") or {}
    return quoted if quoted.get("hasMedia") else {}


async def _download_media(chat_id: str, message_id: str) -> dict:
    """Ask wa-enggine (MCP) to download the media and return its local metadata."""
    dl = await download_media_message(chat_id, message_id)
    if not dl.get("ok"):
        raise WaToolError(
            dl.get("error")
            or "Media tidak bisa diunduh (mungkin sudah kedaluwarsa di cache WA)."
        )
    local_path = dl.get("local_path")
    if local_path and Path(local_path).is_file():
        return dl

    content = await get_media_content(chat_id, message_id)
    if not content.get("ok"):
        reason = content.get("error") or "konten media tidak tersedia"
        raise WaToolError(
            "Media ditemukan di WA, tetapi file tidak dapat diakses oleh service AI: "
            f"{reason}"
        )
    return _materialize_media_content(chat_id, message_id, content)


async def _read_document(chat_id: str, message_id: str) -> dict:
    """Download + parse a document message. Returns parse_document() result + meta."""
    dl = await _download_media(chat_id, message_id)
    parsed = parse_document(
        dl["local_path"], mime_type=dl.get("mime_type"), filename=dl.get("filename")
    )
    parsed["_meta"] = dl
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="document",
                mime_type=dl.get("mime_type"),
                file_name=dl.get("filename"),
                local_path=dl["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


async def _read_image(chat_id: str, message_id: str) -> dict:
    """Download an image and extract text through deterministic OCR."""
    downloaded = await _download_media(chat_id, message_id)
    parsed = parse_image(
        downloaded["local_path"],
        mime_type=downloaded.get("mime_type"),
        filename=downloaded.get("filename"),
    )
    parsed["_meta"] = downloaded
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="image",
                mime_type=downloaded.get("mime_type"),
                file_name=downloaded.get("filename"),
                local_path=downloaded["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


async def _read_audio(chat_id: str, message_id: str) -> dict:
    """Download an audio message and transcribe it to text."""
    downloaded = await _download_media(chat_id, message_id)
    from app.xninetzy.interfaces.media.audio_transcriber import transcribe_audio

    parsed = await transcribe_audio(
        downloaded["local_path"],
        mime_type=downloaded.get("mime_type"),
        filename=downloaded.get("filename"),
    )
    parsed["_meta"] = downloaded
    if not parsed.get("error"):
        try:
            save_media_item(
                chat_id=chat_id,
                message_id=message_id,
                sender_id=None,
                media_type="audio",
                mime_type=downloaded.get("mime_type"),
                file_name=downloaded.get("filename"),
                local_path=downloaded["local_path"],
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
    except WaToolError as exc:
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
    """Baca isi dokumen (pdf/docx/txt/md/csv/json/xlsx/pptx) yang dikirim user di WhatsApp.

    Panggil ini SEBELUM menjawab kalau user mengirim file dan bertanya tentang isinya.
    Gunakan chat_id dari konteks dan message_id dari media yang dikirim.

    Args:
        chat_id: Chat WhatsApp (dari context).
        message_id: ID pesan yang berisi file (dari media context).
        max_chars: Batas panjang teks yang dikembalikan.
    """
    try:
        parsed = await _read_document(chat_id, message_id)
    except WaToolError as exc:
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
    """Baca teks pada image/screenshot WhatsApp menggunakan OCR.

    Args:
        chat_id: Chat WhatsApp dari context.
        message_id: ID pesan image dari media context.
        max_chars: Batas panjang hasil OCR.
    """
    try:
        parsed = await _read_image(chat_id, message_id)
    except WaToolError as exc:
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
    """Baca transkripsi audio/voice note WhatsApp.

    Panggil ini SEBELUM menjawab kalau user mengirim audio dan bertanya
    tentang isinya. Gunakan chat_id dari konteks dan message_id dari media.

    Args:
        chat_id: Chat WhatsApp dari context.
        message_id: ID pesan audio dari media context.
        max_chars: Batas panjang teks yang dikembalikan.
    """
    try:
        parsed = await _read_audio(chat_id, message_id)
    except WaToolError as exc:
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
    except WaToolError as exc:
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
    """Simpan isi dokumen WhatsApp ke knowledge base (FAISS).

    Catatan: untuk file besar/privat, minta approval admin dulu via HITL.

    Args:
        chat_id: Chat WhatsApp (dari context).
        message_id: ID pesan berisi file.
        title: Judul sumber (default: nama file).
    """
    try:
        parsed = await _read_document(chat_id, message_id)
    except WaToolError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    from app.xninetzy.os.knowledge.ingestion import ingest_text

    source_title = title or parsed["_meta"].get("filename") or "Dokumen WhatsApp"
    result = ingest_text(source_title, parsed["text"], source_type="whatsapp_document")
    if result.get("status") == "already_exists":
        return f"ℹ️ *{source_title}* sudah ada di knowledge base."
    return (
        f"✅ Disimpan ke knowledge:\n*{source_title}*\n"
        f"{result.get('chunks', 0)} chunk | ID: `{result.get('source_id', '?')}`"
    )
