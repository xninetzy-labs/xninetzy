from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from xninetzy.core.config import get_settings


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


def _backfill_legacy_owner_columns(conn) -> None:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {row["name"] for row in rows}
    backfills: dict[str, list[tuple[str, str]]] = {
        "improvement_proposals": [
            ("owner", "TEXT"),
            ("scope", "TEXT"),
            ("target_kind", "TEXT"),
            ("target_id", "TEXT"),
            ("source_type", "TEXT"),
            ("source_id", "TEXT"),
            ("proposed_change", "TEXT"),
            ("target_area", "TEXT"),
            ("rationale", "TEXT"),
            ("metrics_json", "TEXT NOT NULL DEFAULT '{}'"),
            ("rollout", "TEXT NOT NULL DEFAULT 'candidate'"),
            ("metadata_json", "TEXT NOT NULL DEFAULT '{}'"),
            ("confidence", "REAL DEFAULT 0"),
            ("risk_score", "REAL DEFAULT 0"),
            ("evidence_json", "TEXT DEFAULT '{}'"),
            ("baseline_metrics_json", "TEXT DEFAULT '{}'"),
            ("candidate_metrics_json", "TEXT DEFAULT '{}'"),
            ("rollout_state", "TEXT DEFAULT 'pending'"),
            ("rollback_json", "TEXT DEFAULT '{}'"),
            ("expires_at", "TEXT"),
            ("idempotency_key", "TEXT"),
            ("reviewed_at", "TEXT"),
            ("reviewed_by", "TEXT"),
            ("updated_at", "TEXT NOT NULL DEFAULT ''"),
        ],
    }
    for table, columns in backfills.items():
        if table not in table_names:
            continue
        existing = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, ddl in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


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
          user_id TEXT,
          sender_id TEXT,
          source TEXT DEFAULT 'user',
          source_ref_id TEXT,
          title TEXT NOT NULL,
          description TEXT,
          context_summary TEXT,
          action_label TEXT,
          display_time_label TEXT,
          deadline_label TEXT,
          offset_label TEXT,
          source_reason TEXT,
          raw_user_message TEXT,
          normalized_task_text TEXT,
          deadline_at TEXT,
          remind_at TEXT NOT NULL,
          timezone TEXT DEFAULT 'Asia/Jakarta',
          status TEXT DEFAULT 'pending',
          priority TEXT DEFAULT 'normal',
          reminder_type TEXT DEFAULT 'explicit',
          offset_value INTEGER,
          offset_unit TEXT,
          repeat_rule TEXT,
          metadata_json TEXT DEFAULT '{}',
          sent_at TEXT,
          expired_at TEXT,
          attempt_count INTEGER DEFAULT 0,
          last_error TEXT,
          locked_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, remind_at)",
        "CREATE INDEX IF NOT EXISTS idx_reminders_chat ON reminders(chat_id, status)",
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
        """
        CREATE TABLE IF NOT EXISTS hebat_downloads (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_id TEXT NOT NULL,
          course_id TEXT,
          cmid TEXT,
          activity_url TEXT,
          file_url TEXT NOT NULL,
          final_url TEXT,
          filename TEXT,
          mime_type TEXT,
          local_path TEXT,
          size_bytes INTEGER,
          sha256 TEXT,
          text_excerpt TEXT,
          summary TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_hebat_activities_course ON hebat_activities(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_assignments_due ON hebat_assignments(due_at)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_submissions_token ON hebat_submissions(confirmation_token)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_audit_chat ON hebat_audit_logs(user_chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_downloads_chat ON hebat_downloads(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_hebat_downloads_cmid ON hebat_downloads(cmid)",
        # Multi-action workflow engine
        """
        CREATE TABLE IF NOT EXISTS workflow_runs (
          id TEXT PRIMARY KEY,
          chat_id TEXT NOT NULL,
          title TEXT,
          original_user_message TEXT NOT NULL,
          status TEXT NOT NULL,
          plan_json TEXT NOT NULL,
          result_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workflow_action_runs (
          id TEXT PRIMARY KEY,
          workflow_id TEXT NOT NULL,
          action_type TEXT NOT NULL,
          title TEXT,
          status TEXT NOT NULL,
          input_json TEXT,
          result_json TEXT,
          result_summary TEXT,
          error TEXT,
          started_at TEXT,
          finished_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_workflow_runs_chat ON workflow_runs(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_action_runs_wf ON workflow_action_runs(workflow_id)",
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
        CREATE TABLE IF NOT EXISTS os_inbox_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          capture_key TEXT NOT NULL UNIQUE,
          chat_id TEXT,
          content TEXT NOT NULL,
          title TEXT NOT NULL,
          inferred_kind TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'inbox',
          target_type TEXT,
          target_id TEXT,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          processed_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_os_inbox_status ON os_inbox_items(status, id)",
        "CREATE INDEX IF NOT EXISTS idx_os_inbox_kind ON os_inbox_items(inferred_kind, status)",
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
        """
        CREATE TABLE IF NOT EXISTS web_source_ledger (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          url TEXT NOT NULL,
          canonical_url TEXT NOT NULL,
          title TEXT,
          publisher TEXT,
          host TEXT,
          content_type TEXT,
          http_status INTEGER,
          excerpt TEXT,
          claim TEXT,
          confidence REAL DEFAULT 0.0,
          retrieval_kind TEXT NOT NULL DEFAULT 'fetch',
          pixelrag_capture_path TEXT,
          evidence_score REAL DEFAULT 0.0,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          fetched_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_web_ledger_url ON web_source_ledger(url)",
        "CREATE INDEX IF NOT EXISTS idx_web_ledger_host ON web_source_ledger(host)",
        "CREATE INDEX IF NOT EXISTS idx_web_ledger_fetched ON web_source_ledger(fetched_at)",
        """
        CREATE TABLE IF NOT EXISTS security_scopes (
          scope_token TEXT PRIMARY KEY,
          owner TEXT NOT NULL,
          targets_json TEXT NOT NULL,
          rationale TEXT,
          expires_at TEXT,
          approved_at TEXT,
          approved_by TEXT,
          created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS security_findings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scope_token TEXT,
          asset TEXT NOT NULL,
          location TEXT,
          category TEXT NOT NULL,
          title TEXT NOT NULL,
          evidence TEXT,
          precondition TEXT,
          reproduction TEXT,
          impact TEXT,
          confidence REAL DEFAULT 0.0,
          severity TEXT DEFAULT 'medium',
          remediation TEXT,
          regression_test TEXT,
          status TEXT DEFAULT 'open',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (scope_token) REFERENCES security_scopes(scope_token)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_security_findings_scope ON security_findings(scope_token)",
        "CREATE INDEX IF NOT EXISTS idx_security_findings_status ON security_findings(status)",
        "CREATE INDEX IF NOT EXISTS idx_security_findings_severity ON security_findings(severity)",
        """
        CREATE TABLE IF NOT EXISTS harness_plans (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_id TEXT NOT NULL UNIQUE,
          owner TEXT NOT NULL,
          title TEXT NOT NULL,
          steps_json TEXT NOT NULL,
          required_tools_json TEXT NOT NULL DEFAULT '[]',
          required_skills_json TEXT NOT NULL DEFAULT '[]',
          verification TEXT,
          status TEXT NOT NULL DEFAULT 'planned',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_harness_plans_owner ON harness_plans(owner)",
        "CREATE INDEX IF NOT EXISTS idx_harness_plans_status ON harness_plans(status)",
        """
        CREATE TABLE IF NOT EXISTS harness_actions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          action_id TEXT NOT NULL UNIQUE,
          plan_id TEXT NOT NULL,
          sequence INTEGER NOT NULL,
          tool_name TEXT NOT NULL,
          args_json TEXT NOT NULL DEFAULT '{}',
          outcome TEXT,
          recorded_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_harness_actions_plan ON harness_actions(plan_id, sequence)",
        """
        CREATE TABLE IF NOT EXISTS harness_verifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_id TEXT NOT NULL,
          passed INTEGER NOT NULL,
          evidence TEXT,
          notes TEXT,
          verified_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_harness_verifications_plan ON harness_verifications(plan_id)",
        """
        CREATE TABLE IF NOT EXISTS improvement_proposals (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          proposal_id TEXT NOT NULL UNIQUE,
          owner TEXT,
          user_id TEXT,
          scope TEXT,
          target_kind TEXT,
          target_id TEXT,
          source_type TEXT,
          source_id TEXT,
          title TEXT,
          problem TEXT,
          proposed_change TEXT,
          target_area TEXT,
          patch_json TEXT DEFAULT '{}',
          risk_level TEXT DEFAULT 'low',
          rationale TEXT,
          metrics_json TEXT NOT NULL DEFAULT '{}',
          rollout TEXT NOT NULL DEFAULT 'candidate',
          status TEXT NOT NULL DEFAULT 'pending',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          confidence REAL DEFAULT 0,
          risk_score REAL DEFAULT 0,
          evidence_json TEXT DEFAULT '{}',
          baseline_metrics_json TEXT DEFAULT '{}',
          candidate_metrics_json TEXT DEFAULT '{}',
          rollout_state TEXT DEFAULT 'pending',
          rollback_json TEXT DEFAULT '{}',
          expires_at TEXT,
          idempotency_key TEXT,
          reviewed_at TEXT,
          reviewed_by TEXT,
          created_at TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL DEFAULT ''
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_improvement_proposals_owner ON improvement_proposals(owner) WHERE owner IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_improvement_proposals_status ON improvement_proposals(status)",
        """
        CREATE TABLE IF NOT EXISTS improvement_evaluations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          proposal_id TEXT NOT NULL,
          metric_name TEXT NOT NULL,
          baseline REAL,
          candidate REAL,
          delta REAL,
          verdict TEXT,
          notes TEXT,
          evaluated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_improvement_eval_proposal ON improvement_evaluations(proposal_id)",
        """
        CREATE TABLE IF NOT EXISTS observability_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_kind TEXT NOT NULL,
          severity TEXT NOT NULL DEFAULT 'info',
          source TEXT,
          subject TEXT,
          payload_json TEXT NOT NULL DEFAULT '{}',
          occurred_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_obs_events_kind ON observability_events(event_kind, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_obs_events_severity ON observability_events(severity, occurred_at)",
        """
        CREATE TABLE IF NOT EXISTS memory_episodes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          episode_id TEXT NOT NULL UNIQUE,
          scope TEXT NOT NULL DEFAULT 'personal',
          owner TEXT NOT NULL,
          task TEXT NOT NULL,
          intent TEXT,
          plan_json TEXT NOT NULL DEFAULT '[]',
          actions_json TEXT NOT NULL DEFAULT '[]',
          outcome TEXT,
          verification TEXT,
          reward REAL DEFAULT 0.0,
          usefulness REAL DEFAULT 0.0,
          status TEXT NOT NULL DEFAULT 'active',
          related_tools_json TEXT NOT NULL DEFAULT '[]',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_memory_episodes_owner ON memory_episodes(owner)",
        "CREATE INDEX IF NOT EXISTS idx_memory_episodes_status ON memory_episodes(status)",
        """
        CREATE TABLE IF NOT EXISTS memory_failures (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          failure_id TEXT NOT NULL UNIQUE,
          owner TEXT NOT NULL,
          failure_class TEXT NOT NULL,
          title TEXT NOT NULL,
          context TEXT,
          root_cause TEXT,
          recovery TEXT,
          recovery_success INTEGER NOT NULL DEFAULT 0,
          related_tool TEXT,
          related_skill TEXT,
          recurrence_count INTEGER NOT NULL DEFAULT 1,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          last_seen_at TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_memory_failures_owner ON memory_failures(owner)",
        "CREATE INDEX IF NOT EXISTS idx_memory_failures_class ON memory_failures(failure_class)",
        """
        CREATE TABLE IF NOT EXISTS memory_procedures (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          procedure_id TEXT NOT NULL UNIQUE,
          owner TEXT NOT NULL,
          name TEXT NOT NULL,
          trigger TEXT NOT NULL,
          steps_json TEXT NOT NULL,
          tools_json TEXT NOT NULL DEFAULT '[]',
          skills_json TEXT NOT NULL DEFAULT '[]',
          verification TEXT,
          success_count INTEGER NOT NULL DEFAULT 0,
          failure_count INTEGER NOT NULL DEFAULT 0,
          last_used_at TEXT,
          status TEXT NOT NULL DEFAULT 'candidate',
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_memory_procedures_owner ON memory_procedures(owner)",
        "CREATE INDEX IF NOT EXISTS idx_memory_procedures_status ON memory_procedures(status)",
        """
        CREATE TABLE IF NOT EXISTS memory_promotion_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_kind TEXT NOT NULL,
          source_id TEXT NOT NULL,
          candidate_kind TEXT NOT NULL,
          candidate_id TEXT,
          stage TEXT NOT NULL,
          verdict TEXT,
          rationale TEXT,
          owner TEXT,
          created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_memory_promotion_kind ON memory_promotion_log(source_kind, source_id)",
    )

    with connect() as conn:
        _backfill_legacy_owner_columns(conn)
        for statement in statements:
            conn.execute(statement)
