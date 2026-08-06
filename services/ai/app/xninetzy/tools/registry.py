"""Central tools registry for Xninetzy (IT Learning OS).

Tools are grouped by category inside ``get_all_tools()``:
core/general · it-learning roadmap · knowledge · research · notes/obsidian ·
academic/hebat · life · reminder · whatsapp · media · graph · hitl · rules/style ·
memory · lightning · helper.

``get_all_tools()`` returns the full, unchanged tool set — grouping is
organizational only.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool

from app.xninetzy.tools.internal.calculation import calculate, calculate_percentage
from app.xninetzy.tools.internal.datetime_info import datetime_now
from app.xninetzy.tools.internal.obsidian import (
    obsidian_add_tags,
    obsidian_append,
    obsidian_backlinks,
    obsidian_create,
    obsidian_create_folder,
    obsidian_daily,
    obsidian_generate_moc,
    obsidian_headings,
    obsidian_list,
    obsidian_read,
    obsidian_save_note,
    obsidian_search,
    obsidian_search_health,
    obsidian_set_frontmatter,
    obsidian_todos,
    obsidian_update_section,
)
from app.xninetzy.tools.internal.obsidian_organization import (
    obsidian_folder_status,
    obsidian_moc_refresh,
    obsidian_organize_apply,
    obsidian_organize_preview,
    obsidian_verify,
    obsidian_vault_init,
)
from app.xninetzy.tools.internal.planning import (
    draft_workflow,
    generate_plan,
    idea_analysis,
    skill_discovery,
    task_breakdown,
)
from app.xninetzy.tools.internal.reminder import (
    reminder_cancel,
    reminder_create,
    reminder_list,
)
from app.xninetzy.interfaces.whatsapp.messaging import (
    wa_forward_media_to_admin,
    wa_pin_message,
    wa_send_admin_verification,
    wa_send_audio,
    wa_send_document,
    wa_send_image,
    wa_send_ptt,
    wa_send_sticker,
    wa_send_text,
    wa_send_video,
    wa_set_announce,
)
from app.xninetzy.os.academic.hebat.tools import (
    hebat_login_status,
    hebat_start_login,
    hebat_sync_courses,
    hebat_list_courses,
    hebat_sync_course_activities,
    hebat_download_material,
    hebat_read_pdf,
    hebat_sync_assignments,
    hebat_get_assignment_detail,
    hebat_prepare_submission_from_whatsapp_file,
    hebat_upload_submission,
    hebat_cancel_submission,
    hebat_remove_submission,
    hebat_academic_digest,
    hebat_debug_login,
    hebat_login_status_verbose,
)
from app.xninetzy.os.academic.mahasiswa_portal.tools import (
    portal_academic_status,
    portal_current_krs,
    portal_info,
    portal_krs_capabilities,
    portal_krs_watcher_status,
    portal_krs_watcher_start,
    portal_krs_watcher_stop,
    portal_krs_war_arm,
    portal_krs_war_disarm,
    portal_krs_war_dry_run,
    portal_krs_war_plan,
    portal_krs_war_status,
    portal_login_cancel,
    portal_login_start,
    portal_login_submit_captcha,
    portal_logout,
    portal_navigation,
    portal_profile,
    portal_grade_changes,
    portal_grades,
    portal_grade_token_submit,
    portal_schedule,
    portal_session_status,
    uacc_info,
    uacc_login_cancel,
    uacc_login_start,
    uacc_login_submit_captcha,
    uacc_logout,
    uacc_session_status,
)
from app.xninetzy.os.academic.qa_portal.tools import (
    qa_fill_kuesioner,
    qa_list_kuesioner,
)
from app.xninetzy.os.jobs.tools import os_job_status
from app.xninetzy.os.policy.tools import action_policy_evaluate
from app.xninetzy.os.inbox.tools import os_capture, os_inbox, os_today, os_triage
from app.xninetzy.tools.ecosystem.web_analysis_tools import (
    web_analysis_refresh,
    web_analysis_status,
    web_analysis_catalog,
    web_discover,
    web_fetch,
)
from app.xninetzy.tools.ecosystem.goal_tools import (
    goal_create,
    goal_list,
    goal_update_progress,
    goal_review,
)
from app.xninetzy.tools.ecosystem.life_tools import (
    task_capture,
    task_list,
    task_today,
    task_complete,
    money_add_transaction,
    money_summary,
    workout_log,
    workout_summary,
    habit_log,
    habit_today,
    daily_checkin,
    daily_review_generate,
    life_dashboard,
)
from app.xninetzy.tools.ecosystem.knowledge_tools import (
    knowledge_ingest_text,
    knowledge_ingest_file,
    knowledge_search,
    knowledge_answer,
    knowledge_list_sources,
    knowledge_rebuild_index,
)
from app.xninetzy.tools.ecosystem.knowledge_eval_tools import knowledge_evaluate_retrieval
from app.xninetzy.tools.ecosystem.unified_search_tools import unified_search
from app.xninetzy.tools.ecosystem.document_tools import (
    document_analyze,
    document_ingest,
    document_overview,
    document_tables,
    document_catalog,
)
from app.xninetzy.tools.ecosystem.research_tools import (
    web_search,
    youtube_search,
    deep_research_topic,
    deep_research_get,
    deep_research_list,
    research_light,
    research_create_subplans,
    research_web_collect,
    research_youtube_collect,
    research_rank_sources,
    research_generate_brief,
    research_save_brief,
    youtube_learning_search,
    youtube_playlist_finder,
    youtube_video_ranker,
)
from app.xninetzy.tools.ecosystem.helper_tools import (
    helper_get,
    helper_generate_obsidian_docs,
)
from app.xninetzy.tools.ecosystem.tool_catalog_tools import tool_catalog
from app.xninetzy.tools.ecosystem.ai_runtime_tools import (
    ai_provider_list,
    ai_provider_status,
    ai_provider_use,
    coding_agent_list,
    coding_agent_status,
    coding_agent_use,
    coding_agent_run,
)
from app.xninetzy.tools.ecosystem.pixelrag_tools import (
    pixelrag_capture,
    pixelrag_health,
    pixelrag_local_start,
    pixelrag_search_local,
    pixelrag_search_public,
)
from app.xninetzy.skills.tools import (
    skill_get,
    skill_install,
    skill_list,
    skill_resource_list,
    skill_resource_read,
    skill_suggest_for_request,
    skill_validate,
    skill_healthcheck,
)
from app.xninetzy.os.hitl.approval_tools import (
    hitl_approve,
    hitl_get_status,
    hitl_list_pending,
    hitl_reject,
    hitl_request_approval,
)
from app.xninetzy.os.graph.graph_tools import (
    graph_add_edge,
    graph_add_node,
    graph_explain_topic_map,
    graph_get_context,
    graph_link_note_to_topic,
    graph_link_research_to_roadmap,
    graph_search,
)
from app.xninetzy.os.graph.v3.graph_tools_v3 import (
    graph_v3_link,
    graph_v3_neighborhood,
    graph_v3_path,
    graph_v3_rebuild,
    graph_v3_search,
    graph_v3_stats,
    graph_v3_upsert_node,
)
from app.xninetzy.domains.it_learning.roadmap_tools import (
    learning_attach_resource,
    learning_create_roadmap,
    learning_generate_today_plan,
    learning_get_roadmap,
    learning_get_study_progress,
    learning_list_roadmaps,
    learning_review_week,
    learning_update_progress,
)
from app.xninetzy.domains.it_learning.study_session import (
    learning_complete_study_session,
    learning_list_study_sessions,
    learning_start_study_session,
)
from app.xninetzy.domains.it_learning.concept_graph import (
    learning_define_concept,
    learning_get_concept_map,
    learning_record_concept_evidence,
)
from app.xninetzy.domains.it_learning.recall import (
    learning_create_recall_card,
    learning_due_recall,
    learning_submit_recall_answer,
)
from app.xninetzy.os.notifications.admin_notifier import admin_notify_progress
from app.xninetzy.interfaces.media.media_tools import (
    analyze_media,
    media_info,
    media_ingest_to_knowledge,
    media_read_audio,
    media_read_document,
    media_read_image,
)
from app.xninetzy.workflow.tools import (
    workflow_status,
    workflow_latest,
    workflow_resume,
    workflow_cancel,
)
from app.xninetzy.os.rules.tools import (
    rule_add,
    rule_delete,
    rule_disable,
    rule_enable,
    rule_list,
    rule_search,
    rules_healthcheck,
)
from app.xninetzy.os.style.tools import style_reset, style_set, style_show
from app.xninetzy.os.memory.memory_tools import (
    memory_add,
    memory_forget,
    memory_get_context,
    memory_list,
    memory_search,
    memory_update_tool,
)
from app.xninetzy.os.lightning.tools import (
    lightning_approve,
    lightning_errors,
    lightning_episode_finish,
    lightning_episode_start,
    lightning_feedback,
    lightning_healthcheck,
    lightning_improve,
    lightning_list_proposals,
    lightning_propose_improvement,
    lightning_record_action,
    lightning_record_outcome,
    lightning_regression_check,
    lightning_reject,
    lightning_reward_summary,
    lightning_strategy_rank,
)
from app.xninetzy.interfaces.external_mcp import EXTERNAL_MCP_TOOLS

_ALL_TOOLS: list[BaseTool] | None = None


def get_all_tools() -> list[BaseTool]:
    global _ALL_TOOLS
    if _ALL_TOOLS is None:
        _ALL_TOOLS = [
            # General
            calculate,
            calculate_percentage,
            datetime_now,
            *EXTERNAL_MCP_TOOLS,
            # Obsidian
            obsidian_search_health,
            obsidian_search,
            obsidian_read,
            obsidian_create,
            obsidian_append,
            obsidian_daily,
            obsidian_save_note,
            obsidian_list,
            obsidian_create_folder,
            obsidian_update_section,
            obsidian_todos,
            obsidian_backlinks,
            obsidian_headings,
            obsidian_generate_moc,
            obsidian_add_tags,
            obsidian_set_frontmatter,
            obsidian_vault_init,
            obsidian_folder_status,
            obsidian_organize_preview,
            obsidian_organize_apply,
            obsidian_moc_refresh,
            obsidian_verify,
            # Reminders
            reminder_create,
            reminder_list,
            reminder_cancel,
            # Planning (legacy)
            skill_discovery,
            task_breakdown,
            idea_analysis,
            generate_plan,
            draft_workflow,
            # WhatsApp
            wa_pin_message,
            wa_set_announce,
            wa_send_text,
            wa_send_image,
            wa_send_document,
            wa_send_audio,
            wa_send_ptt,
            wa_send_video,
            wa_send_sticker,
            wa_send_admin_verification,
            wa_forward_media_to_admin,
            # HEBAT / Moodle
            hebat_login_status,
            hebat_start_login,
            hebat_sync_courses,
            hebat_list_courses,
            hebat_sync_course_activities,
            hebat_download_material,
            hebat_read_pdf,
            hebat_sync_assignments,
            hebat_get_assignment_detail,
            hebat_prepare_submission_from_whatsapp_file,
            hebat_upload_submission,
            hebat_cancel_submission,
            hebat_remove_submission,
            hebat_academic_digest,
            hebat_debug_login,
            hebat_login_status_verbose,
            # Local-owner academic portal / structural web analysis
            web_analysis_status,
            web_analysis_catalog,
            web_analysis_refresh,
            web_discover,
            web_fetch,
            portal_info,
            portal_profile,
            portal_academic_status,
            portal_current_krs,
            portal_navigation,
            portal_krs_capabilities,
            portal_grade_changes,
            portal_grades,
            portal_grade_token_submit,
            portal_schedule,
            portal_krs_watcher_status,
            portal_krs_watcher_start,
            portal_krs_watcher_stop,
            portal_krs_war_status,
            portal_krs_war_arm,
            portal_krs_war_disarm,
            portal_krs_war_plan,
            portal_krs_war_dry_run,
            portal_login_start,
            portal_login_submit_captcha,
            portal_login_cancel,
            portal_session_status,
            portal_logout,
            uacc_info,
            uacc_login_start,
            uacc_login_submit_captcha,
            uacc_login_cancel,
            uacc_session_status,
            uacc_logout,
            # QA portal (qa.unair.ac.id)
            qa_list_kuesioner,
            qa_fill_kuesioner,
            # Life OS — Goals
            goal_create,
            goal_list,
            goal_update_progress,
            goal_review,
            # Life OS — Tasks
            task_capture,
            task_list,
            task_today,
            task_complete,
            # Life OS — Money
            money_add_transaction,
            money_summary,
            # Life OS — Workout
            workout_log,
            workout_summary,
            # Life OS — Habits
            habit_log,
            habit_today,
            # Life OS — Daily
            daily_checkin,
            daily_review_generate,
            life_dashboard,
            os_job_status,
            action_policy_evaluate,
            os_capture,
            os_inbox,
            os_triage,
            os_today,
            # Knowledge OS
            knowledge_ingest_text,
            knowledge_ingest_file,
            knowledge_search,
            knowledge_answer,
            knowledge_list_sources,
            knowledge_rebuild_index,
            knowledge_evaluate_retrieval,
            unified_search,
            # Document extraction (router-based)
            document_analyze,
            document_ingest,
            document_overview,
            document_tables,
            document_catalog,
            # Research
            web_search,
            youtube_search,
            research_light,
            research_create_subplans,
            research_web_collect,
            research_youtube_collect,
            research_rank_sources,
            research_generate_brief,
            research_save_brief,
            deep_research_topic,
            deep_research_get,
            deep_research_list,
            youtube_learning_search,
            youtube_playlist_finder,
            youtube_video_ranker,
            # PixelRAG (visual RAG)
            pixelrag_capture,
            pixelrag_search_public,
            pixelrag_search_local,
            pixelrag_health,
            pixelrag_local_start,
            # Skills
            skill_list,
            skill_get,
            skill_suggest_for_request,
            skill_validate,
            skill_install,
            skill_resource_list,
            skill_resource_read,
            skill_healthcheck,
            # Learning Roadmap
            learning_create_roadmap,
            learning_list_roadmaps,
            learning_get_roadmap,
            learning_update_progress,
            learning_generate_today_plan,
            learning_get_study_progress,
            learning_review_week,
            learning_attach_resource,
            learning_start_study_session,
            learning_complete_study_session,
            learning_list_study_sessions,
            learning_define_concept,
            learning_record_concept_evidence,
            learning_get_concept_map,
            learning_create_recall_card,
            learning_due_recall,
            learning_submit_recall_answer,
            # Graph RAG
            graph_add_node,
            graph_add_edge,
            graph_search,
            graph_get_context,
            graph_link_research_to_roadmap,
            graph_link_note_to_topic,
            graph_explain_topic_map,
            # Graph RAG V3 (tri-store)
            graph_v3_upsert_node,
            graph_v3_link,
            graph_v3_search,
            graph_v3_neighborhood,
            graph_v3_path,
            graph_v3_stats,
            graph_v3_rebuild,
            # HITL
            hitl_request_approval,
            hitl_list_pending,
            hitl_approve,
            hitl_reject,
            hitl_get_status,
            # Admin notifications
            admin_notify_progress,
            # Media (WhatsApp documents)
            media_read_document,
            media_read_image,
            media_read_audio,
            media_info,
            analyze_media,
            media_ingest_to_knowledge,
            # Multi-action workflow
            workflow_status,
            workflow_latest,
            workflow_resume,
            workflow_cancel,
            # Rules & Style (defense system)
            rule_add,
            rule_list,
            rule_disable,
            rule_enable,
            rule_delete,
            rule_search,
            rules_healthcheck,
            style_set,
            style_show,
            style_reset,
            # Semantic memory
            memory_add,
            memory_search,
            memory_list,
            memory_update_tool,
            memory_forget,
            memory_get_context,
            # Lightning self-improvement
            lightning_episode_start,
            lightning_record_action,
            lightning_record_outcome,
            lightning_episode_finish,
            lightning_feedback,
            lightning_reward_summary,
            lightning_strategy_rank,
            lightning_regression_check,
            lightning_propose_improvement,
            lightning_list_proposals,
            lightning_improve,
            lightning_approve,
            lightning_reject,
            lightning_errors,
            lightning_healthcheck,
            # AI provider and local coding-agent runtime
            ai_provider_list,
            ai_provider_status,
            ai_provider_use,
            coding_agent_list,
            coding_agent_status,
            coding_agent_use,
            coding_agent_run,
            # Helper
            helper_get,
            helper_generate_obsidian_docs,
            tool_catalog,
        ]
    return _ALL_TOOLS


def get_tool_names() -> list[str]:
    return [t.name for t in get_all_tools()]


def get_tool_descriptions() -> list[dict]:
    return [
        {"name": t.name, "description": (t.description or "").split("\n")[0]}
        for t in get_all_tools()
    ]


def get_tool_groups() -> dict[str, list[str]]:
    """Tool names grouped by domain / support OS (for docs and routing hints).

    Organizational only — does not affect what ``get_all_tools()`` returns. IT
    Learning is the primary domain; the rest are support OS + interfaces.
    """
    return {
        "core": ["calculate", "calculate_percentage", "datetime_now"],
        "os_kernel": ["os_capture", "os_inbox", "os_triage", "os_today", "os_job_status"],
        "policy": ["action_policy_evaluate"],
        "ai_runtime": [
            "ai_provider_list",
            "ai_provider_status",
            "ai_provider_use",
            "coding_agent_list",
            "coding_agent_status",
            "coding_agent_use",
            "coding_agent_run",
        ],
        "it_learning": [
            "learning_create_roadmap",
            "learning_list_roadmaps",
            "learning_generate_today_plan",
            "learning_get_study_progress",
            "learning_review_week",
            "learning_start_study_session",
            "learning_complete_study_session",
            "learning_list_study_sessions",
        ],
        "knowledge": ["knowledge_ingest_text", "knowledge_search", "knowledge_answer", "knowledge_evaluate_retrieval"],
        "unified_search": ["unified_search"],
        "pixelrag": [
            "pixelrag_capture",
            "pixelrag_search_public",
            "pixelrag_search_local",
            "pixelrag_health",
            "pixelrag_local_start",
        ],
        "web_intelligence": ["web_analysis_status", "web_analysis_catalog", "web_analysis_refresh", "web_discover", "web_fetch"],
        "research": [
            "research_light",
            "deep_research_topic",
            "deep_research_get",
            "deep_research_list",
            "web_search",
            "youtube_search",
        ],
        "graph": ["graph_search", "graph_get_context", "graph_explain_topic_map"],
        "skills": [
            "skill_list",
            "skill_get",
            "skill_suggest_for_request",
            "skill_validate",
            "skill_install",
            "skill_resource_list",
            "skill_resource_read",
            "skill_healthcheck",
        ],
        "notes": [
            "obsidian_search_health",
            "obsidian_search",
            "obsidian_read",
            "obsidian_list",
            "obsidian_create",
            "obsidian_append",
            "obsidian_create_folder",
            "obsidian_update_section",
            "obsidian_todos",
            "obsidian_backlinks",
            "obsidian_headings",
            "obsidian_generate_moc",
            "obsidian_add_tags",
            "obsidian_set_frontmatter",
        ],
        "academic": [
            "hebat_login_status",
            "hebat_sync_courses",
            "hebat_sync_assignments",
            "hebat_get_assignment_detail",
            "web_analysis_status",
            "web_analysis_catalog",
            "web_analysis_refresh",
            "web_discover",
            "web_fetch",
            "portal_info",
            "portal_navigation",
            "portal_krs_capabilities",
            "portal_grade_changes",
            "portal_grades",
            "portal_grade_token_submit",
            "portal_schedule",
            "portal_krs_watcher_status",
            "portal_krs_watcher_start",
            "portal_krs_watcher_stop",
            "portal_krs_war_status",
            "portal_krs_war_arm",
            "portal_krs_war_disarm",
            "portal_krs_war_plan",
            "portal_krs_war_dry_run",
            "portal_login_start",
            "portal_login_submit_captcha",
            "portal_login_cancel",
            "portal_session_status",
            "portal_logout",
            "uacc_info",
            "uacc_login_start",
            "uacc_login_submit_captcha",
            "uacc_login_cancel",
            "uacc_session_status",
            "uacc_logout",
            "qa_list_kuesioner",
            "qa_fill_kuesioner",
        ],
        "lightning": [
            "lightning_episode_start",
            "lightning_record_action",
            "lightning_record_outcome",
            "lightning_episode_finish",
            "lightning_feedback",
            "lightning_reward_summary",
            "lightning_strategy_rank",
            "lightning_regression_check",
            "lightning_propose_improvement",
            "lightning_list_proposals",
            "lightning_improve",
            "lightning_approve",
            "lightning_reject",
            "lightning_errors",
            "lightning_healthcheck",
        ],
        "life": ["goal_create", "task_capture", "daily_checkin"],
        "reminders": ["reminder_create", "reminder_list", "reminder_cancel"],
        "whatsapp": [
            "wa_pin_message",
            "wa_set_announce",
            "wa_send_text",
            "wa_send_image",
            "wa_send_document",
            "wa_send_audio",
            "wa_send_ptt",
            "wa_send_video",
            "wa_send_sticker",
            "wa_send_admin_verification",
            "wa_forward_media_to_admin",
        ],
        "media": [
            "media_read_document",
            "media_read_image",
            "media_read_audio",
            "media_info",
            "media_ingest_to_knowledge",
        ],
    }
