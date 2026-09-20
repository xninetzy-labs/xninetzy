from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xninetzy.context.personal_os.models import (
    LoopStatus,
    OpenLoop,
    PersonalProject,
    ProjectStatus,
    SkillState,
    SkillStatus,
    _now,
    new_loop_id,
    new_project_id,
    new_skill_id,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB = REPO_ROOT / "xninetzy.db"


def _ensure_db() -> None:
    run_migrations()


def _row_to_project(row: Any) -> PersonalProject:
    return PersonalProject(
        project_id=str(row["project_id"]),
        title=str(row["title"]),
        objective=str(row["objective"] or ""),
        goal_id=row["goal_id"] if row["goal_id"] is not None else None,
        status=ProjectStatus(str(row["status"])),
        next_action=str(row["next_action"] or ""),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        last_activity=row["last_activity"],
        metadata=dict(__import__("json").loads(row["metadata_json"] or "{}")),
    )


def _row_to_loop(row: Any) -> OpenLoop:
    created = datetime.fromisoformat(row["created_at"])
    age = max(0, (datetime.now(timezone.utc) - created).days)
    return OpenLoop(
        loop_id=str(row["loop_id"]),
        title=str(row["title"]),
        description=str(row["description"] or ""),
        status=LoopStatus(str(row["status"])),
        age_days=age,
        importance=str(row["importance"]),
        owner_scope=str(row["owner_scope"] or "system"),
        project_id=row["project_id"],
        next_action=str(row["next_action"] or ""),
        created_at=str(row["created_at"]),
        resolved_at=row["resolved_at"],
    )


class PersonalOS:
    def __init__(self, owner_scope: str = "system") -> None:
        self.owner_scope = owner_scope
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        _ensure_db()
        with connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS personal_projects (
                    project_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    objective TEXT,
                    goal_id INTEGER,
                    status TEXT NOT NULL,
                    next_action TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_activity TEXT
                );

                CREATE TABLE IF NOT EXISTS open_loops (
                    loop_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    importance TEXT NOT NULL,
                    owner_scope TEXT NOT NULL,
                    project_id TEXT,
                    next_action TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    UNIQUE(owner_scope, title)
                );

                CREATE TABLE IF NOT EXISTS skill_state (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_count INTEGER NOT NULL DEFAULT 0,
                    last_practiced TEXT,
                    UNIQUE(name)
                );
                """
            )

    def create_project(
        self,
        *,
        title: str,
        objective: str = "",
        goal_id: int | None = None,
        next_action: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PersonalProject:
        import json

        pid = new_project_id()
        now = _now()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO personal_projects
                  (project_id, title, objective, goal_id, status, next_action,
                   metadata_json, created_at, updated_at, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    title,
                    objective,
                    goal_id,
                    ProjectStatus.ACTIVE.value,
                    next_action,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    now,
                    now,
                    now,
                ),
            )
        return PersonalProject(
            project_id=pid,
            title=title,
            objective=objective,
            goal_id=goal_id,
            status=ProjectStatus.ACTIVE,
            next_action=next_action,
            created_at=now,
            updated_at=now,
            last_activity=now,
            metadata=metadata or {},
        )

    def list_projects(
        self, status: ProjectStatus | None = None
    ) -> tuple[PersonalProject, ...]:
        with connect() as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM personal_projects ORDER BY updated_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM personal_projects WHERE status=? ORDER BY updated_at DESC",
                    (status.value,),
                ).fetchall()
        return tuple(_row_to_project(r) for r in rows)

    def get_project(self, project_id: str) -> PersonalProject | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM personal_projects WHERE project_id=?",
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_project(row)

    def update_project_status(
        self, project_id: str, status: ProjectStatus, next_action: str = ""
    ) -> PersonalProject | None:
        now = _now()
        with connect() as conn:
            conn.execute(
                """
                UPDATE personal_projects
                   SET status=?, next_action=?, updated_at=?, last_activity=?
                 WHERE project_id=?
                """,
                (status.value, next_action, now, now, project_id),
            )
        return self.get_project(project_id)

    def stall_project(self, project_id: str, days: int = 14) -> bool:
        from datetime import datetime, timezone

        with connect() as conn:
            row = conn.execute(
                "SELECT last_activity FROM personal_projects WHERE project_id=?",
                (project_id,),
            ).fetchone()
        if row is None or row["last_activity"] is None:
            return False
        last = datetime.fromisoformat(row["last_activity"])
        return (datetime.now(timezone.utc) - last).days >= days

    def open_loop(
        self,
        *,
        title: str,
        description: str = "",
        importance: str = "medium",
        project_id: str | None = None,
        next_action: str = "",
    ) -> OpenLoop:
        lid = new_loop_id()
        now = _now()
        with connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO open_loops
                  (loop_id, title, description, status, importance, owner_scope,
                   project_id, next_action, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lid,
                    title,
                    description,
                    LoopStatus.OPEN.value,
                    importance,
                    self.owner_scope,
                    project_id,
                    next_action,
                    now,
                    None,
                ),
            )
        return self._fetch_loop_by_title(title) or OpenLoop(
            loop_id=lid,
            title=title,
            description=description,
            status=LoopStatus.OPEN,
            age_days=0,
            importance=importance,
            owner_scope=self.owner_scope,
            project_id=project_id,
            next_action=next_action,
            created_at=now,
            resolved_at=None,
        )

    def _fetch_loop_by_title(self, title: str) -> OpenLoop | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM open_loops WHERE owner_scope=? AND title=?",
                (self.owner_scope, title),
            ).fetchone()
        if row is None:
            return None
        return _row_to_loop(row)

    def list_open_loops(self) -> tuple[OpenLoop, ...]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT * FROM open_loops WHERE owner_scope=? AND status=? ORDER BY created_at",
                (self.owner_scope, LoopStatus.OPEN.value),
            ).fetchall()
        return tuple(_row_to_loop(r) for r in rows)

    def resolve_loop(self, loop_id: str) -> OpenLoop | None:
        now = _now()
        with connect() as conn:
            conn.execute(
                "UPDATE open_loops SET status=?, resolved_at=? WHERE loop_id=?",
                (LoopStatus.RESOLVED.value, now, loop_id),
            )
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM open_loops WHERE loop_id=?",
                (loop_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_loop(row)

    def register_skill(self, name: str) -> SkillState:
        sid = new_skill_id()
        now = _now()
        with connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO skill_state (skill_id, name, status, evidence_count, last_practiced) VALUES (?, ?, ?, 0, ?)",
                (sid, name, SkillStatus.UNKNOWN.value, now),
            )
        return self.get_skill(name) or SkillState(
            skill_id=sid,
            name=name,
            status=SkillStatus.UNKNOWN,
            evidence_count=0,
            last_practiced=now,
        )

    def advance_skill(self, name: str, target: SkillStatus) -> SkillState:
        now = _now()
        with connect() as conn:
            conn.execute(
                "UPDATE skill_state SET status=?, evidence_count=evidence_count+1, last_practiced=? WHERE name=?",
                (target.value, now, name),
            )
        return self.get_skill(name) or self.register_skill(name)

    def get_skill(self, name: str) -> SkillState | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM skill_state WHERE name=?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return SkillState(
            skill_id=str(row["skill_id"]),
            name=str(row["name"]),
            status=SkillStatus(str(row["status"])),
            evidence_count=int(row["evidence_count"]),
            last_practiced=row["last_practiced"],
        )


_personal_os: PersonalOS | None = None


def get_personal_os() -> PersonalOS:
    global _personal_os
    if _personal_os is None:
        _personal_os = PersonalOS()
    return _personal_os
