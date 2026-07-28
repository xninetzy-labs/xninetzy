"""OCR parser for WhatsApp images.

The parser intentionally extracts text instead of relying on a vision-capable
LLM so image text extraction stays deterministic and provider-independent.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
_MIME_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "image/bmp": ".bmp",
}


def _error(message: str) -> dict:
    return {
        "text": "",
        "char_count": 0,
        "kind": "image_ocr",
        "width": 0,
        "height": 0,
        "error": message,
    }


def _resolve_extension(path: Path, mime_type: str | None, filename: str | None) -> str:
    for candidate in (path.suffix, Path(filename or "").suffix):
        if candidate.lower() in SUPPORTED_IMAGE_EXTS:
            return candidate.lower()
    if mime_type:
        return _MIME_EXT.get(mime_type.split(";")[0].strip().lower(), "")
    return ""


def _run_ocr(image: Any, languages: str) -> str:
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - dependency is mandatory in Docker
        raise RuntimeError("Library pytesseract belum terinstall") from exc
    try:
        return pytesseract.image_to_string(image, lang=languages)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Binary Tesseract OCR belum terinstall") from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError(f"Tesseract OCR gagal: {exc}") from exc


def ocr_pil_image(image: Any) -> str:
    """Extract text from an already-open Pillow image."""
    from PIL import ImageOps

    settings = get_settings()
    prepared = ImageOps.exif_transpose(image)
    width, height = prepared.size
    pixels = width * height
    if pixels > settings.OCR_MAX_IMAGE_PIXELS:
        scale = math.sqrt(settings.OCR_MAX_IMAGE_PIXELS / pixels)
        target = (max(1, int(width * scale)), max(1, int(height * scale)))
        prepared = prepared.resize(target)
    if prepared.mode not in {"L", "RGB"}:
        prepared = prepared.convert("RGB")
    return (_run_ocr(prepared, settings.OCR_LANGUAGES) or "").strip()


def parse_image(
    path: str,
    mime_type: str | None = None,
    filename: str | None = None,
) -> dict:
    """Return OCR text and image metadata for a supported image file."""
    settings = get_settings()
    if not settings.OCR_ENABLED:
        return _error("OCR image dinonaktifkan.")

    source = Path(path)
    if not source.exists() or not source.is_file():
        return _error(f"File tidak ditemukan: {filename or source.name}")
    if not _resolve_extension(source, mime_type, filename):
        return _error(
            f"Tipe image belum didukung (mime={mime_type}, name={filename or source.name})"
        )

    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(source) as image:
            width, height = image.size
            text = ocr_pil_image(image)
    except UnidentifiedImageError:
        return _error("File image rusak atau formatnya tidak dikenali.")
    except Exception as exc:  # pragma: no cover - defensive around native OCR
        logger.warning("Image OCR failed for %s: %s", source.name, exc)
        return _error(f"Gagal membaca image: {exc}")

    if not text:
        result = _error(
            "Image berhasil dibuka, tetapi OCR tidak menemukan teks. "
            "Deskripsi visual non-teks membutuhkan model vision."
        )
        result.update({"width": width, "height": height})
        return result
    return {
        "text": text,
        "char_count": len(text),
        "kind": "image_ocr",
        "width": width,
        "height": height,
        "error": None,
    }
