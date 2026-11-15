from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from xninetzy.core.config import expand_path, get_settings
from xninetzy.core.paths import resolve_artifact_output
from xninetzy.integrations.document_studio import convert, qa
from xninetzy.integrations.document_studio.docx_render import render_docx
from xninetzy.integrations.document_studio.errors import DocumentStudioError, MissingDependencyError
from xninetzy.integrations.document_studio.markup import document_blocks, parse_blocks, split_front_matter, to_slides
from xninetzy.integrations.document_studio.pptx_render import render_pptx
from xninetzy.integrations.document_studio.preview import render_previews
from xninetzy.integrations.document_studio.themes import Theme, load_theme

FORMATS = {"docx", "pdf", "pptx", "slides_pdf"}
SOURCE_SUFFIXES = {".md", ".markdown", ".txt"}
MAX_SOURCE_BYTES = 2_000_000


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "document"


def output_root(output_dir: str = "") -> Path:
    base = output_dir or expand_path(get_settings().GENERATED_DOCUMENTS_DIR)
    return resolve_artifact_output(base, create_parents=False)


def _source(markdown: str, source_path: str) -> tuple[str, Path]:
    if markdown.strip():
        return markdown, Path.cwd()
    if not source_path:
        raise DocumentStudioError("provide markdown text or source_path")
    path = Path(source_path).expanduser().resolve()
    if path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
        raise DocumentStudioError("source_path must be an existing .md, .markdown or .txt file")
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise DocumentStudioError("source file is larger than 2 MB")
    return path.read_text(encoding="utf-8"), path.parent


