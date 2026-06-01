from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.auth import require_api_key
from app.skills.base import SkillInput, SkillOutput
from app.skills.executor import execute_skill
from app.skills.registry import get_skill, list_skills
from app.skills.schemas import SkillRunRequest

router = APIRouter(prefix="/skills", tags=["skills"], dependencies=[Depends(require_api_key)])


@router.get("")
async def skills() -> dict:
    return {"skills": list_skills()}


@router.post("/{skill_name}/run", response_model=SkillOutput)
async def run_skill(skill_name: str, request: SkillRunRequest) -> SkillOutput:
    if skill_name != "skill_discovery" and not get_skill(skill_name):
        raise HTTPException(status_code=404, detail="Skill not found")
    return await execute_skill(
        skill_name,
        SkillInput(chat_id=request.chat_id, sender_id=request.sender_id, message=request.message, metadata=request.metadata),
        action=request.metadata.get("action"),
    )
