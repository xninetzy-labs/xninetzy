from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.core.logging import logging
from app.xninetzy.interfaces.media.document_parser import parse_document
from app.xninetzy.interfaces.media.media_store import save_media_item
from app.xninetzy.interfaces.whatsapp.client import WaToolError, download_media_message

logger = logging.getLogger(__name__)

_PREVIEW_CHARS = 4000


async def _download_media(chat_id: str, message_id: str) -> dict:
    """Ask wa-enggine (MCP) to download the media and return its local metadata."""
    dl = await download_media_message(chat_id, message_id)
    if not dl.get("ok") or not dl.get("local_path"):
        raise WaToolError(dl.get("error") or "Media tidak bisa diunduh (mungkin sudah kedaluwarsa di cache WA).")
    return dl


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
                chat_id=chat_id, message_id=message_id, sender_id=None,
                media_type="document", mime_type=dl.get("mime_type"),
                file_name=dl.get("filename"), local_path=dl["local_path"],
                extracted_text=parsed["text"][:20000],
            )
        except Exception as exc:  # pragma: no cover - persistence is best-effort
            logger.warning("save_media_item failed: %s", exc)
    return parsed


@tool
async def media_read_document(chat_id: str, message_id: str, max_chars: int = _PREVIEW_CHARS) -> str:
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
def media_info(metadata: dict | None = None) -> str:
    """Tampilkan info media pada pesan saat ini tanpa mengunduh isinya."""
    media = (metadata or {}).get("media") or {}
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
    """Analisis media yang dikirim user di pesan ini (dokumen). Dipakai untuk /analyze-media."""
    media = (metadata or {}).get("media") or {}
    if not media.get("hasMedia"):
        return "Tidak ada media di pesan ini. Kirim file lalu beri caption `/analyze-media`."
    media_type = media.get("mediaType")
    message_id = media.get("messageId") or (metadata or {}).get("messageId")
    if not message_id:
        return "Media tidak punya message_id yang bisa dipakai untuk mengunduh."
    if media_type != "document":
        return (
            f"Slice ini baru mendukung *dokumen* (pdf/docx/txt/md/csv/xlsx/pptx). "
            f"Media `{media_type}` (gambar/audio) belum didukung."
        )
    try:
        parsed = await _read_document(chat_id, message_id)
    except WaToolError as exc:
        return f"⚠️ {exc}"
    if parsed.get("error"):
        return f"⚠️ {parsed['error']}"
    name = parsed["_meta"].get("filename") or "dokumen"
    preview = parsed["text"][:1500]
    return (
        f"*File Parsed*\n"
        f"Nama: {name}\n"
        f"Tipe: {parsed['kind']} | Panjang teks: {parsed['char_count']} char\n\n"
        f"*Cuplikan*\n{preview}"
        + ("\n\n_[teks dipotong]_" if parsed["char_count"] > 1500 else "")
        + "\n\nMau aku ringkas, jawab pertanyaan tentang isinya, atau simpan ke knowledge? "
        "Untuk simpan balas `ingest file`."
    )


@tool
async def media_ingest_to_knowledge(chat_id: str, message_id: str, title: str = "") -> str:
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
