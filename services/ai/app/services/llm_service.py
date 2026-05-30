from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.memory.simple_memory import append_message, get_history
from app.schemas.chat import ChatRequest
from app.services.prompt_service import build_system_prompt


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.3,
        )

    async def generate_reply(self, request: ChatRequest) -> str:
        messages = [SystemMessage(content=build_system_prompt(self.settings))]
        messages.extend(self._history_messages(request.chat_id))
        messages.append(
            HumanMessage(
                content=(
                    f"Nama pengirim: {request.sender_name or request.sender_id}\n"
                    f"Tipe chat: {request.chat_type}\n"
                    f"Nama grup: {request.group_name or '-'}\n"
                    f"Pesan: {request.message}"
                )
            )
        )

        response = await self.llm.ainvoke(messages)
        reply = str(response.content).strip()

        append_message(request.chat_id, "user", request.message)
        append_message(request.chat_id, "assistant", reply)

        return reply

    @staticmethod
    def _history_messages(chat_id: str) -> list[HumanMessage | AIMessage]:
        result: list[HumanMessage | AIMessage] = []
        for item in get_history(chat_id):
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
        return result


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService(get_settings())
