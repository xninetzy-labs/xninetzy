from __future__ import annotations

from dataclasses import asdict, dataclass

from app.xninetzy.core.config import Settings, get_settings


@dataclass(frozen=True)
class LLMProfile:
    provider: str
    model: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    kind: str
    default_model: str
    models: tuple[str, ...]
    base_url: str
    enabled: bool
    available: bool
    missing: str = ""


def _csv(value: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.strip() for item in value.split(",") if item.strip())
    )


def _with_default(default: str, configured: str) -> tuple[str, ...]:
    return _csv(",".join(part for part in (default.strip(), configured) if part))


def provider_catalog(settings: Settings | None = None) -> dict[str, ProviderInfo]:
    s = settings or get_settings()
    enabled = set(_csv(s.LLM_ENABLED_PROVIDERS.lower()))

    raw = {
        "flaz": (
            "openai-compatible",
            s.FLAZ_MODEL,
            s.FLAZ_MODELS,
            s.FLAZ_BASE_URL,
            s.FLAZ_API_KEY,
            True,
        ),
        "openai": (
            "openai-compatible",
            s.OPENAI_MODEL,
            s.OPENAI_MODELS,
            s.OPENAI_BASE_URL,
            s.OPENAI_API_KEY,
            True,
        ),
        "anthropic": (
            "anthropic",
            s.ANTHROPIC_MODEL,
            s.ANTHROPIC_MODELS,
            "",
            s.ANTHROPIC_API_KEY,
            True,
        ),
        "openrouter": (
            "openai-compatible",
            s.OPENROUTER_MODEL,
            s.OPENROUTER_MODELS,
            s.OPENROUTER_BASE_URL,
            s.OPENROUTER_API_KEY,
            True,
        ),
        "ollama": (
            "openai-compatible",
            s.OLLAMA_MODEL,
            s.OLLAMA_MODELS,
            s.OLLAMA_BASE_URL,
            "local",
            False,
        ),
        "generic": (
            "openai-compatible",
            s.GENERIC_OPENAI_MODEL,
            s.GENERIC_OPENAI_MODELS,
            s.GENERIC_OPENAI_BASE_URL,
            s.GENERIC_OPENAI_API_KEY,
            False,
        ),
    }
    result: dict[str, ProviderInfo] = {}
    for name, (
        kind,
        default,
        configured,
        base_url,
        api_key,
        requires_key,
    ) in raw.items():
        models = _with_default(default, configured)
        missing: list[str] = []
        if not models:
            missing.append("model")
        if kind == "openai-compatible" and not base_url.strip():
            missing.append("base URL")
        if requires_key and not api_key.strip():
            missing.append(
                {
                    "flaz": "FLAZ_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                }[name]
            )
        result[name] = ProviderInfo(
            name=name,
            kind=kind,
            default_model=default.strip(),
            models=models,
            base_url=base_url.rstrip("/"),
            enabled=name in enabled,
            available=not missing,
            missing=", ".join(missing),
        )
    return result


def resolve_profile(
    provider: str | None = None,
    model: str | None = None,
    settings: Settings | None = None,
) -> LLMProfile:
    s = settings or get_settings()
    name = (provider or s.LLM_DEFAULT_PROVIDER).strip().lower()
    catalog = provider_catalog(s)
    info = catalog.get(name)
    if info is None:
        raise ValueError(f"Provider tidak dikenal: {name}")
    if not info.enabled:
        raise ValueError(
            f"Provider '{name}' belum diaktifkan di LLM_ENABLED_PROVIDERS."
        )
    if not info.available:
        raise ValueError(f"Provider '{name}' belum siap: {info.missing}.")

    selected = (model or info.default_model).strip()
    if selected not in info.models:
        allowed = ", ".join(info.models)
        raise ValueError(
            f"Model '{selected}' tidak diizinkan untuk {name}. Pilihan: {allowed}"
        )
    return LLMProfile(provider=name, model=selected)


def profile_from_metadata(metadata: dict | None) -> LLMProfile | None:
    value = (metadata or {}).get("_llm_profile")
    if not isinstance(value, dict):
        return None
    provider = value.get("provider")
    model = value.get("model")
    if not isinstance(provider, str) or not isinstance(model, str):
        return None
    return LLMProfile(provider=provider, model=model)
