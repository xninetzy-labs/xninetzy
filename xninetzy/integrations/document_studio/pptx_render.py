from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from xninetzy.integrations.document_studio.errors import require
from xninetzy.integrations.document_studio.markup import Block, Run, Slide
from xninetzy.integrations.document_studio.theme_extract import blend
from xninetzy.integrations.document_studio.themes import Theme

CONTINUED = {"id": "lanjutan", "en": "cont."}
BULLETS = ("•", "–", "▪", "·")
MARGIN = 0.6


@dataclass
class DeckReport:
    slides: int = 0
    split_slides: int = 0
    shrunk_slides: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class Item:
    level: int
    bullet: bool
    runs: list[Run]
    ordered: bool = False

    @property
    def length(self) -> int:
        return sum(len(run.text) for run in self.runs)


def _u():
    return require("pptx.util")


def _rgb(value: str):
    return require("pptx.dml.color").RGBColor.from_string(value.lstrip("#"))


def _soft(theme: Theme) -> str:
    return blend(theme.colors.slide_text, theme.colors.slide_background, 0.35)


def _size(theme: Theme) -> tuple[float, float]:
    return (13.333, 7.5) if theme.deck.aspect == "16:9" else (10.0, 7.5)


def _items(blocks: list[Block]) -> list[Item]:
    items: list[Item] = []
    for block in blocks:
        if block.kind == "paragraph":
            items.append(Item(0, False, block.runs))
        elif block.kind == "heading":
            items.append(Item(0, False, [Run(run.text, bold=True, italic=run.italic, link=run.link) for run in block.runs]))
        elif block.kind == "list":
            items.extend(Item(level, True, runs, ordered) for level, ordered, runs in block.items)
        elif block.kind == "quote":
            items.append(Item(0, False, [Run(run.text, bold=run.bold, italic=True) for run in block.runs]))
    return items


def _fits(items: list[Item], font: float, width_in: float, height_in: float) -> bool:
    if not items:
        return True
    total = 0.0
    for item in items:
        usable = (width_in - 0.35 * (item.level + (1 if item.bullet else 0))) * 72
        per_line = max(int(usable / (font * 0.52)), 8)
        lines = max(math.ceil(item.length / per_line), 1)
        total += lines * font * 1.2 + font * 0.45
    return total <= height_in * 72


def _fit(items: list[Item], theme: Theme, width_in: float, height_in: float) -> tuple[float, list[list[Item]]]:
    size = theme.sizes.slide_body
    while size >= theme.sizes.slide_min:
        if _fits(items, size, width_in, height_in) and sum(1 for item in items if item.level == 0) <= theme.deck.max_bullets + 2:
            return size, [items]
        size -= 1
    chunks: list[list[Item]] = [[]]
    for item in items:
        candidate = chunks[-1] + [item]
        if chunks[-1] and (not _fits(candidate, theme.sizes.slide_min, width_in, height_in) or len(candidate) > theme.deck.max_bullets + 2):
            chunks.append([item])
        else:
            chunks[-1] = candidate
    return theme.sizes.slide_min, chunks


def _paragraph_bullet(paragraph, item: Item, font: float) -> None:
    oxml_ns = require("pptx.oxml.ns")
    ppr = paragraph._p.get_or_add_pPr()
    for child in list(ppr):
        if child.tag.endswith(("buNone", "buChar", "buAutoNum")):
            ppr.remove(child)
    indent = int(_u().Pt(font * (1.4 if item.ordered else 0.9)))
    if item.bullet:
        ppr.set("marL", str(indent * (item.level + 1)))
        ppr.set("indent", str(-indent))
        if item.ordered:
            node = ppr.makeelement(oxml_ns.qn("a:buAutoNum"), {"type": "arabicPeriod"})
        else:
            node = ppr.makeelement(oxml_ns.qn("a:buChar"), {"char": BULLETS[item.level % len(BULLETS)]})
    else:
        ppr.set("marL", "0")
        ppr.set("indent", "0")
        node = ppr.makeelement(oxml_ns.qn("a:buNone"), {})
    ppr.append(node)


