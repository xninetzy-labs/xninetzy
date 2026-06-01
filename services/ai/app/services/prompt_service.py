from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Literal

from app.core.config import Settings

PromptId = Literal[
    "PROMPT_SYSTEM_MVP",
    "PROMPT_PREPROCESSOR",
    "PROMPT_MEMORY_RETRIEVER",
    "PROMPT_INTENT_ROUTER",
    "PROMPT_TOOL_AGENT",
    "PROMPT_TOOL_RESULT_PROCESSOR",
    "PROMPT_CASUAL_RESPONSE",
    "PROMPT_LEARNING_RESPONSE",
    "PROMPT_TASK_RESPONSE",
    "PROMPT_GROUP_MGMT_RESPONSE",
    "PROMPT_MEDIA_RESPONSE",
    "PROMPT_CS_RESPONSE",
    "PROMPT_GREETING_HANDLER",
    "PROMPT_CLARIFICATION_HANDLER",
    "PROMPT_CONTINUATION_HANDLER",
    "PROMPT_ADMIN_CONFIRMATION",
    "PROMPT_RESPONSE_SYNTHESIZER",
    "PROMPT_MEMORY_SUMMARIZER",
    "PROMPT_MEMORY_SQLITE_FORMATTER",
    "PROMPT_ERROR_HANDLER",
    "PROMPT_TENANT_CUSTOMIZER",
]

PROMPTS_FILE = Path(__file__).resolve().parents[1] / "prompts" / "prompts.md"


@dataclass(frozen=True)
class PromptTemplate:
    id: PromptId
    node: str
    purpose: str
    template: str


PROMPT_META: dict[PromptId, tuple[str, str]] = {
    "PROMPT_SYSTEM_MVP": ("chat_mvp", "System prompt untuk endpoint chat MVP."),
    "PROMPT_PREPROCESSOR": ("preprocess_node", "Normalisasi pesan masuk dan ekstraksi metadata."),
    "PROMPT_MEMORY_RETRIEVER": ("memory_retrieve_node", "Rencana query FAISS dan SQLite."),
    "PROMPT_INTENT_ROUTER": ("intent_router_node", "Klasifikasi intent dan routing LangGraph."),
    "PROMPT_TOOL_AGENT": ("tool_agent_node", "Agent ReAct untuk MCP tools."),
    "PROMPT_TOOL_RESULT_PROCESSOR": ("tool_result_node", "Interpretasi hasil tool."),
    "PROMPT_CASUAL_RESPONSE": ("response_node.casual", "Respons santai."),
    "PROMPT_LEARNING_RESPONSE": ("response_node.learning", "Respons belajar."),
    "PROMPT_TASK_RESPONSE": ("response_node.task_management", "Respons task management."),
    "PROMPT_GROUP_MGMT_RESPONSE": ("response_node.group_management", "Respons manajemen grup."),
    "PROMPT_MEDIA_RESPONSE": ("response_node.media_action", "Respons media."),
    "PROMPT_CS_RESPONSE": ("response_node.customer_service", "Respons customer service."),
    "PROMPT_GREETING_HANDLER": ("greeting_node", "Sapaan dan farewell."),
    "PROMPT_CLARIFICATION_HANDLER": ("clarify_node", "Klarifikasi pesan ambigu."),
    "PROMPT_CONTINUATION_HANDLER": ("continuation_node", "Lanjutan percakapan."),
    "PROMPT_ADMIN_CONFIRMATION": ("admin_confirm_node", "Konfirmasi aksi admin sensitif."),
    "PROMPT_RESPONSE_SYNTHESIZER": ("synthesizer_node", "Finalisasi respons WhatsApp."),
    "PROMPT_MEMORY_SUMMARIZER": ("memory_summary_node", "Ringkasan untuk FAISS."),
    "PROMPT_MEMORY_SQLITE_FORMATTER": ("memory_sqlite_node", "Format record SQLite."),
    "PROMPT_ERROR_HANDLER": ("error_node", "Respons error user-friendly."),
    "PROMPT_TENANT_CUSTOMIZER": ("tenant_init_node", "Adaptasi prompt tenant."),
}

NODE_PROMPT_MAP: dict[str, PromptId] = {
    node: prompt_id
    for prompt_id, (node, _) in PROMPT_META.items()
    if prompt_id != "PROMPT_SYSTEM_MVP"
}


def build_system_prompt(settings: Settings) -> str:
    return render_prompt(
        get_prompt_template("PROMPT_SYSTEM_MVP").template,
        bot_name=settings.BOT_NAME,
        bot_owner=settings.BOT_OWNER,
    )


def get_prompt_template(prompt_id: PromptId) -> PromptTemplate:
    node, purpose = PROMPT_META[prompt_id]
    template = load_prompt_templates()[prompt_id]
    return PromptTemplate(id=prompt_id, node=node, purpose=purpose, template=template)


def get_prompt_for_node(node_name: str) -> PromptTemplate:
    return get_prompt_template(NODE_PROMPT_MAP[node_name])


def render_prompt(template: str, **values: object) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def prompt_variables(template: str) -> set[str]:
    return set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template))


@lru_cache
def load_prompt_templates() -> dict[PromptId, str]:
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPTS_FILE}")

    prompts = _parse_markdown_prompts(PROMPTS_FILE.read_text(encoding="utf-8"))
    missing = set(PROMPT_META) - set(prompts)
    if missing:
        raise ValueError(f"Missing prompt sections in {PROMPTS_FILE}: {sorted(missing)}")

    return prompts


def _parse_markdown_prompts(markdown: str) -> dict[PromptId, str]:
    prompts: dict[PromptId, str] = {}
    lines = markdown.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("## PROMPT_"):
            prompt_id = line.removeprefix("## ").strip()
            index = _find_next_fence(lines, index + 1)
            if index >= len(lines):
                raise ValueError(f"Prompt {prompt_id} does not contain a fenced template block")

            fence = lines[index].strip()
            fence_lang = fence.removeprefix("```").strip()
            index += 1
            block: list[str] = []

            while index < len(lines) and lines[index].strip() != "```":
                block.append(lines[index])
                index += 1

            if index >= len(lines):
                raise ValueError(f"Prompt {prompt_id} has an unterminated fenced block")

            if not fence_lang.startswith("prompt"):
                raise ValueError(f"Prompt {prompt_id} must use a ```prompt fenced block")

            prompts[prompt_id] = "\n".join(block).strip()

        index += 1

    return prompts  # type: ignore[return-value]


def _find_next_fence(lines: list[str], start: int) -> int:
    for index in range(start, len(lines)):
        if lines[index].strip().startswith("```"):
            return index
    return len(lines)
