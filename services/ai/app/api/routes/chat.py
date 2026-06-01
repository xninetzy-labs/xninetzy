from __future__ import annotations

from fastapi import APIRouter

from app.agent.graph import get_compiled_graph
from app.ecosystem.command_router import parse_command
from app.memory.chat_store import ChatStore
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


async def _invoke_tool_directly(tool_name: str, kwargs: dict, chat_id: str) -> str:
    """Invoke a single tool directly, bypassing LangGraph (for slash commands)."""
    from app.tools.registry import get_all_tools
    tools = {t.name: t for t in get_all_tools()}
    tool = tools.get(tool_name)
    if not tool:
        return f"Command tidak dikenali: `{tool_name}`"
    try:
        kwargs.setdefault("chat_id", chat_id)
        result = await tool.ainvoke(kwargs)
        return str(result)
    except Exception as e:
        return f"Error menjalankan command: {e}"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Check for slash command (deterministic routing, skip LangGraph)
    tool_name, kwargs = parse_command(request.message)
    if tool_name:
        reply = await _invoke_tool_directly(tool_name, kwargs, request.chat_id)
        return ChatResponse(reply=reply)

    # 2. Normal LangGraph flow
    store = ChatStore()
    history = store.get_recent(request.chat_id)

    initial_state = {
        "chat_id": request.chat_id,
        "sender_id": request.sender_id,
        "sender_name": request.sender_name,
        "message": request.message,
        "chat_type": request.chat_type,
        "group_name": request.group_name,
        "metadata": request.metadata,
        "messages": history,
        "route": "",
        "clarification_question": None,
        "response": "",
    }

    graph = get_compiled_graph()
    result = await graph.ainvoke(initial_state)

    new_messages = result["messages"][len(history):]
    if new_messages:
        store.save_messages(request.chat_id, new_messages)

    return ChatResponse(reply=result["response"])
