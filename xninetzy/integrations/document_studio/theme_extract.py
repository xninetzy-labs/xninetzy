from __future__ import annotations

import colorsys
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

from xninetzy.integrations.document_studio.errors import DocumentStudioError

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
SCHEME_KEYS = ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6")


def _rgb(hex_value: str) -> tuple[float, float, float]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)


def luminance(hex_value: str) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in _rgb(hex_value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def blend(a: str, b: str, weight: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x * (1 - weight) + y * weight for x, y in zip(ra, rb)))


def saturation(hex_value: str) -> float:
    return colorsys.rgb_to_hls(*_rgb(hex_value))[2]


def _color(node) -> str | None:
    if node is None:
        return None
    srgb = node.find(f"{A}srgbClr")
    if srgb is not None and srgb.get("val"):
        return "#" + srgb.get("val").upper()
    sys = node.find(f"{A}sysClr")
    if sys is not None and sys.get("lastClr"):
        return "#" + sys.get("lastClr").upper()
    return None


def _scheme(xml: bytes) -> tuple[dict[str, str], str, str]:
    root = ElementTree.fromstring(xml)
    colors: dict[str, str] = {}
    scheme = root.find(f".//{A}clrScheme")
    if scheme is not None:
        for key in SCHEME_KEYS:
            value = _color(scheme.find(f"{A}{key}"))
            if value:
                colors[key] = value
    major = root.find(f".//{A}majorFont/{A}latin")
    minor = root.find(f".//{A}minorFont/{A}latin")
    return colors, (major.get("typeface") if major is not None else ""), (minor.get("typeface") if minor is not None else "")


