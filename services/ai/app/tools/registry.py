from __future__ import annotations

from langchain_core.tools import BaseTool

from app.tools.internal.calculation import calculate, calculate_percentage
from app.tools.internal.datetime_info import datetime_now
from app.tools.internal.obsidian import (
    obsidian_append,
    obsidian_create,
    obsidian_daily,
    obsidian_read,
    obsidian_save_note,
    obsidian_search,
)
from app.tools.internal.planning import (
    draft_workflow,
    generate_plan,
    idea_analysis,
    skill_discovery,
    task_breakdown,
)
from app.tools.internal.reminder import reminder_cancel, reminder_create, reminder_list
from app.tools.whatsapp.messaging import wa_pin_message, wa_send_text, wa_set_announce
from app.tools.hebat.tools import (
    hebat_login_status, hebat_start_login, hebat_sync_courses, hebat_list_courses,
    hebat_sync_course_activities, hebat_download_material, hebat_read_pdf,
    hebat_sync_assignments, hebat_get_assignment_detail,
    hebat_prepare_submission_from_whatsapp_file, hebat_upload_submission,
    hebat_cancel_submission, hebat_academic_digest, hebat_debug_login,
    hebat_login_status_verbose,
)
from app.tools.ecosystem.goal_tools import (
    goal_create, goal_list, goal_update_progress, goal_review,
)
from app.tools.ecosystem.life_tools import (
    task_capture, task_list, task_today, task_complete,
    money_add_transaction, money_summary,
    workout_log, workout_summary,
    habit_log, habit_today,
    daily_checkin, daily_review_generate, life_dashboard,
)
from app.tools.ecosystem.knowledge_tools import (
    knowledge_ingest_text, knowledge_ingest_file,
    knowledge_search, knowledge_answer,
    knowledge_list_sources, knowledge_rebuild_index,
)
from app.tools.ecosystem.research_tools import (
    web_search, youtube_search, deep_research_topic, research_light,
    research_create_subplans, research_web_collect, research_youtube_collect,
    research_rank_sources, research_generate_brief, research_save_brief,
    youtube_learning_search, youtube_playlist_finder, youtube_video_ranker,
)
from app.tools.ecosystem.helper_tools import helper_get, helper_generate_obsidian_docs
from app.skills.tools import skill_get, skill_list, skill_suggest_for_request
from app.hitl.approval_tools import (
    hitl_approve, hitl_get_status, hitl_list_pending, hitl_reject, hitl_request_approval,
)
from app.graph_rag.graph_tools import (
    graph_add_edge, graph_add_node, graph_explain_topic_map, graph_get_context,
    graph_link_note_to_topic, graph_link_research_to_roadmap, graph_search,
)
from app.learning.roadmap_tools import (
    learning_attach_resource, learning_create_roadmap, learning_generate_today_plan,
    learning_get_roadmap, learning_list_roadmaps, learning_review_week,
    learning_update_progress,
)
from app.notifications.admin_notifier import admin_notify_progress
from app.media.media_tools import (
    analyze_media, media_info, media_ingest_to_knowledge, media_read_document,
)
from app.rules.tools import (
    rule_add, rule_delete, rule_disable, rule_enable, rule_list, rule_search,
    rules_healthcheck,
)
from app.style.tools import style_reset, style_set, style_show
from app.memory.memory_tools import (
    memory_add, memory_forget, memory_get_context, memory_list, memory_search,
    memory_update_tool,
)
from app.lightning.tools import (
    lightning_approve, lightning_errors, lightning_feedback, lightning_healthcheck,
    lightning_improve, lightning_list_proposals, lightning_reject,
)

_ALL_TOOLS: list[BaseTool] | None = None


def get_all_tools() -> list[BaseTool]:
    global _ALL_TOOLS
    if _ALL_TOOLS is None:
        _ALL_TOOLS = [
            # General
            calculate, calculate_percentage, datetime_now,
            # Obsidian
            obsidian_search, obsidian_read, obsidian_create,
            obsidian_append, obsidian_daily, obsidian_save_note,
            # Reminders
            reminder_create, reminder_list, reminder_cancel,
            # Planning (legacy)
            skill_discovery, task_breakdown, idea_analysis, generate_plan, draft_workflow,
            # WhatsApp
            wa_pin_message, wa_set_announce, wa_send_text,
            # HEBAT / Moodle
            hebat_login_status, hebat_start_login, hebat_sync_courses, hebat_list_courses,
            hebat_sync_course_activities, hebat_download_material, hebat_read_pdf,
            hebat_sync_assignments, hebat_get_assignment_detail,
            hebat_prepare_submission_from_whatsapp_file, hebat_upload_submission,
            hebat_cancel_submission, hebat_academic_digest, hebat_debug_login,
            hebat_login_status_verbose,
            # Life OS — Goals
            goal_create, goal_list, goal_update_progress, goal_review,
            # Life OS — Tasks
            task_capture, task_list, task_today, task_complete,
            # Life OS — Money
            money_add_transaction, money_summary,
            # Life OS — Workout
            workout_log, workout_summary,
            # Life OS — Habits
            habit_log, habit_today,
            # Life OS — Daily
            daily_checkin, daily_review_generate, life_dashboard,
            # Knowledge OS
            knowledge_ingest_text, knowledge_ingest_file,
            knowledge_search, knowledge_answer,
            knowledge_list_sources, knowledge_rebuild_index,
            # Research
            web_search, youtube_search, research_light, research_create_subplans,
            research_web_collect, research_youtube_collect, research_rank_sources,
            research_generate_brief, research_save_brief, deep_research_topic,
            youtube_learning_search, youtube_playlist_finder, youtube_video_ranker,
            # Skills
            skill_list, skill_get, skill_suggest_for_request,
            # Learning Roadmap
            learning_create_roadmap, learning_list_roadmaps, learning_get_roadmap,
            learning_update_progress, learning_generate_today_plan,
            learning_review_week, learning_attach_resource,
            # Graph RAG
            graph_add_node, graph_add_edge, graph_search, graph_get_context,
            graph_link_research_to_roadmap, graph_link_note_to_topic,
            graph_explain_topic_map,
            # HITL
            hitl_request_approval, hitl_list_pending, hitl_approve,
            hitl_reject, hitl_get_status,
            # Admin notifications
            admin_notify_progress,
            # Media (WhatsApp documents)
            media_read_document, media_info, analyze_media, media_ingest_to_knowledge,
            # Rules & Style (defense system)
            rule_add, rule_list, rule_disable, rule_enable, rule_delete, rule_search,
            rules_healthcheck, style_set, style_show, style_reset,
            # Semantic memory
            memory_add, memory_search, memory_list, memory_update_tool,
            memory_forget, memory_get_context,
            # Lightning self-improvement
            lightning_feedback, lightning_list_proposals, lightning_improve,
            lightning_approve, lightning_reject, lightning_errors, lightning_healthcheck,
            # Helper
            helper_get, helper_generate_obsidian_docs,
        ]
    return _ALL_TOOLS


def get_tool_names() -> list[str]:
    return [t.name for t in get_all_tools()]


def get_tool_descriptions() -> list[dict]:
    return [
        {"name": t.name, "description": (t.description or "").split("\n")[0]}
        for t in get_all_tools()
    ]
