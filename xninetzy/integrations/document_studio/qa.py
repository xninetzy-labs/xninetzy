from __future__ import annotations

import re
from pathlib import Path

from xninetzy.integrations.document_studio.errors import DocumentStudioError, require

LEFTOVER = re.compile(r"(\*\*[^*]+\*\*|\]\([^)]+\)|^\s*#{1,6}\s|\|\s*-{3,}|```)", re.M)


def _finding(level: str, message: str) -> dict:
    return {"level": level, "message": message}


def check_docx(path: Path) -> dict:
    docx = require("docx")
    document = docx.Document(str(path))
    findings = []
    last = 0
    headings = 0
    for paragraph in document.paragraphs:
        name = paragraph.style.name if paragraph.style is not None else ""
        if name.startswith("Heading "):
            headings += 1
            level = int(name.split()[-1]) if name.split()[-1].isdigit() else 1
            if level > last + 1 and last:
                findings.append(_finding("warning", f"heading level jumps from H{last} to H{level}: {paragraph.text[:60]!r}"))
            last = level
            if not paragraph.text.strip():
                findings.append(_finding("error", "empty heading"))
        if LEFTOVER.search(paragraph.text):
            findings.append(_finding("warning", f"unrendered Markdown: {paragraph.text[:60]!r}"))
    return {"format": "docx", "paragraphs": len(document.paragraphs), "headings": headings,
            "tables": len(document.tables), "images": len(document.inline_shapes), "findings": findings}


def check_pptx(path: Path) -> dict:
    pptx = require("pptx")
    prs = pptx.Presentation(str(path))
    findings = []
    width, height = prs.slide_width, prs.slide_height
    for number, slide in enumerate(prs.slides, 1):
        texts = 0
        for shape in slide.shapes:
            if shape.left is not None and (shape.left < 0 or shape.top < 0 or shape.left + shape.width > width * 1.01 or shape.top + shape.height > height * 1.01):
                findings.append(_finding("warning", f"slide {number}: shape '{shape.name}' extends past the slide edge"))
            if shape.has_text_frame and shape.text_frame.text.strip():
                texts += 1
                if LEFTOVER.search(shape.text_frame.text):
                    findings.append(_finding("warning", f"slide {number}: unrendered Markdown"))
        if not texts and not any(shape.shape_type == 13 for shape in slide.shapes):
            findings.append(_finding("warning", f"slide {number} has no text or picture"))
    return {"format": "pptx", "slides": len(prs.slides), "findings": findings}


def check_pdf(path: Path, expected_fonts: list[str]) -> dict:
    from xninetzy.integrations.document_studio.convert import pdf_fonts, pdf_pages_text

    pages = pdf_pages_text(path)
    fonts = pdf_fonts(path)
    findings = []
    normalized = [re.sub(r"[^a-z]", "", font.lower()) for font in fonts]
    for expected in dict.fromkeys(expected_fonts):
        key = re.sub(r"[^a-z]", "", expected.lower())
        if key and not any(key in font for font in normalized):
            findings.append(_finding("info", f"font {expected!r} was substituted in the PDF (embedded: {', '.join(fonts[:6])})"))
    blank = [i + 1 for i, text in enumerate(pages) if not text.strip()]
    if blank and len(blank) < len(pages):
        findings.append(_finding("info", f"pages without extractable text: {blank[:10]}"))
    return {"format": "pdf", "pages": len(pages), "fonts": fonts, "findings": findings}


def check(path: Path, expected_fonts: list[str] | None = None) -> dict:
    suffix = path.suffix.lower()
    if not path.is_file():
        raise DocumentStudioError(f"file not found: {path}")
    if suffix in (".docx", ".dotx"):
        report = check_docx(path)
    elif suffix in (".pptx", ".potx"):
        report = check_pptx(path)
    elif suffix == ".pdf":
        report = check_pdf(path, expected_fonts or [])
    else:
        raise DocumentStudioError("validation supports .docx, .pptx and .pdf")
    levels = {finding["level"] for finding in report["findings"]}
    report["status"] = "error" if "error" in levels else "warning" if "warning" in levels else "ok"
    report["path"] = str(path)
    return report
