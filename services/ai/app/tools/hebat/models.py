from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuthMode(str, Enum):
    USERNAME_PASSWORD = "username_password"
    MANUAL_BROWSER = "manual_browser"
    GOOGLE_OAUTH = "google_oauth"


class UploadStatus(str, Enum):
    PENDING_CONFIRMATION = "pending_confirmation"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActivityType(str, Enum):
    RESOURCE = "resource"
    FOLDER = "folder"
    ASSIGN = "assign"
    FORUM = "forum"
    QUIZ = "quiz"
    PAGE = "page"
    URL = "url"
    UNKNOWN = "unknown"


class HebatSession(BaseModel):
    user_chat_id: str
    profile_name: str | None = None
    storage_state_path: str | None = None
    auth_mode: AuthMode = AuthMode.USERNAME_PASSWORD
    is_active: bool = False
    last_login_at: str | None = None
    last_checked_at: str | None = None


class HebatCourse(BaseModel):
    moodle_course_id: str
    fullname: str
    shortname: str | None = None
    course_url: str
    last_synced_at: str | None = None


class HebatActivity(BaseModel):
    course_id: str
    cmid: str
    type: ActivityType
    title: str
    section_title: str | None = None
    activity_url: str
    due_at: str | None = None
    opened_at: str | None = None
    status: str | None = None


class HebatAssignment(BaseModel):
    activity_id: int
    title: str
    instruction_text: str | None = None
    opened_at: str | None = None
    due_at: str | None = None
    time_remaining_text: str | None = None
    submission_status: str | None = None
    grading_status: str | None = None
    last_modified_text: str | None = None
    max_files: int = 1
    max_bytes: int = 5_242_880
    accepted_types: str = ".pdf"
    latest_submission_file: str | None = None


class HebatFile(BaseModel):
    activity_id: int
    filename: str
    file_url: str
    local_path: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None


class SubmissionPreview(BaseModel):
    status: str
    confirmation_token: str | None = None
    assignment_title: str
    detected_file: str
    expected_filename: str | None = None
    warnings: list[str] = Field(default_factory=list)
    confirmation_message: str


class EditSubmissionFields(BaseModel):
    """Dynamic fields extracted from Moodle edit submission form."""
    form_action: str
    item_id: str
    sesskey: str
    assign_id: str
    user_id: str
    context_id: str | None = None
    max_bytes: int = 5_242_880
    max_files: int = 1
    accepted_types: list[str] = Field(default_factory=lambda: [".pdf"])