def _slide_usage(archive: zipfile.ZipFile, major: str, minor: str, scheme: dict[str, str]) -> dict:
    fills: Counter = Counter()
    text_small: Counter = Counter()
    text_large: Counter = Counter()
    fonts_small: Counter = Counter()
    fonts_large: Counter = Counter()
    slide_area = 1
    try:
        pres = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
        size = pres.find(f"{P}sldSz")
        slide_area = int(size.get("cx")) * int(size.get("cy"))
    except (KeyError, ElementTree.ParseError, TypeError, AttributeError):
        pass
    names = sorted(n for n in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    for name in names:
        root = ElementTree.fromstring(archive.read(name))
        background = root.find(f".//{P}bg//{A}solidFill")
        bg = _color(background)
        if bg:
            fills[bg] += slide_area
        for sp in root.iter(f"{P}spPr"):
            fill = _color(sp.find(f"{A}solidFill"))
            ext = sp.find(f"{A}xfrm/{A}ext")
            if fill and ext is not None:
                fills[fill] += int(ext.get("cx", 0)) * int(ext.get("cy", 0))
        for run in root.iter(f"{A}r"):
            rpr = run.find(f"{A}rPr")
            text = (run.findtext(f"{A}t") or "").strip()
            if not text:
                continue
            size = int(rpr.get("sz", "1800")) / 100 if rpr is not None else 18
            color = _color(rpr.find(f"{A}solidFill")) if rpr is not None else None
            scheme_ref = rpr.find(f"{A}solidFill/{A}schemeClr") if rpr is not None else None
            if not color and scheme_ref is not None:
                color = scheme.get({"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}.get(scheme_ref.get("val"), scheme_ref.get("val")))
            latin = rpr.find(f"{A}latin") if rpr is not None else None
            face = latin.get("typeface") if latin is not None else ""
            face = {"+mj-lt": major, "+mn-lt": minor}.get(face, face)
            weight = len(text)
            if size >= 24:
                if color:
                    text_large[color] += weight
                if face:
                    fonts_large[face] += weight
            else:
                if color:
                    text_small[color] += weight
                if face:
                    fonts_small[face] += weight
    return {"slides": len(names), "slide_area": slide_area, "fills": fills, "text_small": text_small,
            "text_large": text_large, "fonts_small": fonts_small, "fonts_large": fonts_large}


def installed_fonts() -> set[str]:
    if not shutil.which("fc-list"):
        return set()
    result = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, check=False)
    names: set[str] = set()
    for line in result.stdout.splitlines():
        for name in line.split(","):
            names.add(name.strip().lower())
    return names


def extract_theme(path: Path, *, keep_fonts: bool = False) -> tuple[dict, dict]:
    if not path.is_file() or path.suffix.lower() not in (".pptx", ".potx", ".docx", ".dotx"):
        raise DocumentStudioError("theme extraction needs an existing .pptx, .potx, .docx or .dotx file")
    with zipfile.ZipFile(path) as archive:
        theme_part = next((n for n in archive.namelist() if re.match(r"(ppt|word)/theme/theme\d*\.xml$", n)), None)
        scheme, major, minor = _scheme(archive.read(theme_part)) if theme_part else ({}, "", "")
        usage = _slide_usage(archive, major, minor, scheme) if path.suffix.lower() in (".pptx", ".potx") else None
    evidence: dict = {"scheme": scheme, "theme_fonts": {"heading": major, "body": minor}, "warnings": []}
    background = scheme.get("lt1", "#FFFFFF")
    text = scheme.get("dk1", "#1A1A1A")
    title = scheme.get("dk2", text)
    accent = scheme.get("accent1", "#2E74B5")
    body_font, heading_font = minor or "Arial", major or minor or "Arial"
    if usage and usage["slides"]:
        large_fills = [c for c, area in usage["fills"].most_common() if area >= 0.5 * usage["slide_area"]]
        if large_fills:
            background = large_fills[0]
        if usage["text_small"]:
            text = usage["text_small"].most_common(1)[0][0]
        if usage["text_large"]:
            title = usage["text_large"].most_common(1)[0][0]
        candidates = [c for c, _ in (usage["fills"] + usage["text_large"] + usage["text_small"]).most_common()
                      if saturation(c) > 0.25 and contrast(c, background) > 1.6 and c not in (text, background)]
        if candidates:
            accent = candidates[0]
        if usage["fonts_small"]:
            body_font = usage["fonts_small"].most_common(1)[0][0]
        if usage["fonts_large"]:
            heading_font = usage["fonts_large"].most_common(1)[0][0]
        evidence["usage"] = {
            "slides": usage["slides"],
            "top_fills": [c for c, _ in usage["fills"].most_common(5)],
            "top_text_colors": [c for c, _ in (usage["text_small"] + usage["text_large"]).most_common(5)],
            "top_fonts": [f for f, _ in (usage["fonts_small"] + usage["fonts_large"]).most_common(5)],
        }
    dark = luminance(background) < 0.25
    if contrast(text, background) < 4.5:
        text = "#FFFFFF" if dark else "#1A1A1A"
        evidence["warnings"].append("body text contrast was below 4.5:1; replaced with a readable color")
    if contrast(title, background) < 3:
        title = accent if contrast(accent, background) >= 3 else text
    doc_text = text if not dark else "#1A1A1A"
    doc_heading = title if not dark and contrast(title, "#FFFFFF") >= 3 else (accent if contrast(accent, "#FFFFFF") >= 3 else "#1A1A1A")
    header_bg = accent if contrast(accent, "#FFFFFF") >= 3 else doc_heading
    header_text = "#FFFFFF" if contrast("#FFFFFF", header_bg) >= contrast("#000000", header_bg) else "#000000"
    fonts = {"heading": heading_font, "body": body_font}
    available = installed_fonts()
    if available and not keep_fonts:
        for role, face in list(fonts.items()):
            if face.lower() not in available:
                evidence["warnings"].append(f"font {face!r} ({role}) is not installed; using Arial (keep_fonts=true keeps it for PowerPoint users who have it)")
                fonts[role] = "Arial"
    overrides = {
        "fonts": {"heading": fonts["heading"], "body": fonts["body"], "deck_heading": fonts["heading"], "deck_body": fonts["body"]},
        "colors": {
            "text": doc_text,
            "heading": doc_heading,
            "accent": accent,
            "muted": blend(doc_text, "#FFFFFF", 0.45),
            "table_header_bg": header_bg,
            "table_header_text": header_text,
            "table_stripe": blend(accent, "#FFFFFF", 0.9),
            "slide_background": background,
            "slide_title": title,
            "slide_text": text,
        },
    }
    return overrides, evidence
