from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from app.xninetzy.interfaces.mcp_runtime import MCP_PATH_OVERRIDES

from app.xninetzy.core.coding_agents import (
    CodingAgentResult,
    _run_local_coding_agent,
    runtime_catalog,
)
from app.xninetzy.core.config import Settings, get_settings
from app.xninetzy.core.chat_failover import (
    ChatFailoverResult,
    _run_local_chat_failover,
)

assert isinstance(MCP_PATH_OVERRIDES, dict)


class HostAgentRunRequest(BaseModel):
    runtime: str = Field(min_length=1, max_length=32)
    task: str = Field(min_length=1, max_length=20_000)
    workspace: str = Field(default=".", max_length=400)
    user_id: str = Field(min_length=1, max_length=200)
    chat_id: str = Field(min_length=1, max_length=200)


class HostAgentRunResponse(BaseModel):
    run_id: str
    runtime: str
    status: str
    output: str = ""
    error: str = ""


class HostChatHistoryItem(BaseModel):
    type: str = Field(default="message", max_length=32)
    content: str = Field(default="", max_length=2_000)


class HostChatFailoverRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    user_id: str = Field(min_length=1, max_length=200)
    chat_id: str = Field(min_length=1, max_length=200)
    history: list[HostChatHistoryItem] = Field(default_factory=list, max_length=8)
    metadata: dict[str, object] = Field(default_factory=dict)


class HostChatFailoverResponse(BaseModel):
    run_id: str
    status: str
    output: str = ""
    error: str = ""


app = FastAPI(title="Xninetzy host coding-agent bridge")


def _bridge_token(settings: Settings) -> str:
    return settings.CODING_AGENT_HOST_BRIDGE_TOKEN.strip()


def require_bridge_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected = _bridge_token(get_settings())
    provided = (authorization or "").removeprefix("Bearer ").strip()
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Host bridge unauthorized")


@app.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    host_settings = settings.model_copy(
        update={
            "CODING_AGENT_EXECUTION_MODE": "local",
            "CODING_AGENT_WORKSPACE": settings.CODING_AGENT_HOST_WORKSPACE,
            "CODING_AGENT_ALLOWED_ROOT": settings.CODING_AGENT_HOST_ALLOWED_ROOT,
        }
    )
    return {
        "status": "ok",
        "execution_mode": "host",
        "runtimes": {
            name: info.installed
            for name, info in runtime_catalog(host_settings).items()
            if name != "internal"
        },
    }


@app.post(
    "/v1/run",
    response_model=HostAgentRunResponse,
    dependencies=[Depends(require_bridge_auth)],
)
async def run_host_agent(payload: HostAgentRunRequest) -> HostAgentRunResponse:
    settings = get_settings()
    if not settings.CODING_AGENT_ENABLED:
        raise HTTPException(status_code=503, detail="Coding agent dinonaktifkan")
    runtime = payload.runtime.strip().lower()
    if runtime not in {"codex", "claude-code", "opencode"}:
        raise HTTPException(status_code=400, detail="Runtime host tidak didukung")
    host_settings = settings.model_copy(
        update={
            "CODING_AGENT_EXECUTION_MODE": "local",
            "CODING_AGENT_WORKSPACE": settings.CODING_AGENT_HOST_WORKSPACE,
            "CODING_AGENT_ALLOWED_ROOT": settings.CODING_AGENT_HOST_ALLOWED_ROOT,
        }
    )
    result: CodingAgentResult = await _run_local_coding_agent(
        runtime,
        payload.task,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        workspace=payload.workspace,
        settings=host_settings,
    )
    return HostAgentRunResponse(
        run_id=result.run_id,
        runtime=result.runtime,
        status=result.status,
        output=result.output,
        error=result.error,
    )


@app.post(
    "/v1/chat-failover",
    response_model=HostChatFailoverResponse,
    dependencies=[Depends(require_bridge_auth)],
)
async def run_host_chat_failover(
    payload: HostChatFailoverRequest,
) -> HostChatFailoverResponse:
    settings = get_settings()
    if not settings.CHAT_FAILOVER_ENABLED:
        raise HTTPException(status_code=503, detail="Chat failover dinonaktifkan")
    host_settings = settings.model_copy(
        update={
            "CODING_AGENT_EXECUTION_MODE": "local",
            "CODING_AGENT_WORKSPACE": settings.CODING_AGENT_HOST_WORKSPACE,
            "CODING_AGENT_ALLOWED_ROOT": settings.CODING_AGENT_HOST_ALLOWED_ROOT,
        }
    )
    messages = []
    for item in payload.history:
        if item.type == "human":
            messages.append(HumanMessage(content=item.content))
        elif item.type == "ai":
            messages.append(AIMessage(content=item.content))
    result: ChatFailoverResult = await _run_local_chat_failover(
        payload.message,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        history=messages,
        metadata=payload.metadata,
        settings=host_settings,
    )
    return HostChatFailoverResponse(
        run_id=result.run_id,
        status=result.status,
        output=result.output,
        error=result.error,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.xninetzy.interfaces.host_agent_bridge:app",
        host=os.getenv("CODING_AGENT_HOST_BRIDGE_HOST", "127.0.0.1"),
        port=int(os.getenv("CODING_AGENT_HOST_BRIDGE_PORT", "8765")),
    )