def _write_runs(paragraph, runs: list[Run], theme: Theme, font: float, color: str, face: str, link_color: str | None = None) -> None:
    u = _u()
    for item in runs:
        run = paragraph.add_run()
        run.text = item.text
        run.font.size = u.Pt(font)
        run.font.bold = item.bold or None
        run.font.italic = item.italic or None
        run.font.name = theme.fonts.mono if item.code else face
        run.font.color.rgb = _rgb((link_color or theme.colors.accent) if item.link else color)
        if item.link and link_color:
            run.font.underline = True
        elif item.link.startswith(("http://", "https://", "mailto:")):
            run.hyperlink.address = item.link


def _textbox(slide, left, top, width, height, theme: Theme):
    u = _u()
    box = slide.shapes.add_textbox(u.Inches(left), u.Inches(top), u.Inches(width), u.Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, u.Inches(0.05))
    return box, frame


def _fill_items(frame, items: list[Item], theme: Theme, font: float) -> None:
    u = _u()
    first = True
    for item in items:
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        _paragraph_bullet(paragraph, item, font)
        paragraph.space_after = u.Pt(font * 0.45)
        paragraph.line_spacing = 1.05
        _write_runs(paragraph, item.runs, theme, font, theme.colors.slide_text, theme.deck_body_font)


def _rect(slide, left, top, width, height, color: str):
    u = _u()
    shapes = require("pptx.enum.shapes")
    shape = slide.shapes.add_shape(shapes.MSO_SHAPE.RECTANGLE, u.Inches(left), u.Inches(top), u.Inches(width), u.Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(color)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def _background(slide, color: str) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color)


def _title(slide, text: str, theme: Theme, width: float) -> None:
    u = _u()
    if theme.deck.accent_bar:
        _rect(slide, MARGIN - 0.25, 0.5, 0.09, 0.85, theme.colors.accent)
    _, frame = _textbox(slide, MARGIN, 0.38, width - 2 * MARGIN, 1.05, theme)
    anchor = require("pptx.enum.text")
    frame.vertical_anchor = anchor.MSO_ANCHOR.MIDDLE
    size = theme.sizes.slide_title if len(text) <= 60 else max(theme.sizes.slide_title - 6, 20)
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = text
    run.font.size = u.Pt(size)
    run.font.bold = True
    run.font.name = theme.deck_heading_font
    run.font.color.rgb = _rgb(theme.colors.slide_title)


def _footer(slide, number: int, theme: Theme, width: float, height: float, dark: bool = False) -> None:
    color = "#FFFFFF" if dark else _soft(theme)
    if theme.deck.slide_numbers:
        _, frame = _textbox(slide, width - MARGIN - 1.0, height - 0.45, 1.0, 0.3, theme)
        paragraph = frame.paragraphs[0]
        paragraph.alignment = require("pptx.enum.text").PP_ALIGN.RIGHT
        _write_runs(paragraph, [Run(str(number))], theme, 11, color, theme.deck_body_font)
    if theme.deck.footer_text:
        _, frame = _textbox(slide, MARGIN, height - 0.45, width / 2, 0.3, theme)
        _write_runs(frame.paragraphs[0], [Run(theme.deck.footer_text)], theme, 10, color, theme.deck_body_font)


def _notes(slide, text: str) -> None:
    if text:
        slide.notes_slide.notes_text_frame.text = text


def _title_slide(prs, layout, meta: dict, theme: Theme, width: float, height: float) -> None:
    u = _u()
    slide = prs.slides.add_slide(layout)
    _background(slide, theme.colors.slide_background)
    _rect(slide, 0, 0, 0.35, height, theme.colors.accent)
    _rect(slide, 0.35, height - 0.12, width - 0.35, 0.12, theme.colors.slide_title)
    _, frame = _textbox(slide, 1.0, height * 0.28, width - 2.0, 1.8, theme)
    frame.vertical_anchor = require("pptx.enum.text").MSO_ANCHOR.BOTTOM
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = str(meta.get("title", ""))
    run.font.size = u.Pt(min(theme.sizes.slide_title + 10, 44))
    run.font.bold = True
    run.font.name = theme.deck_heading_font
    run.font.color.rgb = _rgb(theme.colors.slide_title)
    lines = [str(meta["subtitle"])] if meta.get("subtitle") else []
    _, frame = _textbox(slide, 1.0, height * 0.28 + 1.9, width - 2.0, 1.8, theme)
    authors = meta.get("author") or meta.get("authors")
    if authors:
        lines.append(", ".join(authors) if isinstance(authors, list) else str(authors))
    for key in ("course", "institution", "date"):
        if meta.get(key):
            lines.append(str(meta[key]))
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        lead = index == 0 and bool(meta.get("subtitle"))
        paragraph.space_after = u.Pt(14 if lead else 4)
        _write_runs(paragraph, [Run(line)], theme, 20 if lead else 14, _soft(theme), theme.deck_body_font)


