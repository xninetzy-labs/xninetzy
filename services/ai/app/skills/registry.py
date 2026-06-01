from __future__ import annotations

from app.skills.base import Skill

_skills: dict[str, Skill] = {}
_intent_map: dict[str, list[str]] = {}


def register_skill(skill: Skill, intents: list[str] | None = None) -> None:
    if skill.name in _skills:
        raise ValueError(f"Skill already registered: {skill.name}")
    _skills[skill.name] = skill
    for intent in intents or []:
        _intent_map.setdefault(intent, []).append(skill.name)


def get_skill(name: str) -> Skill | None:
    ensure_default_skills_registered()
    return _skills.get(name)


def list_skills() -> list[dict]:
    ensure_default_skills_registered()
    return [
        {
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "input_schema": skill.input_schema,
            "output_schema": skill.output_schema,
            "safety_policy": skill.safety_policy,
            "memory_behavior": skill.memory_behavior,
        }
        for skill in _skills.values()
    ]


def find_skills_by_intent(intent: str) -> list[Skill]:
    ensure_default_skills_registered()
    return [_skills[name] for name in _intent_map.get(intent, []) if name in _skills]


def ensure_default_skills_registered() -> None:
    if _skills:
        return

    from app.skills.skills.calculation_skill import CalculationSkill
    from app.skills.skills.date_time_skill import DateTimeSkill
    from app.skills.skills.group_action_skill import GroupActionSkill
    from app.skills.skills.idea_analysis_skill import IdeaAnalysisSkill
    from app.skills.skills.learning_skill import LearningSkill
    from app.skills.skills.note_skill import NoteGenerationSkill
    from app.skills.skills.obsidian_skill import ObsidianSkill
    from app.skills.skills.planning_skill import PlanningSkill
    from app.skills.skills.reminder_skill import ReminderSkill
    from app.skills.skills.task_breakdown_skill import TaskBreakdownSkill
    from app.skills.skills.workflow_skill import WorkflowSkill

    register_skill(LearningSkill(), ["learning"])
    register_skill(ReminderSkill(), ["reminder_create", "reminder_query", "reminder_update", "reminder_delete"])
    register_skill(CalculationSkill(), ["calculation"])
    register_skill(DateTimeSkill(), ["date_time"])
    register_skill(GroupActionSkill(), ["group_management", "admin_action"])
    register_skill(IdeaAnalysisSkill(), ["idea_analysis"])
    register_skill(TaskBreakdownSkill(), ["task_breakdown", "task_management"])
    register_skill(WorkflowSkill(), ["workflow_automation"])
    register_skill(ObsidianSkill(), ["obsidian_read", "obsidian_write"])
    register_skill(NoteGenerationSkill(), ["note_generation"])
    register_skill(PlanningSkill(), ["daily_planning"])
