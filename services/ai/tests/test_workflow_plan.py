"""Offline tests for multi-action detection + deterministic plan decomposition."""

from __future__ import annotations

import pytest

from app.xninetzy.workflow.models import WorkflowActionType as T
from app.xninetzy.workflow.plan import build_workflow_plan, is_multi_action_request


def types_of(plan):
    return [a.type for a in plan.actions]


# ─── detection ───────────────────────────────────────────────────────────────

def test_simple_request_is_not_multi_action():
    assert not is_multi_action_request("ringkas dokumen ini")
    assert not is_multi_action_request("halo apa kabar")
    assert not is_multi_action_request("list course hebat saya")  # single domain
    assert not is_multi_action_request("")


def test_connector_plus_two_domains_is_multi_action():
    assert is_multi_action_request("riset materi graph rag lalu buat planning pengerjaan")
    assert is_multi_action_request("ambil tugas HEBAT course AI lalu buat planning")


def test_three_domains_without_connector_is_multi_action():
    assert is_multi_action_request("riset graph rag buat roadmap simpan ke obsidian")


# ─── decomposition: spec cases ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_case1_research_then_roadmap():
    plan = await build_workflow_plan("628", "carikan materi graph rag lengkap, lalu buat roadmap belajar")
    assert types_of(plan) == [
        T.DEEP_RESEARCH, T.KNOWLEDGE_INGEST, T.ROADMAP_CREATE, T.OBSIDIAN_SAVE, T.FINAL_SYNTHESIS,
    ]


@pytest.mark.asyncio
async def test_case2_hebat_assignment_then_planning():
    plan = await build_workflow_plan("628", "ambil tugas di HEBAT course AI lalu buat planning pengerjaannya")
    assert types_of(plan) == [
        T.HEBAT_SYNC, T.HEBAT_COURSE_DETAIL, T.HEBAT_ASSIGNMENT_DETAIL,
        T.HEBAT_DOWNLOAD_MATERIALS, T.TASK_PLANNING, T.OBSIDIAN_SAVE, T.FINAL_SYNTHESIS,
    ]
    # No knowledge ingest when there's no research/knowledge intent.
    assert T.KNOWLEDGE_INGEST not in types_of(plan)


@pytest.mark.asyncio
async def test_case3_research_from_hebat_file_then_plan():
    plan = await build_workflow_plan("628", "deep research materi dari file tugas HEBAT, lalu bikin plan pengerjaan")
    assert types_of(plan) == [
        T.HEBAT_ASSIGNMENT_DETAIL, T.HEBAT_DOWNLOAD_MATERIALS, T.KNOWLEDGE_INGEST,
        T.DEEP_RESEARCH, T.TASK_PLANNING, T.OBSIDIAN_SAVE, T.FINAL_SYNTHESIS,
    ]


@pytest.mark.asyncio
async def test_youtube_paper_obsidian_roadmap():
    plan = await build_workflow_plan(
        "628", "carikan youtube dan paper gratis untuk belajar security dasar, lalu buat roadmap dan simpan di obsidian"
    )
    t = types_of(plan)
    assert T.YOUTUBE_SEARCH in t and T.PAPER_SEARCH in t
    assert T.ROADMAP_CREATE in t and T.OBSIDIAN_SAVE in t
    assert t[-1] == T.FINAL_SYNTHESIS


@pytest.mark.asyncio
async def test_min_four_actions_for_hebat_download_roadmap():
    plan = await build_workflow_plan(
        "628", "ambil materi course AI di HEBAT, download filenya, pahami isinya, lalu buat roadmap belajar"
    )
    assert plan.action_count() >= 4


# ─── dependency ordering ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_actions_have_linear_dependencies():
    plan = await build_workflow_plan("628", "riset graph rag lalu buat planning lalu simpan obsidian")
    assert plan.actions[0].depends_on == []
    for prev, cur in zip(plan.actions, plan.actions[1:]):
        assert cur.depends_on == [prev.id]
    # ids are stable + unique
    ids = [a.id for a in plan.actions]
    assert len(ids) == len(set(ids))


@pytest.mark.asyncio
async def test_plan_metadata_populated():
    plan = await build_workflow_plan("628xyz", "riset graph rag lalu buat roadmap")
    assert plan.chat_id == "628xyz"
    assert plan.id and plan.created_at
    assert plan.title
    assert plan.actions[-1].type == T.FINAL_SYNTHESIS
