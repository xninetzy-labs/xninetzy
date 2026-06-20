from __future__ import annotations

from fastapi import APIRouter

from app.xninetzy.os.memory.chat_store import ChatStore
from app.xninetzy.schemas.routing import ToolInvokeRequest
from app.xninetzy.tools.registry import get_tool_descriptions, get_all_tools

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/tools")
async def list_tools() -> dict:
    """List all available tools with their descriptions."""
    return {"tools": get_tool_descriptions()}


@router.get("/memory/{chat_id}")
async def get_memory(chat_id: str, limit: int = 20) -> dict:
    """View recent chat history for a given chat_id."""
    store = ChatStore()
    messages = store.get_recent(chat_id, limit=limit)
    return {
        "chat_id": chat_id,
        "count": len(messages),
        "messages": [
            {"role": type(m).__name__, "content": m.content}
            for m in messages
        ],
    }


@router.delete("/memory/{chat_id}")
async def clear_memory(chat_id: str) -> dict:
    """Clear chat history for a given chat_id."""
    ChatStore().clear(chat_id)
    return {"status": "cleared", "chat_id": chat_id}


@router.post("/invoke-tool/{tool_name}")
async def invoke_tool(tool_name: str, request: ToolInvokeRequest) -> dict:
    """Directly invoke a tool by name for testing."""
    tools = {t.name: t for t in get_all_tools()}
    if tool_name not in tools:
        return {"error": f"Tool '{tool_name}' not found", "available": list(tools.keys())}
    try:
        result = await tools[tool_name].ainvoke(request.args)
        return {"tool": tool_name, "result": result}
    except Exception as e:
        return {"tool": tool_name, "error": str(e)}
