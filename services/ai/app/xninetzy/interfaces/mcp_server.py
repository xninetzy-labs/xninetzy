from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# Bootstrap host-safe paths before modules below can load get_settings().
from app.xninetzy.interfaces.mcp_runtime import (
    MCP_PATH_OVERRIDES as _MCP_PATH_OVERRIDES,
)
from app.xninetzy.interfaces.mcp_tool_adapter import (
    expose_xninetzy_tools,
    mcp_principal,
)

from app.xninetzy.tools.ecosystem.knowledge_tools import (
    knowledge_answer as _knowledge_answer,
    knowledge_ingest_text as _knowledge_ingest_text,
    knowledge_list_sources as _knowledge_list_sources,
    knowledge_search as _knowledge_search,
)
from app.xninetzy.tools.ecosystem.life_tools import (
    task_capture as _task_capture,
    task_complete as _task_complete,
    task_list as _task_list,
    task_today as _task_today,
)
from app.xninetzy.tools.internal.obsidian import (
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
from app.xninetzy.tools.internal.reminder import (
    reminder_cancel as _reminder_cancel,
    reminder_create as _reminder_create,
    reminder_list as _reminder_list,
)

# stdio MCP reserves stdout for protocol messages, so bootstrap stays silent.
assert isinstance(_MCP_PATH_OVERRIDES, dict)
_MCP_PRINCIPAL = mcp_principal()
_MCP_CONTEXT = _MCP_PRINCIPAL.as_tool_context()


mcp = FastMCP(
    "xninetzy",
    instructions=(
        "Akses Xninetzy OS milik owner lokal: Obsidian, knowledge, learning, HEBAT, "
        "life OS, task, reminder, research, dan workflow. Gunakan knowledge_answer "
        "untuk jawaban tersintesis dan tersitasi; knowledge_search hanya untuk inspeksi "
        "bukti. Semua path vault harus relatif terhadap vault."
    ),
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
    title: str, text: str, source_type: str = "manual_note", uri: str = ""
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
    title: str, description: str = "", priority: str = "medium", due_at: str = ""
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


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
