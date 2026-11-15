from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from xninetzy.integrations.document_studio.errors import DocumentStudioError


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str = ""


@dataclass
class Block:
    kind: str
    level: int = 0
    runs: list[Run] = field(default_factory=list)
    items: list[tuple[int, bool, list[Run]]] = field(default_factory=list)
    header: list[list[Run]] = field(default_factory=list)
    rows: list[list[list[Run]]] = field(default_factory=list)
    align: list[str] = field(default_factory=list)
    text: str = ""
    path: str = ""
    caption: str = ""
    lang: str = ""

    @property
    def plain(self) -> str:
        return "".join(run.text for run in self.runs)


@dataclass
class Slide:
    blocks: list[Block]
    notes: str = ""
    layout: str = ""

    @property
    def title(self) -> str:
        for block in self.blocks:
            if block.kind == "heading":
                return block.plain
        return ""


INLINE = re.compile(
    r"(\*\*(?P<b>.+?)\*\*|__(?P<b2>.+?)__|`(?P<c>[^`]+)`|\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\)"
    r"|(?<![\w*])\*(?P<i>[^*\s][^*]*?)\*(?!\w)|(?<![\w_])_(?P<i2>[^_\s][^_]*?)_(?!\w))"
)
FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
LIST = re.compile(r"^(?P<indent>\s*)(?P<marker>[-*+]|\d+[.)])\s+(?P<text>.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
IMAGE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+\"(?P<title>[^\"]*)\")?\)\s*$")
DIRECTIVE = re.compile(r"^<!--\s*(?P<key>[a-z]+)\s*(?::\s*(?P<value>.*?))?\s*-->$")
CAPTION = re.compile(r"^(?:Table|Tabel)\s*:\s*(?P<text>.+)$", re.I)


def inline(text: str) -> list[Run]:
    runs: list[Run] = []
    pos = 0
    for match in INLINE.finditer(text):
        if match.start() > pos:
            runs.append(Run(text[pos:match.start()]))
        groups = match.groupdict()
        if groups["b"] or groups["b2"]:
            for inner in inline(groups["b"] or groups["b2"]):
                inner.bold = True
                runs.append(inner)
        elif groups["c"] is not None:
            runs.append(Run(groups["c"], code=True))
        elif groups["lt"]:
            runs.append(Run(groups["lt"], link=groups["lu"]))
        else:
            for inner in inline(groups["i"] or groups["i2"]):
                inner.italic = True
                runs.append(inner)
        pos = match.end()
    if pos < len(text):
        runs.append(Run(text[pos:]))
    return [run for run in runs if run.text]