def _section_slide(prs, layout, slide_data: Slide, number: int, theme: Theme, width: float, height: float) -> None:
    u = _u()
    slide = prs.slides.add_slide(layout)
    _background(slide, theme.colors.slide_title)
    _rect(slide, MARGIN, height * 0.5 + 0.1, 1.2, 0.08, theme.colors.accent)
    _, frame = _textbox(slide, MARGIN, height * 0.25, width - 2 * MARGIN, height * 0.25, theme)
    frame.vertical_anchor = require("pptx.enum.text").MSO_ANCHOR.BOTTOM
    run = frame.paragraphs[0].add_run()
    run.text = slide_data.title
    run.font.size = u.Pt(min(theme.sizes.slide_title + 8, 40))
    run.font.bold = True
    run.font.name = theme.deck_heading_font
    run.font.color.rgb = _rgb("#FFFFFF")
    extra = [block for block in slide_data.blocks if block.kind == "paragraph"]
    if extra:
        _, frame = _textbox(slide, MARGIN, height * 0.5 + 0.35, width - 2 * MARGIN, 1.2, theme)
        _write_runs(frame.paragraphs[0], extra[0].runs, theme, 18, "#FFFFFF", theme.deck_body_font, link_color="#FFFFFF")
    _footer(slide, number, theme, width, height, dark=True)
    _notes(slide, slide_data.notes)


def _table_shape(slide, block: Block, rows: list, theme: Theme, left, top, width, height) -> None:
    u = _u()
    columns = max(len(block.header), 1)
    shape = slide.shapes.add_table(len(rows) + 1, columns, u.Inches(left), u.Inches(top), u.Inches(width), u.Inches(min(height, 0.42 * (len(rows) + 1))))
    table = shape.table
    font = 14 if len(rows) <= 6 and columns <= 4 else 12 if columns <= 6 else 10
    for r, row in enumerate([block.header] + rows):
        for c in range(columns):
            cell = table.cell(r, c)
            cell.margin_left = cell.margin_right = u.Inches(0.06)
            runs = row[c] if c < len(row) else []
            frame = cell.text_frame
            frame.word_wrap = True
            paragraph = frame.paragraphs[0]
            if r == 0:
                runs = [Run(run.text, bold=True, italic=run.italic) for run in runs]
            _write_runs(paragraph, runs, theme, font, theme.colors.table_header_text if r == 0 else theme.colors.text, theme.deck_body_font)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(theme.colors.table_header_bg if r == 0 else theme.colors.table_stripe if r % 2 == 0 else "#FFFFFF")


def _picture(slide, path: Path, left, top, width, height) -> None:
    u = _u()
    try:
        image_module = require("PIL.Image", extra="browser")
        with image_module.open(path) as image:
            ratio = image.width / max(image.height, 1)
    except Exception:
        ratio = 16 / 9
    w, h = width, width / ratio
    if h > height:
        h, w = height, height * ratio
    slide.shapes.add_picture(str(path), u.Inches(left + (width - w) / 2), u.Inches(top + (height - h) / 2), u.Inches(w), u.Inches(h))


def _content_slide(prs, layout, title: str, theme: Theme, width: float, height: float, number: int, notes: str):
    slide = prs.slides.add_slide(layout)
    _background(slide, theme.colors.slide_background)
    if title:
        _title(slide, title, theme, width)
    _footer(slide, number, theme, width, height)
    _notes(slide, notes)
    return slide


VISUALS = ("table", "image", "code")


def _split_visuals(slide: Slide) -> list[Slide]:
    title_block = next((block for block in slide.blocks if block.kind == "heading"), None)
    body = [block for block in slide.blocks if block is not title_block]
    if sum(1 for block in body if block.kind in VISUALS) <= 1:
        return [slide]
    parts: list[list[Block]] = [[]]
    for block in body:
        if block.kind in VISUALS and any(b.kind in VISUALS for b in parts[-1]):
            parts.append([])
        parts[-1].append(block)
    head = [title_block] if title_block else []
    return [Slide(blocks=head + part, notes=slide.notes if i == 0 else "", layout=slide.layout) for i, part in enumerate(parts)]


