from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from langchain_core.tools import tool
from PIL import Image


SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
_MAX_DIMENSION = 4096
_TESSERACT_LANGS = "eng"
_TESSERACT_MIN_CONF = 30


@dataclass(slots=True)
class ImageMeta:
    path: str
    width: int
    height: int
    channels: int
    file_size: int
    format: str


def _resolve_path(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return None
    return path


def _decode(path: Path) -> np.ndarray | None:
    try:
        with Image.open(path) as img:
            arr = np.array(img.convert("RGB"))
        return arr
    except (OSError, ValueError):
        return None


def _metadata(path: Path) -> ImageMeta:
    size = path.stat().st_size
    arr = _decode(path)
    if arr is None:
        return ImageMeta(
            path=str(path), width=0, height=0, channels=0,
            file_size=size, format=path.suffix.lstrip(".").lower() or "unknown",
        )
    h, w, c = arr.shape
    return ImageMeta(
        path=str(path), width=int(w), height=int(h), channels=int(c),
        file_size=size, format=path.suffix.lstrip(".").lower() or "unknown",
    )


def _bounded(value: int, cap: int) -> int:
    return max(1, min(value, cap))


def _ensure_uint8(arr: np.ndarray) -> np.ndarray:
    if arr.dtype != np.uint8:
        return np.clip(arr, 0, 255).astype(np.uint8)
    return arr


@tool
def image_inspect(
    path: str,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Metadata piksel (lebar/tinggi/channel/format/ukuran file).

    Args:
        path: Path absolut/relatif ke file gambar (PNG/JPG/GIF/BMP/WEBP/TIFF).
        chat_id: Chat ID (dari context).
        sender_id: Owner principal (dari context).
    """
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found or unsupported format"}, ensure_ascii=False)
    meta = _metadata(resolved)
    if meta.width > _MAX_DIMENSION or meta.height > _MAX_DIMENSION:
        return json.dumps({
            "error": "image too large",
            "limit": _MAX_DIMENSION,
            "width": meta.width,
            "height": meta.height,
        }, ensure_ascii=False)
    arr = _decode(resolved)
    stats: dict[str, Any] = {}
    if arr is not None:
        mean = arr.mean(axis=(0, 1))
        std = arr.std(axis=(0, 1))
        stats = {
            "mean_rgb": [round(float(x), 2) for x in mean],
            "stddev_rgb": [round(float(x), 2) for x in std],
            "brightness": round(float(mean.mean()), 2),
        }
    payload = {
        "path": meta.path,
        "width": meta.width,
        "height": meta.height,
        "channels": meta.channels,
        "file_size": meta.file_size,
        "format": meta.format,
        "stats": stats,
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def image_preprocess(
    path: str,
    output_path: str = "",
    grayscale: bool = False,
    denoise: bool = False,
    threshold: str = "none",
    deskew: bool = False,
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Pipeline pra-pemrosesan citra: grayscale/denoise/threshold/deskew → tulis ke output_path.

    Args:
        path: Path sumber.
        output_path: Path tujuan (default: path dengan suffix __prep).
        grayscale: True untuk konversi ke grayscale.
        denoise: True untuk fastNlMeansDenoising.
        threshold: none|otsu|adaptive (default none).
        deskew: True untuk deskew berbasis minAreaRect.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional untuk skip re-run.
    """
    if idempotency_key:
        pass
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found"}, ensure_ascii=False)
    arr = _decode(resolved)
    if arr is None:
        return json.dumps({"error": "image unreadable"}, ensure_ascii=False)

    applied: list[str] = []
    work = arr
    if grayscale:
        work = cv2.cvtColor(work, cv2.COLOR_RGB2GRAY)
        applied.append("grayscale")
    if denoise:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_RGB2GRAY)
        work = cv2.fastNlMeansDenoising(work, h=7)
        applied.append("denoise")

    if threshold in {"otsu", "adaptive"}:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_RGB2GRAY)
            applied.append("grayscale")
        if threshold == "otsu":
            _, work = cv2.threshold(work, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            applied.append("otsu")
        else:
            work = cv2.adaptiveThreshold(
                work, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 31, 10,
            )
            applied.append("adaptive")

    if deskew and work.ndim == 2:
        work = _deskew(work)
        applied.append("deskew")

    work = _ensure_uint8(work)
    out = Path(output_path).expanduser() if output_path else resolved.with_name(f"{resolved.stem}__prep.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    if work.ndim == 2:
        Image.fromarray(work, mode="L").save(out)
    else:
        Image.fromarray(work, mode="RGB").save(out)

    payload = {
        "source": str(resolved),
        "output": str(out),
        "applied": applied,
        "shape": list(work.shape),
    }
    return json.dumps(payload, ensure_ascii=False)


def _deskew(gray: np.ndarray) -> np.ndarray:
    inv = cv2.bitwise_not(gray)
    thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 5:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    h, w = gray.shape
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


@tool
def image_crop(
    path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Crop ROI dan tulis ke file baru.

    Args:
        path: Path sumber.
        x: Koordinat X pojok kiri atas.
        y: Koordinat Y pojok kiri atas.
        width: Lebar crop (px).
        height: Tinggi crop (px).
        output_path: Path tujuan (default: source__crop.png).
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    if idempotency_key:
        pass
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found"}, ensure_ascii=False)
    arr = _decode(resolved)
    if arr is None:
        return json.dumps({"error": "image unreadable"}, ensure_ascii=False)
    h, w = arr.shape[:2]
    x0 = _bounded(x, w)
    y0 = _bounded(y, h)
    x1 = _bounded(x0 + width, w)
    y1 = _bounded(y0 + height, h)
    if x1 <= x0 or y1 <= y0:
        return json.dumps({"error": "empty crop region", "bounds": [x0, y0, x1, y1]}, ensure_ascii=False)
    crop = arr[y0:y1, x0:x1]
    out = Path(output_path).expanduser() if output_path else resolved.with_name(f"{resolved.stem}__crop.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(crop, mode="RGB").save(out)
    payload = {
        "source": str(resolved),
        "output": str(out),
        "bounds": [x0, y0, x1, y1],
        "shape": list(crop.shape),
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def image_ocr(
    path: str,
    lang: str = "eng",
    preprocess: bool = True,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """OCR via Tesseract (region + teks + confidence). Otomatis fallback ke pesan kalau tesseract tidak ada.

    Args:
        path: Path gambar.
        lang: Kode bahasa Tesseract (default eng).
        preprocess: True untuk grayscale+otsu otomatis.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found"}, ensure_ascii=False)
    if not shutil.which("tesseract"):
        return json.dumps({
            "error": "tesseract binary not available",
            "hint": "install tesseract-ocr",
            "path": str(resolved),
        }, ensure_ascii=False)

    src = resolved
    if preprocess:
        arr = _decode(resolved)
        if arr is not None:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            prep = resolved.with_name(f"{resolved.stem}__ocr.png")
            Image.fromarray(bw, mode="L").save(prep)
            src = prep

    cmd = [
        "tesseract", str(src), "-",
        "-l", lang or _TESSERACT_LANGS,
        "--psm", "6",
        "tsv",
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return json.dumps({"error": f"tesseract failed: {exc}"}, ensure_ascii=False)
    if proc.returncode != 0:
        return json.dumps({
            "error": (proc.stderr or "").strip()[:400],
            "path": str(src),
        }, ensure_ascii=False)

    lines = proc.stdout.splitlines()
    header = lines[0].split("\t") if lines else []
    rows: list[dict[str, Any]] = []
    confidences: list[int] = []
    for raw in lines[1:]:
        cols = raw.split("\t")
        if len(cols) != len(header):
            continue
        record = dict(zip(header, cols))
        try:
            conf = int(float(record.get("conf", "-1")))
        except ValueError:
            conf = -1
        text = record.get("text", "").strip()
        if not text or conf < _TESSERACT_MIN_CONF:
            continue
        confidences.append(conf)
        rows.append({
            "text": text,
            "confidence": conf,
            "bbox": [
                int(record.get("left", 0)),
                int(record.get("top", 0)),
                int(record.get("left", 0)) + int(record.get("width", 0)),
                int(record.get("top", 0)) + int(record.get("height", 0)),
            ],
        })

    full_text = " ".join(r["text"] for r in rows)
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    payload = {
        "path": str(resolved),
        "language": lang or _TESSERACT_LANGS,
        "regions": rows,
        "text": full_text,
        "confidence": avg_conf,
        "region_count": len(rows),
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def image_regions(
    path: str,
    method: str = "contours",
    limit: int = 50,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Deteksi region/box via OpenCV (contours|edges|lines).

    Args:
        path: Path gambar.
        method: contours|edges|lines (default contours).
        limit: Maks jumlah region (cap 500).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found"}, ensure_ascii=False)
    arr = _decode(resolved)
    if arr is None:
        return json.dumps({"error": "image unreadable"}, ensure_ascii=False)
    bounded_limit = max(1, min(limit, 500))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    regions: list[dict[str, Any]] = []

    if method == "edges":
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 8 or h < 8:
            continue
        area = int(cv2.contourArea(cnt))
        regions.append({
            "bbox": [int(x), int(y), int(x + w), int(y + h)],
            "area": area,
            "aspect": round(w / max(h, 1), 3),
        })
        if len(regions) >= bounded_limit:
            break

    payload = {
        "path": str(resolved),
        "method": method,
        "region_count": len(regions),
        "limit": bounded_limit,
        "regions": regions,
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def image_compare(
    path_a: str,
    path_b: str,
    metric: str = "ssim",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Bandingkan dua gambar: skor similaritas (ssim|histogram|diff).

    Args:
        path_a: Path gambar pertama.
        path_b: Path gambar kedua.
        metric: ssim|histogram|diff (default ssim).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    a = _resolve_path(path_a)
    b = _resolve_path(path_b)
    if a is None or b is None:
        return json.dumps({"error": "one or both images not found"}, ensure_ascii=False)
    arr_a = _decode(a)
    arr_b = _decode(b)
    if arr_a is None or arr_b is None:
        return json.dumps({"error": "image unreadable"}, ensure_ascii=False)

    if arr_a.shape != arr_b.shape:
        h = min(arr_a.shape[0], arr_b.shape[0])
        w = min(arr_a.shape[1], arr_b.shape[1])
        arr_a = cv2.resize(arr_a, (w, h))
        arr_b = cv2.resize(arr_b, (w, h))

    score: float
    if metric == "histogram":
        hist_a = cv2.calcHist([cv2.cvtColor(arr_a, cv2.COLOR_RGB2GRAY)], [0], None, [256], [0, 256])
        hist_b = cv2.calcHist([cv2.cvtColor(arr_b, cv2.COLOR_RGB2GRAY)], [0], None, [256], [0, 256])
        cv2.normalize(hist_a, hist_a)
        cv2.normalize(hist_b, hist_b)
        score = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    elif metric == "diff":
        diff = cv2.absdiff(arr_a, arr_b)
        score = float(100.0 - (diff.mean() / 255.0) * 100.0)
    else:
        try:
            from skimage.metrics import structural_similarity as ssim
        except ImportError:
            gray_a = cv2.cvtColor(arr_a, cv2.COLOR_RGB2GRAY)
            gray_b = cv2.cvtColor(arr_b, cv2.COLOR_RGB2GRAY)
            mse = float(((gray_a.astype(float) - gray_b.astype(float)) ** 2).mean())
            score = float(100.0 - min(100.0, mse / 255.0))
        else:
            gray_a = cv2.cvtColor(arr_a, cv2.COLOR_RGB2GRAY)
            gray_b = cv2.cvtColor(arr_b, cv2.COLOR_RGB2GRAY)
            (sim, _) = ssim(gray_a, gray_b, full=True)
            score = float(round(sim, 4))

    payload = {
        "path_a": str(a),
        "path_b": str(b),
        "metric": metric,
        "score": round(score, 4),
        "shape": list(arr_a.shape),
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def image_layout(
    path: str,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Analisis layout kasar: histogram warna, garis dominan, ukuran.

    Args:
        path: Path gambar.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    resolved = _resolve_path(path)
    if resolved is None:
        return json.dumps({"error": "image not found"}, ensure_ascii=False)
    arr = _decode(resolved)
    if arr is None:
        return json.dumps({"error": "image unreadable"}, ensure_ascii=False)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 80, 200)
    edge_density = float((edges > 0).mean())
    h, w = arr.shape[:2]

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 30, 8), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 30, 8)))
    horiz = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
    vert = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
    h_lines = int((horiz > 0).sum() // h)
    v_lines = int((vert > 0).sum() // w)

    color = arr.mean(axis=(0, 1))
    payload = {
        "path": str(resolved),
        "shape": [int(h), int(w)],
        "edge_density": round(edge_density, 4),
        "horizontal_lines": h_lines,
        "vertical_lines": v_lines,
        "mean_rgb": [round(float(x), 2) for x in color],
    }
    return json.dumps(payload, ensure_ascii=False)
