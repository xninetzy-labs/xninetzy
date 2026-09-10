from app.xninetzy.domains.it_learning.prompts import (
    IT_LEARNING_IDENTITY,
    IT_LEARNING_ROADMAP_PROMPT,
)
from app.xninetzy.domains.it_learning.skill_tree import IT_SKILL_TREE
from app.xninetzy.domains.it_learning.tools import (
    IT_LEARNING_TOOL_NAMES,
    get_it_learning_tools,
)
from app.xninetzy.domains.it_learning.workflows import (
    infer_it_learning_intent,
    is_it_learning_topic,
)


def test_it_skill_tree_has_ai_engineering():
    assert "ai_engineering" in IT_SKILL_TREE


def test_is_it_learning_topic_detects_rag():
    assert is_it_learning_topic("buat roadmap belajar RAG dan Graph RAG")


def test_infer_it_learning_intent_detects_roadmap():
    intent = infer_it_learning_intent("buat roadmap belajar backend")
    assert intent.wants_roadmap


def test_domain_prompts_importable():
    assert "IT Learning OS" in IT_LEARNING_IDENTITY
    assert "roadmap" in IT_LEARNING_ROADMAP_PROMPT.lower()


def test_domain_tools_entrypoint():
    tools = get_it_learning_tools()
    assert len(tools) == len(IT_LEARNING_TOOL_NAMES)
    names = {t.name for t in tools}
    assert "learning_create_roadmap" in names
