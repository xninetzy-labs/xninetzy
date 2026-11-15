from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from xninetzy.core.config import expand_path, get_settings
from xninetzy.integrations.document_studio.errors import DocumentStudioError

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BUILTIN_DIR = Path(__file__).resolve().parents[2] / "templates" / "document_studio" / "themes"


class Fonts(BaseModel):
    body: str = "Arial"
    heading: str = "Arial"
    mono: str = "DejaVu Sans Mono"
    deck_body: str | None = None
    deck_heading: str | None = None


class Sizes(BaseModel):
    body: float = 11
    small: float = 9
    title: float = 28
    subtitle: float = 16
    h1: float = 20
    h2: float = 15
    h3: float = 12.5
    slide_title: float = 30
    slide_body: float = 20
    slide_min: float = 14


class Colors(BaseModel):
    text: str = "#1A1A1A"
    heading: str = "#1F3864"
    accent: str = "#2E74B5"
    muted: str = "#666666"
    table_header_bg: str = "#1F3864"
    table_header_text: str = "#FFFFFF"
    table_stripe: str = "#EEF3FA"
    slide_background: str = "#FFFFFF"
    slide_title: str = "#1F3864"
    slide_text: str = "#1A1A1A"

    @field_validator("*")
    @classmethod
    def _hex(cls, value: str) -> str:
        if not HEX.match(value):
            raise ValueError(f"color must be #RRGGBB, got {value!r}")
        return value.upper()


class Page(BaseModel):
    size: Literal["A4", "Letter"] = "A4"
    margin_top_cm: float = 2.54
    margin_bottom_cm: float = 2.54
    margin_left_cm: float = 2.54
    margin_right_cm: float = 2.54


class DocumentOptions(BaseModel):
    language: Literal["id", "en"] = "en"
    line_spacing: float = 1.15
    paragraph_after_pt: float = 6
    justify: bool = False
    cover: bool = True
    toc: bool = False
    page_numbers: bool = True
    heading_numbering: bool = False
    caption_numbering: bool = True
    header_text: str = ""
    footer_text: str = ""


class DeckOptions(BaseModel):
    aspect: Literal["16:9", "4:3"] = "16:9"
    accent_bar: bool = True
    slide_numbers: bool = True
    max_bullets: int = Field(default=6, ge=2, le=12)
    max_table_rows: int = Field(default=8, ge=2, le=20)
    footer_text: str = ""


class Theme(BaseModel):
    name: str
    description: str = ""
    fonts: Fonts = Fonts()
    sizes: Sizes = Sizes()
    colors: Colors = Colors()
    page: Page = Page()
    document: DocumentOptions = DocumentOptions()
    deck: DeckOptions = DeckOptions()

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        if not NAME.match(value) or len(value) > 48:
            raise ValueError("theme name must be lowercase kebab-case, at most 48 characters")
        return value

    @property
    def deck_heading_font(self) -> str:
        return self.fonts.deck_heading or self.fonts.heading

    @property
    def deck_body_font(self) -> str:
        return self.fonts.deck_body or self.fonts.body


def user_theme_dir() -> Path:
    return Path(expand_path(get_settings().DATA_DIR)) / "document_studio" / "themes"


def _read(path: Path) -> Theme:
    try:
        return Theme.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        raise DocumentStudioError(f"invalid theme file {path.name}: {exc}") from exc


def list_themes() -> list[dict]:
    found: dict[str, dict] = {}
    for source, root in (("builtin", BUILTIN_DIR), ("user", user_theme_dir())):
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.json")):
            theme = _read(path)
            found[theme.name] = {"name": theme.name, "description": theme.description, "source": source}
    return list(found.values())


def load_theme(name: str) -> Theme:
    key = (name or "professional").strip().lower()
    for root in (user_theme_dir(), BUILTIN_DIR):
        path = root / f"{key}.json"
        if path.is_file():
            return _read(path)
    available = ", ".join(item["name"] for item in list_themes())
    raise DocumentStudioError(f"unknown theme {key!r}; available: {available}")


def merge(base: dict, overrides: dict) -> dict:
    out = dict(base)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out


def save_theme(name: str, overrides: dict, base: str = "professional") -> tuple[Theme, Path]:
    parent = load_theme(base).model_dump()
    theme = Theme.model_validate(merge(parent, {**(overrides or {}), "name": name}))
    if (BUILTIN_DIR / f"{theme.name}.json").is_file():
        raise DocumentStudioError(f"{theme.name!r} is a built-in theme; save under another name")
    root = user_theme_dir()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{theme.name}.json"
    path.write_text(json.dumps(theme.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return theme, path