def _resolve(path: str, base_dir: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else base_dir / candidate


def _delete_slides(prs) -> None:
    ids = prs.slides._sldIdLst
    for slide_id in list(ids):
        prs.part.drop_rel(slide_id.rId)
        ids.remove(slide_id)


def _layout(prs, *names: str, fallback: int = 6):
    for layout in prs.slide_layouts:
        if layout.name.lower() in names:
            return layout
    layouts = list(prs.slide_layouts)
    return layouts[min(fallback, len(layouts) - 1)]


def render_pptx(
    slides: list[Slide],
    meta: dict,
    theme: Theme,
    output: Path,
    *,
    base_dir: Path,
    template: Path | None = None,
) -> DeckReport:
    pptx = require("pptx")
    u = _u()
    report = DeckReport()
    prs = pptx.Presentation(str(template)) if template else pptx.Presentation()
    if template:
        _delete_slides(prs)
        width, height = prs.slide_width / 914400, prs.slide_height / 914400
    else:
        width, height = _size(theme)
        prs.slide_width, prs.slide_height = u.Inches(width), u.Inches(height)
    blank = _layout(prs, "blank", "kosong")
    body_top, body_height = 1.65, height - 1.65 - 0.65
    body_width = width - 2 * MARGIN
    label = CONTINUED[theme.document.language]
    number = 0
    if meta.get("title"):
        _title_slide(prs, blank, meta, theme, width, height)
        number += 1
    expanded = [part for slide in slides for part in _split_visuals(slide)]
    for slide_data in expanded:
        kinds = {block.kind for block in slide_data.blocks}
        title = slide_data.title
        rest = [block for block in slide_data.blocks if not (block.kind == "heading" and block.plain == title)]
        rest_kinds = {block.kind for block in rest}
        layout = slide_data.layout or (
            "section" if kinds <= {"heading", "paragraph"} and len([b for b in rest if b.kind == "paragraph"]) <= 1 and sum(len(b.plain) for b in rest) <= 140 and any(b.kind == "heading" and b.level == 1 for b in slide_data.blocks)
            else "table" if "table" in rest_kinds
            else "image" if "image" in rest_kinds
            else "columns" if "column" in rest_kinds
            else "code" if "code" in rest_kinds
            else "content"
        )
        if layout == "section":
            number += 1
            _section_slide(prs, blank, slide_data, number, theme, width, height)
            continue
        if layout == "table":
            table = next(block for block in rest if block.kind == "table")
            intro = _items([block for block in rest if block.kind in ("paragraph", "list")])[:1]
            rows_per = theme.deck.max_table_rows
            chunks = [table.rows[i:i + rows_per] for i in range(0, max(len(table.rows), 1), rows_per)] or [[]]
            report.split_slides += len(chunks) - 1
            for index, rows in enumerate(chunks):
                number += 1
                heading = title if index == 0 else f"{title} ({label})"
                slide = _content_slide(prs, blank, heading, theme, width, height, number, slide_data.notes if index == 0 else "")
                top = body_top
                if intro and index == 0:
                    _, frame = _textbox(slide, MARGIN, body_top, body_width, 0.7, theme)
                    _fill_items(frame, intro, theme, max(theme.sizes.slide_min, theme.sizes.slide_body - 4))
                    top += 0.75
                _table_shape(slide, table, rows, theme, MARGIN, top, body_width, body_height - (top - body_top))
                if table.caption and index == 0:
                    _, frame = _textbox(slide, MARGIN, height - 0.95, body_width, 0.35, theme)
                    _write_runs(frame.paragraphs[0], [Run(table.caption, italic=True)], theme, 12, _soft(theme), theme.deck_body_font)
            continue
        if layout == "image":
            image = next(block for block in rest if block.kind == "image")
            path = _resolve(image.path, base_dir)
            items = _items([block for block in rest if block.kind != "image"])
            number += 1
            slide = _content_slide(prs, blank, title, theme, width, height, number, slide_data.notes)
            if not path.is_file():
                report.warnings.append(f"slide {number}: image not found: {image.path}")
                continue
            if items:
                text_width = body_width * 0.45
                size, chunks = _fit(items, theme, text_width, body_height)
                _, frame = _textbox(slide, MARGIN, body_top, text_width, body_height, theme)
                _fill_items(frame, chunks[0], theme, size)
                if len(chunks) > 1:
                    report.warnings.append(f"slide {number}: text beside image was truncated to fit; shorten it")
                _picture(slide, path, MARGIN + text_width + 0.3, body_top, body_width - text_width - 0.3, body_height - 0.4)
            else:
                _picture(slide, path, MARGIN, body_top, body_width, body_height - 0.45)
            if image.caption:
                _, frame = _textbox(slide, MARGIN, height - 0.95, body_width, 0.35, theme)
                frame.paragraphs[0].alignment = require("pptx.enum.text").PP_ALIGN.CENTER
                _write_runs(frame.paragraphs[0], [Run(image.caption, italic=True)], theme, 12, _soft(theme), theme.deck_body_font)
            continue
        if layout == "columns":
            index = next(i for i, block in enumerate(rest) if block.kind == "column")
            left_items, right_items = _items(rest[:index]), _items(rest[index + 1:])
            column_width = (body_width - 0.4) / 2
            size_left, left_chunks = _fit(left_items, theme, column_width, body_height)
            size_right, right_chunks = _fit(right_items, theme, column_width, body_height)
            size = min(size_left, size_right)
            if len(left_chunks) > 1 or len(right_chunks) > 1:
                report.warnings.append(f"slide {number + 1}: column text exceeds the slide; shorten it")
            number += 1
            slide = _content_slide(prs, blank, title, theme, width, height, number, slide_data.notes)
            for offset, chunks in ((0.0, left_chunks), (column_width + 0.4, right_chunks)):
                _, frame = _textbox(slide, MARGIN + offset, body_top, column_width, body_height, theme)
                _fill_items(frame, chunks[0], theme, size)
            continue
        if layout == "code":
            code = next(block for block in rest if block.kind == "code")
            after = _items([block for block in rest if block.kind != "code"])
            number += 1
            slide = _content_slide(prs, blank, title, theme, width, height, number, slide_data.notes)
            lines = code.text.split("\n")
            font = 16 if len(lines) <= 12 else 13 if len(lines) <= 18 else 11
            if len(lines) > 24:
                report.warnings.append(f"slide {number}: code block has {len(lines)} lines; only readable up to ~24")
            box_height = min(body_height * (0.7 if after else 1.0), len(lines) * font * 1.25 / 72 + 0.4)
            box = _rect(slide, MARGIN, body_top, body_width, box_height, "#F4F5F7")
            frame = box.text_frame
            frame.word_wrap = True
            frame.vertical_anchor = require("pptx.enum.text").MSO_ANCHOR.TOP
            frame.margin_left = frame.margin_top = u.Inches(0.2)
            for i, line in enumerate(lines):
                paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
                paragraph.alignment = require("pptx.enum.text").PP_ALIGN.LEFT
                _write_runs(paragraph, [Run(line or " ", code=True)], theme, font, theme.colors.text, theme.fonts.mono)
            if after:
                remaining = body_height - box_height - 0.25
                size, chunks = _fit(after, theme, body_width, remaining)
                _, text_frame = _textbox(slide, MARGIN, body_top + box_height + 0.25, body_width, remaining, theme)
                _fill_items(text_frame, chunks[0], theme, size)
                if len(chunks) > 1:
                    report.warnings.append(f"slide {number}: text under the code block was truncated; shorten it")
            continue
        items = _items(rest)
        size, chunks = _fit(items, theme, body_width, body_height)
        if size < theme.sizes.slide_body:
            report.shrunk_slides += 1
        report.split_slides += len(chunks) - 1
        for index, chunk in enumerate(chunks):
            number += 1
            heading = title if index == 0 or not title else f"{title} ({label})"
            slide = _content_slide(prs, blank, heading, theme, width, height, number, slide_data.notes if index == 0 else "")
            if chunk:
                _, frame = _textbox(slide, MARGIN, body_top, body_width, body_height, theme)
                _fill_items(frame, chunk, theme, size)
            if not title and not chunk:
                report.warnings.append(f"slide {number} is empty")
    report.slides = number
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    return report
