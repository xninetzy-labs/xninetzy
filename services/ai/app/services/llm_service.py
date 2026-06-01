from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.memory.simple_memory import append_message, get_history
from app.schemas.chat import ChatRequest
from app.services.prompt_service import build_system_prompt
from app.skills.base import SkillInput
from app.skills.executor import execute_skill
from app.skills.router import route_skill
from app.skills.tools.date_tool import DateTool


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
        skill_reply = await self._try_generate_skill_reply(request)
        if skill_reply:
            append_message(request.chat_id, "user", request.message)
            append_message(request.chat_id, "assistant", skill_reply)
            return skill_reply

        messages = [SystemMessage(content=build_system_prompt(self.settings))]
        messages.extend(self._history_messages(request.chat_id))
        
        now = DateTool().now()
        quoted_text = request.metadata.get("quotedMessageText")
        quoted_context = f"\nMembalas pesan: \"{quoted_text}\"" if quoted_text else ""
        
        messages.append(
            HumanMessage(
                content=(
                    f"Nama pengirim: {request.sender_name or request.sender_id}\n"
                    f"Tipe chat: {request.chat_type}\n"
                    f"Nama grup: {request.group_name or '-'}\n"
                    f"Tanggal sekarang: {now['human_datetime']}\n"
                    f"Timestamp ISO: {now['iso']}{quoted_context}\n"
                    f"Pesan: {request.message}"
                )
            )
        )

        response = await self.llm.ainvoke(messages)
        reply = str(response.content).strip()

        append_message(request.chat_id, "user", request.message)
        append_message(request.chat_id, "assistant", reply)

        return reply

    async def _try_generate_skill_reply(self, request: ChatRequest) -> str | None:
        if not self.settings.SKILLS_ENABLED:
            return None

        route = route_skill(request.message)
        if not route.needs_skill or not route.skill_name or route.requires_confirmation:
            return None

        output = await execute_skill(
            route.skill_name,
            SkillInput(
                chat_id=request.chat_id,
                sender_id=request.sender_id,
                message=request.message,
                metadata={**request.metadata, **route.skill_args, "action": route.skill_action},
            ),
            action=route.skill_action,
        )
        if output.user_facing_text:
            return output.user_facing_text
        return None

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
