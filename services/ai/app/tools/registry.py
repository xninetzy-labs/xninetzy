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
    hebat_cancel_submission, hebat_academic_digest,
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
    web_search, youtube_search, deep_research_topic,
)
from app.tools.ecosystem.helper_tools import helper_get, helper_generate_obsidian_docs

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
            hebat_cancel_submission, hebat_academic_digest,
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
            web_search, youtube_search, deep_research_topic,
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
