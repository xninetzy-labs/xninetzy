"""Data models for multi-action agent workflows.

A *workflow* decomposes one complex user request ("riset X lalu buat planning
lalu simpan ke Obsidian") into ordered :class:`WorkflowAction`s that the
executor runs one-by-one, sending short WA progress updates between them.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowActionType(str, Enum):
    HEBAT_SYNC = "hebat_sync"
    HEBAT_COURSE_DETAIL = "hebat_course_detail"
    HEBAT_ASSIGNMENT_DETAIL = "hebat_assignment_detail"
    HEBAT_DOWNLOAD_MATERIALS = "hebat_download_materials"
    DEEP_RESEARCH = "deep_research"
    WEB_SEARCH = "web_search"
    YOUTUBE_SEARCH = "youtube_search"
    PAPER_SEARCH = "paper_search"
    KNOWLEDGE_INGEST = "knowledge_ingest"
    ROADMAP_CREATE = "roadmap_create"
    TASK_PLANNING = "task_planning"
    REMINDER_CREATE = "reminder_create"
    REMINDER_INFER = "reminder_infer"
    REMINDER_LIST = "reminder_list"
    REMINDER_CANCEL = "reminder_cancel"
    OBSIDIAN_SAVE = "obsidian_save"
    MEMORY_SAVE = "memory_save"
    FINAL_SYNTHESIS = "final_synthesis"


class WorkflowActionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowRunnerMode(str, Enum):
    INLINE = "inline"
    QUEUED = "queued"


class WorkflowAction(BaseModel):
    id: str
    type: WorkflowActionType
    title: str
    goal: str
    input: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    status: WorkflowActionStatus = WorkflowActionStatus.PENDING
    result_summary: str | None = None
    error: str | None = None
    # Critical actions stop the workflow on failure; non-critical ones are skipped past.
    critical: bool = False
    notify_on_done: bool = True


class WorkflowPlan(BaseModel):
    id: str
    chat_id: str
    original_user_message: str
    title: str
    actions: list[WorkflowAction]
    final_goal: str
    created_at: str

    def action_count(self) -> int:
        return len(self.actions)


class WorkflowState(BaseModel):
    """Mutable scratchpad shared across actions during execution."""
    plan_id: str
    chat_id: str
    original_user_message: str
    from_whatsapp: bool = True
    artifacts: dict[str, Any] = Field(default_factory=dict)
    summaries: list[str] = Field(default_factory=list)
    downloaded_files: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    course_context: dict | None = None
    assignment_context: dict | None = None
    research_context: dict | None = None
    roadmap_context: dict | None = None
    planning_context: dict | None = None
    reminder_context: dict | None = None
    obsidian_paths: list[str] = Field(default_factory=list)


class WorkflowActionResult(BaseModel):
    action_id: str
    status: WorkflowActionStatus
    summary: str | None = None
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResult(BaseModel):
    plan_id: str
    status: WorkflowActionStatus
    final_response: str
    action_results: list[WorkflowActionResult] = Field(default_factory=list)

    def succeeded(self) -> list[WorkflowActionResult]:
        return [r for r in self.action_results if r.status == WorkflowActionStatus.SUCCESS]

    def failed(self) -> list[WorkflowActionResult]:
        return [r for r in self.action_results if r.status == WorkflowActionStatus.FAILED]
