from __future__ import annotations

import math
from pathlib import Path

from xninetzy.integrations.document_studio.errors import require


def render_previews(pdf: Path, out_dir: Path, max_pages: int = 12, scale: float = 1.0) -> dict:
    pdfium = require("pypdfium2")
    image_module = require("PIL.Image", extra="browser")
    draw_module = require("PIL.ImageDraw", extra="browser")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page-*.png"):
        old.unlink()
    document = pdfium.PdfDocument(str(pdf))
    total = len(document)
    pages: list[str] = []
    thumbs = []
    for index in range(min(total, max_pages)):
        bitmap = document[index].render(scale=scale)
        image = bitmap.to_pil().convert("RGB")
        path = out_dir / f"page-{index + 1:02d}.png"
        image.save(path)
        pages.append(str(path))
        thumb = image.copy()
        thumb.thumbnail((360, 360))
        thumbs.append(thumb)
    document.close()
    sheet_path = None
    if thumbs:
        cols = min(4, len(thumbs))
        rows = math.ceil(len(thumbs) / cols)
        cell_w = max(t.width for t in thumbs) + 20
        cell_h = max(t.height for t in thumbs) + 36
        sheet = image_module.new("RGB", (cols * cell_w + 20, rows * cell_h + 20), "#E9ECEF")
        draw = draw_module.Draw(sheet)
        for i, thumb in enumerate(thumbs):
            x = 20 + (i % cols) * cell_w
            y = 20 + (i // cols) * cell_h
            sheet.paste(thumb, (x, y))
            draw.rectangle([x - 1, y - 1, x + thumb.width, y + thumb.height], outline="#ADB5BD")
            draw.text((x, y + thumb.height + 6), f"{i + 1}", fill="#212529")
        sheet_path = out_dir / "contact-sheet.png"
        sheet.save(sheet_path)
    return {"page_count": total, "pages": pages, "contact_sheet": str(sheet_path) if sheet_path else None}
