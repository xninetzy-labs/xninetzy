from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.core.config import get_settings


def get_db_path() -> Path:
    settings = get_settings()
    path = Path(settings.SQLITE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    statements: Iterable[str] = (
        """
        CREATE TABLE IF NOT EXISTS file_operations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          operation TEXT NOT NULL,
          path TEXT NOT NULL,
          old_content_hash TEXT,
          new_content_hash TEXT,
          backup_path TEXT,
          success INTEGER NOT NULL,
          error TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS skill_calls (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          sender_id TEXT,
          skill_name TEXT NOT NULL,
          skill_action TEXT,
          skill_args_json TEXT,
          skill_result_json TEXT,
          success INTEGER NOT NULL,
          error TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reminders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          sender_id TEXT,
          title TEXT NOT NULL,
          description TEXT,
          remind_at TEXT NOT NULL,
          timezone TEXT DEFAULT 'Asia/Jakarta',
          status TEXT DEFAULT 'pending',
          repeat_rule TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workflows (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          name TEXT NOT NULL,
          description TEXT,
          trigger_json TEXT NOT NULL,
          steps_json TEXT NOT NULL,
          status TEXT DEFAULT 'draft',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
    )

    with connect() as conn:
        for statement in statements:
            conn.execute(statement)
