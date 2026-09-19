from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.core.providers import provider_catalog, resolve_profile
from xninetzy.os.ai_preferences import (
    resolve_user_profile,
    save_preference,
)


def _user_key(sender_id: str, chat_id: str) -> str:
    return sender_id.strip() or chat_id.strip() or "default"


@tool
def ai_provider_list() -> str:
    """Tampilkan provider dan model chat AI yang tersedia tanpa membocorkan API key."""
    lines = ["*Provider LLM Xninetzy*"]
    for info in provider_catalog().values():
        state = "siap" if info.enabled and info.available else "nonaktif"
        if info.enabled and not info.available:
            state = f"belum siap ({info.missing})"
        models = ", ".join(info.models) or "belum dikonfigurasi"
        lines.append(f"• *{info.name}* — {state}\n  model: {models}")
    lines.append("\nPilih: `/llm use <provider> <model>`")
    return "\n".join(lines)


@tool
def ai_provider_status(sender_id: str = "", chat_id: str = "") -> str:
    """Tampilkan pilihan provider/model chat AI pengguna saat ini."""
    profile = resolve_user_profile(_user_key(sender_id, chat_id))
    return f"LLM aktif: *{profile.provider}* / `{profile.model}`\nLihat pilihan: `/llm list`"


@tool
def ai_provider_use(
    provider: str, model: str = "", sender_id: str = "", chat_id: str = ""
) -> str:
    """Pilih provider/model chat AI dari allowlist operator untuk pengguna saat ini."""
    try:
        profile = resolve_profile(provider, model or None)
    except ValueError as exc:
        return f"❌ {exc}"
    save_preference(
        _user_key(sender_id, chat_id),
        chat_provider=profile.provider,
        chat_model=profile.model,
    )
    return f"✅ LLM diubah ke *{profile.provider}* / `{profile.model}`."