def _template(template_path: str, suffixes: tuple[str, ...]) -> Path | None:
    if not template_path:
        return None
    path = Path(template_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in suffixes:
        raise DocumentStudioError(f"template must be an existing {' or '.join(suffixes)} file")
    return path


def _key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()[:50]


def _heading_pages(pages: list[str], headings: list[tuple[int, str]], skip: int) -> dict[int, int]:
    normalized = [re.sub(r"\s+", " ", text).lower() for text in pages]
    listed = [(index, _key(text)) for index, (level, text) in enumerate(headings) if level <= 3 and _key(text)]
    if not listed:
        return {}
    toc_end = next((page for page in range(skip, len(normalized)) if listed[-1][1] in normalized[page]), skip)
    found: dict[int, int] = {}
    cursor = toc_end + 1
    for index, key in listed:
        for page in range(cursor, len(normalized)):
            if key in normalized[page]:
                found[index] = page + 1
                cursor = page
                break
    return found


def render(
    *,
    markdown: str = "",
    source_path: str = "",
    formats: list[str] | None = None,
    theme: str = "",
    output_name: str = "",
    output_dir: str = "",
    template_path: str = "",
    preview_pages: int = 8,
) -> dict:
    wanted = [item.lower() for item in (formats or ["docx", "pdf"])]
    unknown = sorted(set(wanted) - FORMATS)
    if unknown:
        raise DocumentStudioError(f"unsupported formats {unknown}; use {sorted(FORMATS)}")
    text, base_dir = _source(markdown, source_path)
    meta, body = split_front_matter(text)
    chosen: Theme = load_theme(theme or str(meta.get("theme", "")) or "professional")
    name = slugify(output_name or str(meta.get("title", "")) or (Path(source_path).stem if source_path else "document"))
    folder = resolve_artifact_output(output_root(output_dir) / name, create_parents=True)
    folder.mkdir(parents=True, exist_ok=True)
    blocks = parse_blocks(body)
    manifest: dict = {"status": "ok", "theme": chosen.name, "output_dir": str(folder), "files": {}, "qa": {}, "warnings": [], "previews": {}}
    fonts = [chosen.fonts.body, chosen.fonts.heading]
    if "docx" in wanted or "pdf" in wanted:
        docx_path = folder / f"{name}.docx"
        template = _template(template_path, (".docx", ".dotx")) if template_path.lower().endswith((".docx", ".dotx")) else None
        doc_blocks = document_blocks(blocks)
        report = render_docx(doc_blocks, meta, chosen, docx_path, base_dir=base_dir, template=template)
        manifest["warnings"] += report.warnings
        toc = chosen.document.toc and meta.get("toc", True) and report.headings
        pdf_path = None
        if "pdf" in wanted or toc:
            try:
                pdf_path = convert.to_pdf(docx_path, folder)
            except MissingDependencyError as exc:
                manifest["warnings"].append(str(exc))
        if toc and pdf_path:
            skip = 1 if chosen.document.cover and meta.get("title") else 0
            pages = _heading_pages(convert.pdf_pages_text(pdf_path), report.headings, skip)
            render_docx(doc_blocks, meta, chosen, docx_path, base_dir=base_dir, template=template, toc_pages=pages)
            pdf_path = convert.to_pdf(docx_path, folder)
            missing = sum(1 for level, _ in report.headings if level <= 3) - len(pages)
            if missing > 0:
                manifest["warnings"].append(f"{missing} table-of-contents entries have no page number (heading not found in PDF text)")
        elif toc:
            manifest["warnings"].append("table of contents has no page numbers because PDF conversion is unavailable")
        if "docx" in wanted:
            manifest["files"]["docx"] = str(docx_path)
            manifest["qa"]["docx"] = qa.check(docx_path)
        elif docx_path.exists():
            docx_path.unlink()
        if "pdf" in wanted and pdf_path:
            manifest["files"]["pdf"] = str(pdf_path)
            manifest["qa"]["pdf"] = qa.check(pdf_path, fonts)
            manifest["previews"]["pdf"] = render_previews(pdf_path, folder / "preview" / "document", preview_pages)
        elif pdf_path and pdf_path.exists() and "pdf" not in wanted:
            pdf_path.unlink()
    if "pptx" in wanted or "slides_pdf" in wanted:
        pptx_path = folder / f"{name}.pptx"
        template = _template(template_path, (".pptx", ".potx")) if template_path.lower().endswith((".pptx", ".potx")) else None
        report = render_pptx(to_slides(blocks), meta, chosen, pptx_path, base_dir=base_dir, template=template)
        manifest["warnings"] += report.warnings
        manifest["deck"] = {"slides": report.slides, "split_slides": report.split_slides, "shrunk_slides": report.shrunk_slides}
        manifest["files"]["pptx"] = str(pptx_path)
        manifest["qa"]["pptx"] = qa.check(pptx_path)
        if "slides_pdf" in wanted:
            try:
                slides_dir = folder / "slides"
                slides_pdf = convert.to_pdf(pptx_path, slides_dir)
                manifest["files"]["slides_pdf"] = str(slides_pdf)
                manifest["qa"]["slides_pdf"] = qa.check(slides_pdf, [chosen.deck_body_font, chosen.deck_heading_font])
                manifest["previews"]["slides"] = render_previews(slides_pdf, folder / "preview" / "slides", preview_pages)
            except MissingDependencyError as exc:
                manifest["warnings"].append(str(exc))
        if "pptx" not in wanted:
            pptx_path.unlink()
            manifest["files"].pop("pptx")
    statuses = {report.get("status") for report in manifest["qa"].values()}
    if "error" in statuses:
        manifest["status"] = "error"
    elif "warning" in statuses or manifest["warnings"]:
        manifest["status"] = "warning"
    manifest["source_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["next_step"] = "Open the contact sheet(s) in previews and inspect the pages before delivering."
    return manifest


def preview(path: str, max_pages: int = 12) -> dict:
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise DocumentStudioError(f"file not found: {target}")
    folder = resolve_artifact_output(target.parent / "preview" / target.stem, create_parents=True)
    pdf = target
    if target.suffix.lower() in (".docx", ".pptx"):
        pdf = convert.to_pdf(target, folder)
    elif target.suffix.lower() != ".pdf":
        raise DocumentStudioError("preview supports .pdf, .docx and .pptx")
    return render_previews(pdf, folder, max_pages)
