from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    etree = None

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "templates" / "tableau" / "schemas"
SCHEMA_FILES: dict[str, str] = {"26.1": "twb_2026.1.0.xsd", "26.2": "twb_2026.2.0.xsd"}
FORMAT_SCHEMA: dict[str, str] = {"18.1": "26.2"}
DEFAULT_VERSION = "26.2"
MAX_ERRORS = 50


def supported_versions() -> tuple[str, ...]:
    return tuple(SCHEMA_FILES)


def resolve_version(version: str) -> str:
    return FORMAT_SCHEMA.get(version, version)


def available() -> bool:
    return etree is not None and all((SCHEMA_DIR / name).is_file() for name in SCHEMA_FILES.values())


@lru_cache(maxsize=4)
def _schema(version: str):
    return etree.XMLSchema(etree.parse(str(SCHEMA_DIR / SCHEMA_FILES[version])))


def declared_version(data: bytes | str) -> str:
    if etree is None:
        return ""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    try:
        root = etree.fromstring(raw, etree.XMLParser(resolve_entities=False, no_network=True))
    except etree.XMLSyntaxError:
        return ""
    return str(root.get("version") or "")


def validate(data: bytes | str, version: str | None = None) -> list[str]:
    if etree is None:
        raise RuntimeError("lxml tidak terpasang")
    chosen = resolve_version(version or declared_version(data) or DEFAULT_VERSION)
    if chosen not in SCHEMA_FILES:
        raise KeyError(chosen)
    raw = data.encode("utf-8") if isinstance(data, str) else data
    if b"<!DOCTYPE" in raw[:4096].upper() or b"<!ENTITY" in raw[:4096].upper():
        return ["Error(0,0): DOCTYPE/ENTITY tidak diizinkan di workbook"]
    try:
        document = etree.fromstring(raw, etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
    except etree.XMLSyntaxError as exc:
        return [f"Error(0,0): XML tidak well-formed: {exc}"]
    schema = _schema(chosen)
    if schema.validate(document):
        return []
    return [f"Error({entry.line},{entry.column}): {entry.message}" for entry in list(schema.error_log)[:MAX_ERRORS]]
