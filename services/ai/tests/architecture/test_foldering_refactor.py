"""Verifies the app.xninetzy namespace refactor and backward-compat adapters.

New code must import from app.xninetzy.*; legacy import paths must keep working
via the thin adapters generated at the old locations.
"""
from __future__ import annotations

import importlib

import pytest

NEW_MODULES = [
    "app.xninetzy.agent.graph",
    "app.xninetzy.workflow.executor",
    "app.xninetzy.domains.it_learning.roadmap_planner",
    "app.xninetzy.os.knowledge.rag",
    "app.xninetzy.os.academic.hebat.tools",
    "app.xninetzy.tools.registry",
    "app.xninetzy.context.builder",
]

# old path -> new module it should alias to
ADAPTERS = {
    "app.learning.roadmap_planner": "app.xninetzy.domains.it_learning.roadmap_planner",
    "app.knowledge.rag": "app.xninetzy.os.knowledge.rag",
    "app.tools.hebat.tools": "app.xninetzy.os.academic.hebat.tools",
    "app.agent.workflow_executor": "app.xninetzy.workflow.executor",
    "app.obsidian.config": "app.xninetzy.os.notes.obsidian_config",
    "app.wa_tools.client": "app.xninetzy.interfaces.whatsapp.client",
    "app.planning.goal_manager": "app.xninetzy.os.life.goal_manager",
}


@pytest.mark.parametrize("mod", NEW_MODULES)
def test_new_namespace_imports(mod: str) -> None:
    assert importlib.import_module(mod) is not None


@pytest.mark.parametrize("old,new", list(ADAPTERS.items()))
def test_legacy_adapter_aliases_new_module(old: str, new: str) -> None:
    old_mod = importlib.import_module(old)
    new_mod = importlib.import_module(new)
    # Adapter aliases sys.modules so the legacy path resolves to the new module.
    assert old_mod.__name__ == new_mod.__name__


def test_it_learning_skill_tree() -> None:
    from app.xninetzy.domains.it_learning.skill_tree import IT_SKILL_TREE, branch_for

    assert "ai_engineering" in IT_SKILL_TREE
    assert branch_for("rag") == "ai_engineering"


def test_domain_classifier_prioritises_it_learning() -> None:
    from app.xninetzy.context.domain_classifier import classify_domain

    assert classify_domain("bantu aku belajar python backend") == "it_learning"
    assert classify_domain("cek tugas di hebat") == "academic"
    assert classify_domain("halo apa kabar") == "general"


def test_tools_registry_unchanged_surface() -> None:
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    # Spot-check tools from across the OS/domain boundary still register.
    for expected in ("calculate", "learning_create_roadmap", "hebat_login_status",
                     "knowledge_search", "workflow_status"):
        assert expected in names
