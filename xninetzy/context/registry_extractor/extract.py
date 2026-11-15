from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xninetzy.skills.registry import discover_skills

REGISTRY_VERSION = "1.0.0"
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "routing"

README_CLAIMED_TOOL_COUNT = 508
README_CLAIMED_SKILL_COUNT = 68


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _stable_serialize(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")


def _read_json_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def extract_tool_manifest() -> dict[str, dict[str, Any]]:
    from xninetzy.tools.manifest import _POLICY_ACTIONS
    from xninetzy.tools.registry import get_all_tools, get_tool_groups
    from xninetzy.tools.tool_meta import meta_for

    hardcoded_names: set[str] = set(_POLICY_ACTIONS.keys())
    groups: dict[str, list[str]] = get_tool_groups()
    name_to_group: dict[str, str | None] = {}
    for group, members in groups.items():
        for m in members:
            name_to_group[m] = group

    out: dict[str, dict[str, Any]] = {}
    for tool in get_all_tools():
        name = getattr(tool, "name", None) or getattr(tool, "__name__", "")
        if not name:
            continue
        meta = meta_for(name)
        manifest = meta.get("risk")
        description = (getattr(tool, "description", "") or "").split("\n", 1)[0]
        entry: dict[str, Any] = {
            "name": name,
            "feature_pack": meta.get("feature_pack", "core"),
            "risk": manifest or "read",
            "stability": meta.get("stability", "stable"),
            "version": meta.get("version", "2.2.0"),
            "requires_approval": bool(meta.get("requires_approval", False)),
            "requires_idempotency": bool(meta.get("requires_idempotency", False)),
            "requires_evidence": bool(meta.get("requires_evidence", False)),
            "auto_discovered": name not in hardcoded_names,
            "max_output_bytes": 32_768,
            "tags": meta.get("tags", []),
            "annotations": meta.get("annotations", {}),
            "description": description,
            "group": name_to_group.get(name),
        }
        if name == "tableau_publish_workbook":
            entry["deprecated"] = False
            entry["replacement"] = None
        out[name] = entry
    return out


def extract_skill_registry() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, skill in discover_skills().items():
        meta = dict(skill.metadata or {})
        triggers = meta.get("triggers", "")
        if isinstance(triggers, str):
            triggers_list: list[str] = [triggers] if triggers else []
        elif isinstance(triggers, list):
            triggers_list = [str(t) for t in triggers]
        else:
            triggers_list = []
        out[name] = {
            "name": name,
            "description": skill.description or "",
            "intent_class": meta.get("intent_class", ""),
            "scope": meta.get("scope", ""),
            "consumes": meta.get("consumes", ""),
            "produces": meta.get("produces", ""),
            "tags": list(meta.get("tags", []) if isinstance(meta.get("tags"), list) else []),
            "triggers": triggers_list,
            "source": skill.source,
            "path": skill.path,
            "routing_version": REGISTRY_VERSION,
            "dependencies": [],
            "trust_level": skill.trust_level,
            "quality_warnings": list(skill.quality_warnings or []),
            "line_count": int(skill.line_count),
            "resource_paths": list(skill.resource_paths or []),
            "content_hash": skill.content_hash,
        }
    return out


def _safe_providers_from_gateway() -> list[dict[str, Any]]:
    try:
        from xninetzy.context.gateway.registry import list_providers

        rows = list_providers()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for p in rows:
        out.append(
            {
                "name": p.provider_id,
                "kind": "external_mcp",
                "transport": p.transport,
                "trust_tier": int(p.trust_tier),
                "risk_class": p.risk_class,
                "capabilities": list(p.capabilities),
                "health_state": p.health_state,
                "last_seen_at": p.last_seen_at,
                "metadata": dict(p.metadata or {}),
            }
        )
    return out


def _safe_llm_providers() -> list[dict[str, Any]]:
    try:
        from xninetzy.core.providers import provider_catalog
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for name, info in provider_catalog().items():
        out.append(
            {
                "name": name,
                "kind": info.kind,
                "default_model": info.default_model,
                "models": list(info.models),
                "base_url": info.base_url,
                "enabled": bool(info.enabled),
                "available": bool(info.available),
                "missing": info.missing or "",
            }
        )
    return out


def _safe_render_providers() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        from xninetzy.context.media.video.renderers import CPU_ALLOWED_ENCODERS
    except Exception:
        CPU_ALLOWED_ENCODERS = []
    for enc in CPU_ALLOWED_ENCODERS:
        out.append({"name": enc, "backend": "ffmpeg", "cpu_allowed": True, "auto_discovered": True})
    try:
        from xninetzy.context.media.video.renderers import RendererRouter

        router = RendererRouter()
        remotion = "remotion" if getattr(router, "has_remotion", False) else None
        if remotion:
            out.append({"name": remotion, "backend": "remotion", "cpu_allowed": True, "auto_discovered": True})
    except Exception:
        pass
    return out


def _safe_dashboard_providers() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        from xninetzy.tools.internal.data_analysis import dashboard_list_providers

        kind = dashboard_list_providers.invoke({})
    except Exception:
        kind = None
    if isinstance(kind, dict):
        providers = kind.get("providers") or []
    elif isinstance(kind, list):
        providers = kind
    else:
        providers = []
    for entry in providers:
        if not isinstance(entry, dict):
            continue
        name = entry.get("provider_id") or entry.get("name") or entry.get("id")
        if not name:
            continue
        out.append(
            {
                "name": str(name),
                "kind": str(entry.get("kind") or "dashboard"),
                "auto_discovered": True,
            }
        )
    return out


def extract_provider_registry() -> dict[str, list[dict[str, Any]]]:
    llm = _safe_llm_providers()
    external_mcp = _safe_providers_from_gateway()
    render = _safe_render_providers()
    dashboard = _safe_dashboard_providers()

    research_source: list[dict[str, Any]] = []
    try:
        from xninetzy.os.research.sources.registry import list_adapters

        registered = set(list_adapters())
    except Exception:
        registered = set()
    try:
        from xninetzy.os.research.sources.base import SourceCategory

        categories = {c.value for c in SourceCategory}
    except Exception:
        categories = set()

    return {
        "external_mcp": external_mcp,
        "llm": llm,
        "research_source": research_source,
        "render": render,
        "dashboard": dashboard,
        "_registered_research_sids": sorted(registered),
        "_research_categories": sorted(categories),
    }


def _discover_research_source_modules() -> list[dict[str, Any]]:

    import xninetzy.os.research.sources as sources_pkg

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for attr_name in dir(sources_pkg):
        mod = getattr(sources_pkg, attr_name)
        if not (hasattr(mod, "__file__") and getattr(mod, "__name__", "").startswith("xninetzy.os.research.sources.")):
            continue
        if attr_name in {"base", "rate_limit", "registry", "query_match", "browser_scraper", "browser_session", "_compat"}:
            continue
        adapter_name = attr_name
        if adapter_name in seen:
            continue
        seen.add(adapter_name)
        module_path = getattr(mod, "__file__", "") or ""
        entry: dict[str, Any] = {
            "adapter": adapter_name,
            "module_path": module_path,
            "version": REGISTRY_VERSION,
            "registered": False,
            "auto_discovered": True,
        }
        out.append(entry)
    return out


def extract_research_sources() -> list[dict[str, Any]]:
    sources = _discover_research_source_modules()
    try:
        from xninetzy.os.research.sources.registry import SOURCE_REGISTRY

        registered = set(SOURCE_REGISTRY.keys())
    except Exception:
        registered = set()
    for entry in sources:
        entry["registered"] = entry["adapter"] in registered
        if entry["registered"]:
            try:
                adapter = SOURCE_REGISTRY[entry["adapter"]]
                category = getattr(getattr(adapter, "category", None), "value", None)
                entry["category"] = str(category) if category else None
                entry["base_url"] = getattr(adapter, "base_url", "")
                entry["requires_api_key"] = bool(getattr(adapter, "requires_api_key", False))
                rl = getattr(adapter, "rate_limit", None)
                if rl is not None:
                    entry["rate_limits"] = {
                        "requests_per_minute": int(getattr(rl, "requests_per_minute", 0) or 0),
                        "burst": int(getattr(rl, "burst", 0) or 0),
                    }
            except Exception:
                pass
    return sources


def _read_empty_tool_groups(groups: dict[str, list[str]] | None = None) -> list[str]:
    if groups is None:
        from xninetzy.tools.registry import get_tool_groups

        groups = get_tool_groups()
    return sorted(name for name, members in groups.items() if not members)


def compute_drift(
    *,
    current_manifest: dict[str, dict[str, Any]],
    current_skills: dict[str, dict[str, Any]],
    current_providers: dict[str, list[dict[str, Any]]] | None = None,
    current_sources: list[dict[str, Any]] | None = None,
    output_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    from xninetzy.tools.registry import get_tool_groups

    groups = get_tool_groups()
    empty_groups = _read_empty_tool_groups(groups)

    actual_tool_count = len(current_manifest)
    actual_skill_count = len(current_skills)
    prov = current_providers or {}
    src = current_sources or []

    providers_summary = {
        "external_mcp": len(prov.get("external_mcp", [])),
        "llm": len(prov.get("llm", [])),
        "research_source": len(prov.get("research_source", []) or []),
        "render": len(prov.get("render", [])),
        "dashboard": len(prov.get("dashboard", [])),
    }

    history: list[dict[str, Any]] = []
    history_dir = (output_root / "history") if output_root else None
    if history_dir and history_dir.exists():
        for p in sorted(history_dir.glob("*.json")):
            try:
                entry = json.loads(p.read_text(encoding="utf-8"))
                if entry.get("generated_at") == (generated_at or _utcnow()):
                    continue
                history.append(entry)
            except Exception:
                continue

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "generated_at": generated_at or _utcnow(),
        "drift": {
            "tool_count": {
                "actual": actual_tool_count,
                "claimed_in_README": README_CLAIMED_TOOL_COUNT,
                "delta": actual_tool_count - README_CLAIMED_TOOL_COUNT,
            },
            "empty_groups_count": len(empty_groups),
            "empty_groups": empty_groups,
            "skill_count": {
                "actual": actual_skill_count,
                "claimed_in_README": README_CLAIMED_SKILL_COUNT,
                "delta": actual_skill_count - README_CLAIMED_SKILL_COUNT,
            },
            "providers": providers_summary,
            "research_source_count": len(src),
        },
        "version_history": history,
    }


def validate_against_schemas(payload: dict[str, Any], schema_name: str) -> bool:
    try:
        import jsonschema
    except ImportError:
        return _minimal_validate(payload, schema_name)

    schema = _read_json_schema(schema_name)
    jsonschema.validate(payload, schema)
    return True


def _minimal_validate(payload: dict[str, Any], schema_name: str) -> bool:
    if schema_name == "manifest":
        if not isinstance(payload, dict):
            return False
        if "tools" not in payload or "tool_count" not in payload:
            return False
        return all(isinstance(v, dict) and "name" in v and "risk" in v and "tags" in v for v in payload["tools"].values())
    if schema_name == "skills":
        return isinstance(payload, dict) and "skills" in payload and "skill_count" in payload
    if schema_name == "providers":
        return isinstance(payload, dict) and "providers" in payload
    if schema_name == "research_sources":
        return isinstance(payload, dict) and "sources" in payload and isinstance(payload["sources"], list)
    if schema_name == "drift":
        return isinstance(payload, dict) and "drift" in payload and "generated_at" in payload
    return False


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    raw = _stable_serialize(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    sha = _sha256_bytes(raw)
    path.with_suffix(path.suffix + ".sha256").write_text(sha + "\n", encoding="utf-8")
    return sha


def write_outputs(
    output_root: str | Path = "data/registry",
    *,
    write: bool = False,
    verbose: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = extract_tool_manifest()
    skills = extract_skill_registry()
    providers = extract_provider_registry()
    sources = extract_research_sources()

    ts = generated_at or _utcnow()
    manifest_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "generated_at": ts,
        "tool_count": len(manifest),
        "tools": manifest,
    }
    skills_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "generated_at": ts,
        "skill_count": len(skills),
        "skills": skills,
    }
    providers_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "generated_at": ts,
        "providers": providers,
    }
    sources_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": REGISTRY_VERSION,
        "registry_version": REGISTRY_VERSION,
        "generated_at": ts,
        "count": len(sources),
        "sources": sources,
    }
    drift_doc = compute_drift(
        current_manifest=manifest,
        current_skills=skills,
        current_providers=providers,
        current_sources=sources,
        output_root=root,
        generated_at=ts,
    )

    paths: dict[str, Path] = {
        "manifest": root / "routing_manifest.json",
        "skills": root / "routing_skills.json",
        "providers": root / "routing_providers.json",
        "research_sources": root / "routing_research_sources.json",
        "drift": root / "routing_drift.json",
    }

    shas: dict[str, str] = {}
    if write:
        for name, payload in (
            ("manifest", manifest_doc),
            ("skills", skills_doc),
            ("providers", providers_doc),
            ("research_sources", sources_doc),
            ("drift", drift_doc),
        ):
            shas[name] = _write_json(paths[name], payload)
        history_dir = root / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        ts = drift_doc["generated_at"].replace(":", "").replace("-", "")
        history_path = history_dir / f"{ts}.json"
        history_entry = {
            "generated_at": drift_doc["generated_at"],
            "manifest_sha256": shas["manifest"],
            "tool_count": drift_doc["drift"]["tool_count"]["actual"],
            "skill_count": drift_doc["drift"]["skill_count"]["actual"],
        }
        history_path.write_text(json.dumps(history_entry, ensure_ascii=False), encoding="utf-8")

    if verbose:
        import sys

        sys.stdout.write(
            f"manifest.tools={len(manifest)} "
            f"skills={len(skills)} "
            f"providers.llm={len(providers.get('llm', []))} "
            f"external_mcp={len(providers.get('external_mcp', []))} "
            f"render={len(providers.get('render', []))} "
            f"dashboard={len(providers.get('dashboard', []))} "
            f"research_source_modules={len(sources)}\n"
        )
        sys.stdout.flush()

    return {
        "manifest": manifest_doc,
        "skills": skills_doc,
        "providers": providers_doc,
        "research_sources": sources_doc,
        "drift": drift_doc,
        "paths": {name: str(path) for name, path in paths.items()},
        "shas": shas,
    }
