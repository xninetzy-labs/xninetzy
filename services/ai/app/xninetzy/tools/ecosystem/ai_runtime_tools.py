from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.core.coding_agents import (
    run_coding_agent,
    runtime_catalog,
    validate_runtime,
)
from app.xninetzy.core.config import get_settings
from app.xninetzy.core.providers import provider_catalog, resolve_profile
from app.xninetzy.os.ai_preferences import (
    get_preference,
    resolve_user_profile,
    save_preference,
)
from app.xninetzy.os.research.permissions import is_owner_admin


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


@tool
def coding_agent_list() -> str:
    """Tampilkan runtime coding-agent lokal yang diizinkan dan tersedia."""
    lines = ["*Coding agents*"]
    for info in runtime_catalog().values():
        if not info.allowed:
            state = "tidak diizinkan"
        elif not info.installed:
            state = "binary tidak ditemukan"
        else:
            state = "siap"
        model = f" — model `{info.model}`" if info.model else ""
        lines.append(f"• *{info.name}*: {state}{model}")
    lines.append("\nPilih: `/agent use codex|claude-code|opencode|internal`")
    return "\n".join(lines)


@tool
def coding_agent_status(sender_id: str = "", chat_id: str = "") -> str:
    """Tampilkan coding-agent yang dipilih pengguna."""
    user_id = _user_key(sender_id, chat_id)
    preference = get_preference(user_id) or {}
    selected = preference.get("coding_agent") or get_settings().CODING_AGENT_DEFAULT
    return f"Coding agent aktif: *{selected}*\nLihat pilihan: `/agent list`"


@tool
def coding_agent_use(runtime: str, sender_id: str = "", chat_id: str = "") -> str:
    """Pilih runtime coding-agent lokal untuk pengguna saat ini."""
    try:
        info = validate_runtime(runtime)
    except ValueError as exc:
        return f"❌ {exc}"
    save_preference(_user_key(sender_id, chat_id), coding_agent=info.name)
    return f"✅ Coding agent diubah ke *{info.name}*."


@tool
async def coding_agent_run(
    task: str,
    workspace: str = "",
    sender_id: str = "",
    sender_name: str = "",
    chat_id: str = "",
) -> str:
    """Jalankan task coding melalui Codex, Claude Code, atau OpenCode yang dipilih.

    Eksekusi dibatasi workspace, timeout, allowlist runtime, dan kebijakan admin.
    """
    settings = get_settings()
    if settings.CODING_AGENT_ADMIN_ONLY and not is_owner_admin(sender_id, sender_name):
        return "❌ `/code` hanya dapat dijalankan oleh admin utama."

    user_id = _user_key(sender_id, chat_id)
    preference = get_preference(user_id) or {}
    runtime = preference.get("coding_agent") or settings.CODING_AGENT_DEFAULT
    if runtime == "internal":
        return "Runtime *internal* memakai agent chat biasa. Pilih `/agent use codex`, `claude-code`, atau `opencode`."
    try:
        result = await run_coding_agent(
            runtime,
            task,
            user_id=user_id,
            chat_id=chat_id or user_id,
            workspace=workspace or None,
        )
    except (OSError, ValueError) as exc:
        return f"❌ Coding agent gagal dimulai: {exc}"

    header = f"*{runtime}* — {result.status} (`{result.run_id[:8]}`)"
    body = result.output or result.error or "Tidak ada output."
    if result.error and result.output:
        body += f"\n\n_Error:_\n{result.error}"
    return f"{header}\n\n{body}"
