from __future__ import annotations

import ipaddress

from mcp.server.fastmcp import FastMCP

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

init_db()
run_migrations()

assert isinstance(_MCP_PATH_OVERRIDES, dict)
_MCP_PRINCIPAL = mcp_principal()


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
        raise ValueError(
            f"XNINETZY_MCP_HTTP_HOST must be loopback for current build, got: {_HTTP_HOST!r}. "
            "Streamable HTTP requires real auth (OAuth 2.1 + Resource Indicators) "
            "before exposing beyond localhost."
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
