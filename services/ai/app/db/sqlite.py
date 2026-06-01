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
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          tool_name TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id)",
        # HEBAT / Moodle tables
        """
        CREATE TABLE IF NOT EXISTS hebat_sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_chat_id TEXT NOT NULL UNIQUE,
          profile_name TEXT,
          storage_state_path TEXT,
          auth_mode TEXT DEFAULT 'username_password',
          is_active INTEGER DEFAULT 0,
          last_login_at TEXT,
          last_checked_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_courses (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          moodle_course_id TEXT NOT NULL UNIQUE,
          fullname TEXT NOT NULL,
          shortname TEXT,
          course_url TEXT NOT NULL,
          last_synced_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_activities (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          course_id TEXT NOT NULL,
          cmid TEXT NOT NULL,
          type TEXT NOT NULL,
          title TEXT NOT NULL,
          section_title TEXT,
          activity_url TEXT NOT NULL,
          due_at TEXT,
          opened_at TEXT,
          status TEXT,
          raw_html_path TEXT,
          last_synced_at TEXT,
          UNIQUE(cmid)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_files (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          activity_id INTEGER NOT NULL,
          filename TEXT NOT NULL,
          file_url TEXT NOT NULL,
          local_path TEXT,
          mime_type TEXT,
          size_bytes INTEGER,
          sha256 TEXT,
          downloaded_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_assignments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          activity_id INTEGER NOT NULL UNIQUE,
          title TEXT NOT NULL,
          instruction_text TEXT,
          opened_at TEXT,
          due_at TEXT,
          time_remaining_text TEXT,
          submission_status TEXT,
          grading_status TEXT,
          last_modified_text TEXT,
          max_files INTEGER DEFAULT 1,
          max_bytes INTEGER DEFAULT 5242880,
          accepted_types TEXT DEFAULT '.pdf',
          latest_submission_file TEXT,
          last_synced_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_submissions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          assignment_id INTEGER NOT NULL,
          source_chat_id TEXT NOT NULL,
          source_message_id TEXT,
          local_file_path TEXT NOT NULL,
          uploaded_filename TEXT,
          upload_status TEXT DEFAULT 'pending_confirmation',
          confirmation_token TEXT UNIQUE,
          confirmed_at TEXT,
          submitted_at TEXT,
          verification_text TEXT,
          error_message TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hebat_audit_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_chat_id TEXT NOT NULL,
          action TEXT NOT NULL,
          target_type TEXT,
          target_id TEXT,
          status TEXT NOT NULL,
          detail_json TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_hebat_activities_course ON hebat_activities(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_assignments_due ON hebat_assignments(due_at)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_submissions_token ON hebat_submissions(confirmation_token)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_audit_chat ON hebat_audit_logs(user_chat_id)",
        # Ecosystem events
        """
        CREATE TABLE IF NOT EXISTS ecosystem_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          source TEXT NOT NULL,
          entity_type TEXT,
          entity_id TEXT,
          payload_json TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_events_chat ON ecosystem_events(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_events_type ON ecosystem_events(event_type)",
        # Life OS tables
        """
        CREATE TABLE IF NOT EXISTS life_goals (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          description TEXT,
          domain TEXT NOT NULL DEFAULT 'personal',
          horizon TEXT NOT NULL DEFAULT 'monthly',
          status TEXT NOT NULL DEFAULT 'active',
          priority TEXT NOT NULL DEFAULT 'medium',
          target_metric TEXT,
          target_value REAL,
          current_value REAL DEFAULT 0,
          unit TEXT,
          start_date TEXT,
          due_date TEXT,
          obsidian_path TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS life_goal_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          goal_id INTEGER NOT NULL,
          log_text TEXT NOT NULL,
          progress_delta REAL DEFAULT 0,
          mood INTEGER,
          confidence INTEGER,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          description TEXT,
          status TEXT NOT NULL DEFAULT 'inbox',
          priority TEXT NOT NULL DEFAULT 'medium',
          domain TEXT,
          goal_id INTEGER,
          project_id INTEGER,
          due_at TEXT,
          scheduled_at TEXT,
          source TEXT DEFAULT 'manual',
          obsidian_path TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_at)",
        """
        CREATE TABLE IF NOT EXISTS money_accounts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          type TEXT NOT NULL DEFAULT 'bank',
          currency TEXT NOT NULL DEFAULT 'IDR',
          balance REAL NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS money_transactions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          account_id INTEGER,
          amount REAL NOT NULL,
          type TEXT NOT NULL,
          category TEXT NOT NULL DEFAULT 'lain-lain',
          description TEXT,
          transaction_date TEXT NOT NULL,
          source TEXT DEFAULT 'manual',
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_money_date ON money_transactions(transaction_date)",
        """
        CREATE TABLE IF NOT EXISTS workout_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          workout_date TEXT NOT NULL,
          type TEXT NOT NULL DEFAULT 'other',
          exercises_json TEXT,
          duration_minutes INTEGER,
          intensity TEXT DEFAULT 'medium',
          notes TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS habits (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          domain TEXT DEFAULT 'personal',
          frequency TEXT NOT NULL DEFAULT 'daily',
          target_count INTEGER NOT NULL DEFAULT 1,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS habit_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          habit_id INTEGER NOT NULL,
          log_date TEXT NOT NULL,
          value INTEGER NOT NULL DEFAULT 1,
          notes TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_reviews (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          date TEXT NOT NULL UNIQUE,
          mood INTEGER,
          energy INTEGER,
          focus INTEGER,
          summary TEXT,
          wins TEXT,
          problems TEXT,
          next_actions TEXT,
          ai_feedback TEXT,
          obsidian_path TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          description TEXT,
          status TEXT NOT NULL DEFAULT 'active',
          domain TEXT,
          goal_id INTEGER,
          obsidian_path TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        # Knowledge tables
        """
        CREATE TABLE IF NOT EXISTS knowledge_sources (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_type TEXT NOT NULL,
          title TEXT NOT NULL,
          uri TEXT,
          local_path TEXT,
          obsidian_path TEXT,
          sha256 TEXT UNIQUE,
          metadata_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_id INTEGER NOT NULL,
          chunk_index INTEGER NOT NULL,
          text TEXT NOT NULL,
          token_count INTEGER,
          faiss_id INTEGER,
          metadata_json TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_chunks_source ON knowledge_chunks(source_id)",
        "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(chunk_id UNINDEXED, text, content='knowledge_chunks', content_rowid='id')",
        # Concept graph (SQLite fallback)
        """
        CREATE TABLE IF NOT EXISTS concept_edges (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          concept_a TEXT NOT NULL,
          relation TEXT NOT NULL,
          concept_b TEXT NOT NULL,
          source_id INTEGER,
          weight REAL DEFAULT 1.0,
          created_at TEXT NOT NULL,
          UNIQUE(concept_a, relation, concept_b)
        )
        """,
        # Learning workspaces
        """
        CREATE TABLE IF NOT EXISTS learning_workspaces (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          topic TEXT NOT NULL,
          description TEXT,
          status TEXT DEFAULT 'active',
          obsidian_folder TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_workspace_sources (
          workspace_id INTEGER NOT NULL,
          source_id INTEGER NOT NULL,
          PRIMARY KEY (workspace_id, source_id)
        )
        """,
    )

    with connect() as conn:
        for statement in statements:
            conn.execute(statement)
