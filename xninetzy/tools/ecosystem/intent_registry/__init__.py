from __future__ import annotations

import json
from pathlib import Path

_REGISTRY_DIR = Path(__file__).resolve().parent


def load_intent_registry() -> dict[str, tuple[str, set[str]]]:
    registry: dict[str, tuple[str, set[str]]] = {}
    for path in sorted(_REGISTRY_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            domain = str(data.get("domain", path.stem)).strip()
            keywords = data.get("keywords") or {}
            if not isinstance(keywords, dict):
                continue
            for keyword, tools in keywords.items():
                if not isinstance(tools, list):
                    continue
                keyword_norm = str(keyword).strip().lower()
                if not keyword_norm:
                    continue
                registry[keyword_norm] = (domain, {str(t) for t in tools if t})
        except Exception:
            continue
    return registry


def list_domains() -> list[str]:
    domains: set[str] = set()
    for path in sorted(_REGISTRY_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            domains.add(str(data.get("domain", path.stem)))
        except Exception:
            continue
    return sorted(domains)


def reload() -> dict[str, tuple[str, set[str]]]:
    global _cached
    _cached = load_intent_registry()
    return _cached


_cached: dict[str, tuple[str, set[str]]] | None = None


def get() -> dict[str, tuple[str, set[str]]]:
    global _cached
    if _cached is None:
        _cached = load_intent_registry()
    return _cached
