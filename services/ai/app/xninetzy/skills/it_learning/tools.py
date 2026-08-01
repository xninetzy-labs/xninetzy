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

TOOLS = [
    "learning_create_roadmap",
    "learning_list_roadmaps",
    "learning_get_roadmap",
    "learning_update_progress",
    "learning_generate_today_plan",
    "learning_get_study_progress",
    "learning_review_week",
    "learning_attach_resource",
    "learning_start_study_session",
    "learning_complete_study_session",
    "learning_list_study_sessions",
    "learning_define_concept",
    "learning_record_concept_evidence",
    "learning_get_concept_map",
    "learning_create_recall_card",
    "learning_due_recall",
    "learning_submit_recall_answer",
]

__all__ = [
    "TOOLS",
    "learning_attach_resource",
    "learning_complete_study_session",
    "learning_create_recall_card",
    "learning_create_roadmap",
    "learning_define_concept",
    "learning_due_recall",
    "learning_generate_today_plan",
    "learning_get_concept_map",
    "learning_get_roadmap",
    "learning_get_study_progress",
    "learning_list_roadmaps",
    "learning_list_study_sessions",
    "learning_record_concept_evidence",
    "learning_review_week",
    "learning_start_study_session",
    "learning_submit_recall_answer",
    "learning_update_progress",
]
