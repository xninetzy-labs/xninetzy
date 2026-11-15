from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from xninetzy.integrations.document_studio.errors import require
from xninetzy.integrations.document_studio.markup import Block, Run
from xninetzy.integrations.document_studio.themes import Theme

LABELS = {
    "id": {"toc": "Daftar Isi", "table": "Tabel", "figure": "Gambar", "by": "Disusun oleh", "lecturer": "Dosen Pengampu"},
    "en": {"toc": "Contents", "table": "Table", "figure": "Figure", "by": "Prepared by", "lecturer": "Lecturer"},
}
PAGE_SIZES = {"A4": (21.0, 29.7), "Letter": (21.59, 27.94)}
BULLETS = ("•", "◦", "▪", "–")


@dataclass
class DocxReport:
    headings: list[tuple[int, str]] = field(default_factory=list)
    tables: int = 0
    images: int = 0
    warnings: list[str] = field(default_factory=list)


def _rgb(value: str):
    shared = require("docx.shared")
    return shared.RGBColor.from_string(value.lstrip("#"))


def _set_font(target, name: str) -> None:
    ns = require("docx.oxml.ns")
    oxml = require("docx.oxml")
    target.font.name = name
    rpr = target.element.get_or_add_rPr()
    fonts = rpr.find(ns.qn("w:rFonts"))
    if fonts is None:
        fonts = oxml.OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        fonts.attrib.pop(ns.qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(ns.qn(attr), name)


def _shade(element, fill: str) -> None:
    ns = require("docx.oxml.ns")
    oxml = require("docx.oxml")
    shd = oxml.OxmlElement("w:shd")
    shd.set(ns.qn("w:val"), "clear")
    shd.set(ns.qn("w:color"), "auto")
    shd.set(ns.qn("w:fill"), fill.lstrip("#"))
    element.append(shd)


def _field(paragraph, instruction: str) -> None:
    ns = require("docx.oxml.ns")
    oxml = require("docx.oxml")
    run = paragraph.add_run()
    for kind, text in (("begin", None), ("instr", instruction), ("separate", None), ("text", "1"), ("end", None)):
        if kind == "instr":
            node = oxml.OxmlElement("w:instrText")
            node.set(ns.qn("xml:space"), "preserve")
            node.text = text
        elif kind == "text":
            node = oxml.OxmlElement("w:t")
            node.text = text
        else:
            node = oxml.OxmlElement("w:fldChar")
            node.set(ns.qn("w:fldCharType"), kind)
        run._r.append(node)


def _hyperlink(paragraph, run: Run, theme: Theme) -> None:
    ns = require("docx.oxml.ns")
    oxml = require("docx.oxml")
    opc = require("docx.opc.constants")
    rid = paragraph.part.relate_to(run.link, opc.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = oxml.OxmlElement("w:hyperlink")
    link.set(ns.qn("r:id"), rid)
    node = oxml.OxmlElement("w:r")
    rpr = oxml.OxmlElement("w:rPr")
    color = oxml.OxmlElement("w:color")
    color.set(ns.qn("w:val"), theme.colors.accent.lstrip("#"))
    underline = oxml.OxmlElement("w:u")
    underline.set(ns.qn("w:val"), "single")
    rpr.append(color)
    rpr.append(underline)
    if run.bold:
        rpr.append(oxml.OxmlElement("w:b"))
    node.append(rpr)
    text = oxml.OxmlElement("w:t")
    text.set(ns.qn("xml:space"), "preserve")
    text.text = run.text
    node.append(text)
    link.append(node)
    paragraph._p.append(link)


def _runs(paragraph, runs: list[Run], theme: Theme, size: float | None = None) -> None:
    shared = require("docx.shared")
    for item in runs:
        if item.link.startswith(("http://", "https://", "mailto:")):
            _hyperlink(paragraph, item, theme)
            continue
        run = paragraph.add_run(item.text)
        run.bold = item.bold or None
        run.italic = item.italic or None
        if item.code:
            _set_font(run, theme.fonts.mono)
            run.font.size = shared.Pt((size or theme.sizes.body) - 1)
        elif size:
            run.font.size = shared.Pt(size)


def _style(document, theme: Theme) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    normal = document.styles["Normal"]
    _set_font(normal, theme.fonts.body)
    normal.font.size = shared.Pt(theme.sizes.body)
    normal.font.color.rgb = _rgb(theme.colors.text)
    fmt = normal.paragraph_format
    fmt.line_spacing = theme.document.line_spacing
    fmt.space_after = shared.Pt(theme.document.paragraph_after_pt)
    fmt.space_before = shared.Pt(0)
    for level, size in ((1, theme.sizes.h1), (2, theme.sizes.h2), (3, theme.sizes.h3), (4, theme.sizes.body), (5, theme.sizes.body), (6, theme.sizes.body)):
        style = document.styles[f"Heading {level}"]
        _set_font(style, theme.fonts.heading)
        style.font.size = shared.Pt(size)
        style.font.bold = True
        style.font.italic = level >= 4 or None
        style.font.color.rgb = _rgb(theme.colors.heading)
        style.paragraph_format.space_before = shared.Pt(18 if level == 1 else 12)
        style.paragraph_format.space_after = shared.Pt(6)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.line_spacing = 1.0
        style.paragraph_format.alignment = enum_text.WD_ALIGN_PARAGRAPH.LEFT
    for name, size in (("Title", theme.sizes.title), ("Subtitle", theme.sizes.subtitle)):
        style = document.styles[name]
        _set_font(style, theme.fonts.heading)
        style.font.size = shared.Pt(size)
        style.font.color.rgb = _rgb(theme.colors.heading if name == "Title" else theme.colors.muted)
        style.font.bold = name == "Title"
        style.font.italic = None


def _page(document, theme: Theme) -> None:
    shared = require("docx.shared")
    width, height = PAGE_SIZES[theme.page.size]
    for section in document.sections:
        section.page_width = shared.Cm(width)
        section.page_height = shared.Cm(height)
        section.top_margin = shared.Cm(theme.page.margin_top_cm)
        section.bottom_margin = shared.Cm(theme.page.margin_bottom_cm)
        section.left_margin = shared.Cm(theme.page.margin_left_cm)
        section.right_margin = shared.Cm(theme.page.margin_right_cm)


def text_width_cm(theme: Theme) -> float:
    return PAGE_SIZES[theme.page.size][0] - theme.page.margin_left_cm - theme.page.margin_right_cm


def _centered(document, text: str, size: float, theme: Theme, bold: bool = False, color: str | None = None, after: float = 6):
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    paragraph = document.add_paragraph()
    paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = shared.Pt(after)
    paragraph.paragraph_format.line_spacing = 1.15
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = shared.Pt(size)
    run.font.color.rgb = _rgb(color or theme.colors.text)
    _set_font(run, theme.fonts.heading)
    return paragraph


def _as_list(value) -> list[str]:
    if value is None or value == "":
        return []
    return [str(item) for item in value] if isinstance(value, (list, tuple)) else [str(value)]


def _cover(document, meta: dict, theme: Theme, base_dir: Path, report: DocxReport) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    labels = LABELS[theme.document.language]
    _centered(document, str(meta.get("title", "")).upper() if theme.document.language == "id" else str(meta.get("title", "")), theme.sizes.title, theme, bold=True, color=theme.colors.heading, after=10)
    if meta.get("subtitle"):
        _centered(document, str(meta["subtitle"]), theme.sizes.subtitle, theme, color=theme.colors.muted, after=24)
    logo = meta.get("logo")
    if logo:
        path = (base_dir / str(logo)).expanduser()
        if path.is_file():
            paragraph = document.add_paragraph()
            paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
            paragraph.add_run().add_picture(str(path), width=shared.Cm(4.5))
        else:
            report.warnings.append(f"cover logo not found: {logo}")
    authors = _as_list(meta.get("author") or meta.get("authors"))
    ids = _as_list(meta.get("student_id") or meta.get("nim"))
    if authors:
        _centered(document, f"{labels['by']}:", theme.sizes.body, theme, after=2)
        for index, author in enumerate(authors):
            line = f"{author} ({ids[index]})" if index < len(ids) else author
            _centered(document, line, theme.sizes.body, theme, bold=True, after=2)
    for key, prefix in (("course", ""), ("lecturer", labels["lecturer"] + ": ")):
        if meta.get(key):
            _centered(document, f"{prefix}{meta[key]}", theme.sizes.body, theme, after=2)
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = shared.Pt(48)
    for key in ("program", "faculty", "institution", "city"):
        if meta.get(key):
            _centered(document, str(meta[key]).upper() if theme.document.language == "id" else str(meta[key]), theme.sizes.body + 1, theme, bold=True, after=2)
    date = meta.get("date") or meta.get("year")
    if date:
        _centered(document, str(date), theme.sizes.body, theme, after=2)
    document.add_page_break()


def _toc(document, headings: list[tuple[int, str]], pages: dict[int, int] | None, theme: Theme) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    labels = LABELS[theme.document.language]
    title = document.add_paragraph(labels["toc"], style="Heading 1")
    title.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
    width = shared.Cm(text_width_cm(theme))
    for index, (level, text) in enumerate(headings):
        if level > 3:
            continue
        paragraph = document.add_paragraph()
        fmt = paragraph.paragraph_format
        fmt.left_indent = shared.Cm(0.6 * (level - 1))
        fmt.space_after = shared.Pt(2)
        fmt.line_spacing = 1.15
        fmt.tab_stops.add_tab_stop(width, enum_text.WD_TAB_ALIGNMENT.RIGHT, enum_text.WD_TAB_LEADER.DOTS)
        number = str(pages.get(index, "")) if pages else ""
        run = paragraph.add_run(f"{text}\t{number}")
        run.bold = level == 1 or None
    document.add_page_break()


def _footer(document, theme: Theme, cover: bool) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    section = document.sections[0]
    section.different_first_page_header_footer = cover
    if theme.document.page_numbers or theme.document.footer_text:
        paragraph = section.footer.paragraphs[0]
        paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
        if theme.document.footer_text:
            run = paragraph.add_run(theme.document.footer_text + ("   " if theme.document.page_numbers else ""))
            run.font.size = shared.Pt(theme.sizes.small)
        if theme.document.page_numbers:
            _field(paragraph, "PAGE")
    if theme.document.header_text:
        header = section.header.paragraphs[0]
        header.alignment = enum_text.WD_ALIGN_PARAGRAPH.RIGHT
        run = header.add_run(theme.document.header_text)
        run.font.size = shared.Pt(theme.sizes.small)
        run.font.color.rgb = _rgb(theme.colors.muted)


def _numbered(counters: list[int], level: int) -> str:
    counters[level - 1] += 1
    for deeper in range(level, len(counters)):
        counters[deeper] = 0
    return ".".join(str(value) for value in counters[:level] if value) + "."


def _list(document, block: Block, theme: Theme) -> None:
    shared = require("docx.shared")
    counters = [0, 0, 0, 0]
    step = 0.63
    for level, ordered, runs in block.items:
        for deeper in range(level + 1, 4):
            counters[deeper] = 0
        if ordered:
            counters[level] += 1
            marker = f"{counters[level]}."
        else:
            marker = BULLETS[level % len(BULLETS)]
        paragraph = document.add_paragraph()
        fmt = paragraph.paragraph_format
        fmt.left_indent = shared.Cm(step * (level + 1))
        fmt.first_line_indent = shared.Cm(-step)
        fmt.space_after = shared.Pt(2)
        fmt.tab_stops.add_tab_stop(shared.Cm(step * (level + 1)))
        paragraph.add_run(f"{marker}\t")
        _runs(paragraph, runs, theme)


def _caption(document, text: str, theme: Theme, italic: bool = True):
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    paragraph = document.add_paragraph()
    paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = shared.Pt(8)
    paragraph.paragraph_format.keep_with_next = False
    run = paragraph.add_run(text)
    run.italic = italic
    run.font.size = shared.Pt(theme.sizes.small + 0.5)
    run.font.color.rgb = _rgb(theme.colors.muted)
    return paragraph


def _table(document, block: Block, theme: Theme, report: DocxReport) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    ns = require("docx.oxml.ns")
    oxml = require("docx.oxml")
    report.tables += 1
    labels = LABELS[theme.document.language]
    if block.caption:
        prefix = f"{labels['table']} {report.tables}. " if theme.document.caption_numbering else ""
        _caption(document, prefix + block.caption, theme, italic=False).paragraph_format.keep_with_next = True
    columns = max(len(block.header), 1)
    table = document.add_table(rows=1 + len(block.rows), cols=columns)
    try:
        table.style = document.styles["Table Grid"]
    except KeyError:
        report.warnings.append("template has no 'Table Grid' style; table borders use defaults")
    aligns = {"left": enum_text.WD_ALIGN_PARAGRAPH.LEFT, "center": enum_text.WD_ALIGN_PARAGRAPH.CENTER, "right": enum_text.WD_ALIGN_PARAGRAPH.RIGHT}
    for r, row in enumerate([block.header] + block.rows):
        for c in range(columns):
            cell = table.cell(r, c)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = shared.Pt(1)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.alignment = aligns.get(block.align[c] if c < len(block.align) else "left")
            runs = row[c] if c < len(row) else []
            if r == 0:
                for item in runs:
                    item.bold = True
            _runs(paragraph, runs, theme, size=theme.sizes.small + 0.5)
            if r == 0:
                for run in paragraph.runs:
                    run.font.color.rgb = _rgb(theme.colors.table_header_text)
                _shade(cell._tc.get_or_add_tcPr(), theme.colors.table_header_bg)
            elif r % 2 == 0:
                _shade(cell._tc.get_or_add_tcPr(), theme.colors.table_stripe)
    header_props = table.rows[0]._tr.get_or_add_trPr()
    repeat = oxml.OxmlElement("w:tblHeader")
    repeat.set(ns.qn("w:val"), "true")
    header_props.append(repeat)
    document.add_paragraph().paragraph_format.space_after = shared.Pt(2)


def _image(document, block: Block, theme: Theme, base_dir: Path, report: DocxReport) -> None:
    shared = require("docx.shared")
    enum_text = require("docx.enum.text")
    labels = LABELS[theme.document.language]
    path = Path(block.path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        report.warnings.append(f"image not found: {block.path}")
        document.add_paragraph(f"[image not found: {block.path}]")
        return
    report.images += 1
    paragraph = document.add_paragraph()
    paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = bool(block.caption)
    width = text_width_cm(theme)
    try:
        image_module = require("PIL.Image", extra="browser")
        with image_module.open(path) as image:
            ratio = image.height / max(image.width, 1)
        target = min(width, 16.0 / max(ratio, 0.01) * 0.9) if ratio > 1.1 else width
    except Exception:
        target = width
    paragraph.add_run().add_picture(str(path), width=shared.Cm(min(target, width)))
    if block.caption:
        prefix = f"{labels['figure']} {report.images}. " if theme.document.caption_numbering else ""
        _caption(document, prefix + block.caption, theme)


def _code(document, block: Block, theme: Theme) -> None:
    shared = require("docx.shared")
    paragraph = document.add_paragraph()
    fmt = paragraph.paragraph_format
    fmt.line_spacing = 1.0
    fmt.space_after = shared.Pt(8)
    fmt.left_indent = shared.Cm(0.3)
    _shade(paragraph._p.get_or_add_pPr(), "#F4F5F7")
    for index, line in enumerate(block.text.split("\n")):
        run = paragraph.add_run(line)
        _set_font(run, theme.fonts.mono)
        run.font.size = shared.Pt(theme.sizes.small)
        if index < block.text.count("\n"):
            run.add_break()


def _quote(document, block: Block, theme: Theme) -> None:
    shared = require("docx.shared")
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = shared.Cm(1.0)
    paragraph.paragraph_format.right_indent = shared.Cm(1.0)
    _runs(paragraph, block.runs, theme)
    for run in paragraph.runs:
        run.italic = True
        run.font.color.rgb = _rgb(theme.colors.muted)


def render_docx(
    blocks: list[Block],
    meta: dict,
    theme: Theme,
    output: Path,
    *,
    base_dir: Path,
    template: Path | None = None,
    toc_pages: dict[int, int] | None = None,
) -> DocxReport:
    docx = require("docx")
    enum_text = require("docx.enum.text")
    report = DocxReport()
    document = docx.Document(str(template)) if template else docx.Document()
    if template:
        body = document.element.body
        for child in list(body):
            if not child.tag.endswith("sectPr"):
                body.remove(child)
    else:
        _page(document, theme)
    _style(document, theme)
    report.headings = [(block.level, block.plain) for block in blocks if block.kind == "heading"]
    cover = bool(theme.document.cover and meta.get("title") and meta.get("cover", True))
    if cover:
        _cover(document, meta, theme, base_dir, report)
    elif meta.get("title"):
        document.add_paragraph(str(meta["title"]), style="Title")
        if meta.get("subtitle"):
            document.add_paragraph(str(meta["subtitle"]), style="Subtitle")
    if theme.document.toc and meta.get("toc", True) and report.headings:
        _toc(document, report.headings, toc_pages, theme)
    counters = [0, 0, 0, 0, 0, 0]
    for block in blocks:
        if block.kind == "heading":
            text = block.plain
            if theme.document.heading_numbering and block.level <= 3:
                text = f"{_numbered(counters, block.level)} {text}"
            document.add_paragraph(text, style=f"Heading {min(block.level, 6)}")
        elif block.kind == "paragraph":
            paragraph = document.add_paragraph()
            if theme.document.justify:
                paragraph.alignment = enum_text.WD_ALIGN_PARAGRAPH.JUSTIFY
            _runs(paragraph, block.runs, theme)
        elif block.kind == "list":
            _list(document, block, theme)
        elif block.kind == "table":
            _table(document, block, theme, report)
        elif block.kind == "image":
            _image(document, block, theme, base_dir, report)
        elif block.kind == "code":
            _code(document, block, theme)
        elif block.kind == "quote":
            _quote(document, block, theme)
        elif block.kind == "pagebreak":
            document.add_page_break()
    _footer(document, theme, cover)
    core = document.core_properties
    core.title = str(meta.get("title", ""))
    core.author = ", ".join(_as_list(meta.get("author") or meta.get("authors")))
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output))
    return report