def split_front_matter(source: str) -> tuple[dict, str]:
    text = source.replace("\r\n", "\n").lstrip("﻿")
    match = FRONT.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise DocumentStudioError(f"front matter is not valid YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise DocumentStudioError("front matter must be a YAML mapping")
    return meta, text[match.end():]


def _cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", body)]


def _alignment(line: str) -> list[str]:
    out = []
    for cell in _cells(line):
        if cell.startswith(":") and cell.endswith(":"):
            out.append("center")
        elif cell.endswith(":"):
            out.append("right")
        else:
            out.append("left")
    return out


def parse_blocks(body: str) -> list[Block]:
    lines = body.split("\n")
    blocks: list[Block] = []
    paragraph: list[str] = []
    pending_caption = ""
    i = 0

    def flush() -> None:
        if paragraph:
            blocks.append(Block("paragraph", runs=inline(" ".join(part.strip() for part in paragraph))))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush()
            i += 1
            continue
        if stripped.startswith("```"):
            flush()
            lang = stripped[3:].strip()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append(Block("code", text="\n".join(code), lang=lang))
            i += 1
            continue
        directive = DIRECTIVE.match(stripped)
        if directive:
            flush()
            blocks.append(Block("directive", text=directive.group("key"), caption=(directive.group("value") or "").strip()))
            i += 1
            continue
        if stripped in ("\\pagebreak", "\\newpage"):
            flush()
            blocks.append(Block("pagebreak"))
            i += 1
            continue
        if stripped == "|||":
            flush()
            blocks.append(Block("column"))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush()
            blocks.append(Block("rule"))
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", stripped)
        if heading:
            flush()
            blocks.append(Block("heading", level=len(heading.group(1)), runs=inline(heading.group(2))))
            i += 1
            continue
        caption = CAPTION.match(stripped)
        if caption:
            ahead = i + 1
            while ahead < len(lines) and not lines[ahead].strip():
                ahead += 1
            if ahead + 1 < len(lines) and "|" in lines[ahead] and TABLE_SEP.match(lines[ahead + 1]):
                flush()
                pending_caption = caption.group("text").strip()
                i = ahead
                continue
        if "|" in stripped and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            flush()
            header = [inline(cell) for cell in _cells(stripped)]
            align = _alignment(lines[i + 1])
            rows = []
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                cells = [inline(cell) for cell in _cells(lines[i])]
                cells += [[] for _ in range(len(header) - len(cells))]
                rows.append(cells[: len(header)])
                i += 1
            blocks.append(Block("table", header=header, rows=rows, align=align, caption=pending_caption))
            pending_caption = ""
            continue
        image = IMAGE.match(stripped)
        if image:
            flush()
            blocks.append(Block("image", path=image.group("src"), caption=(image.group("title") or image.group("alt") or "").strip()))
            i += 1
            continue
        if stripped.startswith(">"):
            flush()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(Block("quote", runs=inline(" ".join(quote))))
            continue
        item = LIST.match(line)
        if item:
            flush()
            items: list[tuple[int, bool, list[Run]]] = []
            while i < len(lines):
                current = LIST.match(lines[i])
                if current:
                    level = min(len(current.group("indent").replace("\t", "    ")) // 2, 3)
                    ordered = current.group("marker")[0].isdigit()
                    items.append((level, ordered, inline(current.group("text").strip())))
                    i += 1
                    continue
                if lines[i].strip() and lines[i].startswith("  ") and items:
                    level, ordered, runs = items[-1]
                    items[-1] = (level, ordered, runs + [Run(" ")] + inline(lines[i].strip()))
                    i += 1
                    continue
                break
            blocks.append(Block("list", items=items))
            continue
        paragraph.append(line)
        i += 1
    flush()
    return blocks


def _is_notes(block: Block) -> bool:
    return block.kind == "paragraph" and re.match(r"^(notes?|catatan)\s*:", block.plain, re.I) is not None


def to_slides(blocks: list[Block]) -> list[Slide]:
    explicit = any(block.kind == "rule" for block in blocks)
    groups: list[list[Block]] = [[]]
    for block in blocks:
        if explicit and block.kind == "rule":
            groups.append([])
            continue
        if not explicit and block.kind == "heading" and block.level <= 2 and groups[-1]:
            groups.append([])
        if block.kind in ("rule", "pagebreak"):
            continue
        groups[-1].append(block)
    slides: list[Slide] = []
    for group in groups:
        notes = []
        layout = ""
        content = []
        for block in group:
            if _is_notes(block):
                notes.append(re.sub(r"^(notes?|catatan)\s*:\s*", "", block.plain, flags=re.I))
            elif block.kind == "directive" and block.text == "layout":
                layout = block.caption.lower()
            elif block.kind == "directive" and block.text == "notes":
                notes.append(block.caption)
            elif block.kind != "directive":
                content.append(block)
        if content or notes:
            slides.append(Slide(blocks=content, notes="\n".join(notes), layout=layout))
    return slides


def document_blocks(blocks: list[Block]) -> list[Block]:
    out = []
    for block in blocks:
        if block.kind in ("column", "rule") or _is_notes(block):
            continue
        if block.kind == "directive":
            if block.text == "pagebreak":
                out.append(Block("pagebreak"))
            continue
        out.append(block)
    return out
