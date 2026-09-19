from __future__ import annotations

import ipaddress

from mcp.server.fastmcp import FastMCP

# Bootstrap host-safe paths before modules below can load get_settings().
from xninetzy.interfaces.mcp_runtime import (
    MCP_PATH_OVERRIDES as _MCP_PATH_OVERRIDES,
)
from xninetzy.interfaces.mcp_tool_adapter import (
    expose_xninetzy_tools,
    mcp_principal,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import init_db
from xninetzy.core.config import get_settings

from xninetzy.tools.ecosystem.knowledge_tools import (
    knowledge_answer as _knowledge_answer,
    knowledge_ingest_text as _knowledge_ingest_text,
    knowledge_list_sources as _knowledge_list_sources,
    knowledge_search as _knowledge_search,
)
from xninetzy.tools.ecosystem.life_tools import (
    task_capture as _task_capture,
    task_complete as _task_complete,
    task_list as _task_list,
    task_today as _task_today,
)
from xninetzy.tools.internal.obsidian import (
    obsidian_add_tags as _obsidian_add_tags,
    obsidian_append as _obsidian_append,
    obsidian_backlinks as _obsidian_backlinks,
    obsidian_create as _obsidian_create,
    obsidian_headings as _obsidian_headings,
    obsidian_list as _obsidian_list,
    obsidian_read as _obsidian_read,
    obsidian_search as _obsidian_search,
    obsidian_set_frontmatter as _obsidian_set_frontmatter,
    obsidian_todos as _obsidian_todos,
    obsidian_update_section as _obsidian_update_section,
)
from xninetzy.tools.internal.reminder import (
    reminder_cancel as _reminder_cancel,
    reminder_create as _reminder_create,
    reminder_list as _reminder_list,
)

init_db()
run_migrations()

# stdio MCP reserves stdout for protocol messages, so bootstrap stays silent.
assert isinstance(_MCP_PATH_OVERRIDES, dict)
_MCP_PRINCIPAL = mcp_principal()
_MCP_CONTEXT = _MCP_PRINCIPAL.as_tool_context()


_XNINETZY_SETTINGS = get_settings()
_TRANSPORT = (_XNINETZY_SETTINGS.XNINETZY_MCP_TRANSPORT or "stdio").strip().lower()
_HTTP_HOST = (_XNINETZY_SETTINGS.XNINETZY_MCP_HTTP_HOST or "127.0.0.1").strip()
_HTTP_PORT = int(_XNINETZY_SETTINGS.XNINETZY_MCP_HTTP_PORT)
_HTTP_PATH = (_XNINETZY_SETTINGS.XNINETZY_MCP_HTTP_PATH or "/mcp").strip()
_HTTP_STATELESS = True
_HTTP_JSON = True

if _TRANSPORT not in {"stdio", "streamable-http"}:
    raise ValueError(
        f"XNINETZY_MCP_TRANSPORT must be stdio|streamable-http, got: {_TRANSPORT!r}"
    )

if _TRANSPORT == "streamable-http":
    try:
        bound = ipaddress.ip_address(_HTTP_HOST)
    except ValueError as exc:
        raise ValueError(f"XNINETZY_MCP_HTTP_HOST must be a valid IP, got: {_HTTP_HOST!r}") from exc
    if not bound.is_loopback:
        import sys
        print(
            "WARNING: XNINETZY_MCP_HTTP_HOST is non-loopback; "
            "Streamable HTTP must carry real auth (OAuth 2.1 + Resource Indicators) "
            "before exposing beyond localhost.",
            file=sys.stderr,
        )


mcp = FastMCP(
    "xninetzy",
    instructions=(
        "Akses Xninetzy OS milik owner lokal: Obsidian, knowledge, learning, HEBAT, "
        "life OS, task, reminder, research, dan workflow. Gunakan knowledge_answer "
        "untuk jawaban tersintesis dan tersitasi; knowledge_search hanya untuk inspeksi "
        "bukti. Gunakan skill_suggest_for_request lalu skill_get untuk memuat workflow "
        "dinamis; gunakan skill_resource_list/read untuk progressive disclosure. Skill baru "
        "dipasang owner melalui skill_validate dan skill_install, "
        "tanpa menambah tool atau kode client. Semua path vault harus relatif terhadap vault."
    ),
    stateless_http=_HTTP_STATELESS,
    json_response=_HTTP_JSON,
    host=_HTTP_HOST,
    port=_HTTP_PORT,
    streamable_http_path=_HTTP_PATH,
)


@mcp.tool()
def obsidian_list(folder: str = "", limit: int = 100) -> str:
    """Daftar note di vault Obsidian."""
    return str(_obsidian_list.invoke({"folder": folder, "limit": limit}))


@mcp.tool()
def obsidian_search(query: str, limit: int = 10) -> str:
    """Cari note berdasarkan keyword."""
    return str(_obsidian_search.invoke({"query": query, "limit": limit}))


@mcp.tool()
def obsidian_read(path: str) -> str:
    """Baca note memakai path relatif vault."""
    return str(_obsidian_read.invoke({"path": path}))


@mcp.tool()
def obsidian_create(path: str, content: str) -> str:
    """Buat note baru; gagal bila path sudah ada."""
    return str(_obsidian_create.invoke({"path": path, "content": content}))


@mcp.tool()
def obsidian_append(path: str, content: str) -> str:
    """Tambahkan markdown ke note."""
    return str(_obsidian_append.invoke({"path": path, "content": content}))


@mcp.tool()
def obsidian_update_section(path: str, heading: str, content: str) -> str:
    """Perbarui atau buat section note berdasarkan heading."""
    return str(
        _obsidian_update_section.invoke(
            {"path": path, "heading": heading, "content": content}
        )
    )


@mcp.tool()
def obsidian_todos(folder: str = "", limit: int = 100) -> str:
    """Ambil checkbox todo dari vault."""
    return str(_obsidian_todos.invoke({"folder": folder, "limit": limit}))


@mcp.tool()
def obsidian_backlinks(note_path: str, limit: int = 100) -> str:
    """Cari backlinks ke note tertentu."""
    return str(_obsidian_backlinks.invoke({"note_path": note_path, "limit": limit}))


@mcp.tool()
def obsidian_headings(path: str) -> str:
    """Baca struktur heading note."""
    return str(_obsidian_headings.invoke({"path": path}))


@mcp.tool()
def obsidian_add_tags(path: str, tags: list[str]) -> str:
    """Tambahkan tag tanpa menghapus tag lama."""
    return str(_obsidian_add_tags.invoke({"path": path, "tags": tags}))


@mcp.tool()
def obsidian_set_frontmatter(path: str, data: dict) -> str:
    """Tambah atau perbarui frontmatter note."""
    return str(_obsidian_set_frontmatter.invoke({"path": path, "data": data}))


@mcp.tool()
def knowledge_search(query: str, limit: int = 5) -> str:
    """Cari di knowledge base Xninetzy."""
    return str(_knowledge_search.invoke({"query": query, "limit": limit}))


@mcp.tool()
async def knowledge_answer(query: str) -> str:
    """Jawab dari knowledge melalui retrieval, sintesis, dan sitasi tervalidasi."""
    return str(
        await _knowledge_answer.ainvoke(
            {"query": query, "chat_id": _MCP_CONTEXT["chat_id"]}
        )
    )


@mcp.tool()
def knowledge_list_sources(source_type: str = "", limit: int = 20) -> str:
    """Daftar sumber knowledge yang telah diingest."""
    return str(
        _knowledge_list_sources.invoke(
            {"source_type": source_type or None, "limit": limit}
        )
    )


@mcp.tool()
def knowledge_ingest_text(
    title: str,
    text: str,
    source_type: str = "manual_note",
    uri: str = "",
    idempotency_key: str = "",
) -> str:
    """Ingest teks ke knowledge base."""
    return str(
        _knowledge_ingest_text.invoke(
            {
                "title": title,
                "text": text,
                "source_type": source_type,
                "uri": uri or None,
                "chat_id": _MCP_CONTEXT["chat_id"],
                "idempotency_key": idempotency_key,
            }
        )
    )


@mcp.tool()
def task_list(status: str = "") -> str:
    """Daftar task aktif atau berdasarkan status."""
    return str(_task_list.invoke({"status": status or None}))


@mcp.tool()
def task_today() -> str:
    """Daftar task due atau overdue hari ini."""
    return str(_task_today.invoke({}))


@mcp.tool()
def task_capture(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_at: str = "",
    idempotency_key: str = "",
) -> str:
    """Buat task baru."""
    return str(
        _task_capture.invoke(
            {
                "title": title,
                "description": description,
                "priority": priority,
                "due_at": due_at or None,
                "goal_id": None,
                "chat_id": _MCP_CONTEXT["chat_id"],
                "idempotency_key": idempotency_key,
            }
        )
    )


@mcp.tool()
def task_complete(task_id: int) -> str:
    """Tandai task selesai."""
    return str(
        _task_complete.invoke({"task_id": task_id, "chat_id": _MCP_CONTEXT["chat_id"]})
    )


@mcp.tool()
def reminder_list() -> str:
    """Daftar reminder pending untuk owner lokal."""
    return str(_reminder_list.invoke({"chat_id": _MCP_CONTEXT["chat_id"]}))


@mcp.tool()
def reminder_create(message: str) -> str:
    """Buat reminder dari kalimat natural language."""
    return str(
        _reminder_create.invoke(
            {"chat_id": _MCP_CONTEXT["chat_id"], "message": message}
        )
    )


@mcp.tool()
def reminder_cancel(reminder_id: int) -> str:
    """Batalkan reminder berdasarkan ID."""
    return str(_reminder_cancel.invoke({"reminder_id": reminder_id}))


EXPOSED_XNINETZY_TOOLS = expose_xninetzy_tools(mcp, principal=_MCP_PRINCIPAL)


@mcp.resource("xninetzy://skills/index")
def skills_index_resource() -> str:
    """List installed skills (name + version + trust level) as a JSON resource."""
    from xninetzy.skills.registry import list_skills

    rows = []
    for skill in list_skills():
        rows.append(
            {
                "name": skill.name,
                "version": skill.metadata.get("version", "unknown"),
                "trust_level": skill.trust_level,
                "source": skill.source,
            }
        )
    import json

    return json.dumps({"count": len(rows), "skills": rows}, ensure_ascii=False, sort_keys=True)


@mcp.resource("xninetzy://tools/catalog")
def tools_catalog_resource() -> str:
    """Tool catalog with risk class and feature pack metadata."""
    from xninetzy.tools.manifest import manifest_for
    from xninetzy.tools.registry import get_tool_names

    rows = []
    for name in get_tool_names():
        try:
            m = manifest_for(name)
            rows.append(
                {
                    "name": name,
                    "feature_pack": m.feature_pack.value,
                    "risk": m.risk.value,
                    "requires_approval": m.requires_approval,
                    "requires_idempotency": m.requires_idempotency,
                }
            )
        except Exception:
            rows.append({"name": name, "error": "manifest_unavailable"})
    import json

    return json.dumps({"count": len(rows), "tools": rows}, ensure_ascii=False, sort_keys=True)


@mcp.prompt("xninetzy-memory-checklist")
def memory_checklist_prompt() -> str:
    """Standard pre-write memory checklist surfaced as a reusable prompt template."""
    return (
        "Before persisting any memory, confirm the following:\n"
        "1. The content is durable (decisions, requirements, stable constraints, blockers, next actions).\n"
        "2. It is not ephemeral reasoning, secrets, or session tokens.\n"
        "3. It carries source provenance (URL, document id, conversation turn).\n"
        "4. Its freshness window is explicit (default 90 days).\n"
        "5. It does not contradict an existing memory (use memory_promote / memory_retire).\n"
        "Persist via the memory_add tool only when all five are satisfied."
    )


def main() -> None:
    if _TRANSPORT == "streamable-http":
        mcp.settings.host = _HTTP_HOST
        mcp.settings.port = _HTTP_PORT
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
