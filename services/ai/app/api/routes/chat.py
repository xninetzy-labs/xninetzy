from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService, get_llm_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    reply = await llm_service.generate_reply(request)
    return ChatResponse(reply=reply)
