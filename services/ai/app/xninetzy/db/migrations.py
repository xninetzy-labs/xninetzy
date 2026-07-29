from __future__ import annotations

from app.xninetzy.db.sqlite import connect


def run_migrations() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            requester_id TEXT,
            requester_name TEXT,
            topic TEXT NOT NULL,
            mode TEXT DEFAULT 'balanced',
            status TEXT DEFAULT 'planned',
            plan_json TEXT DEFAULT '[]',
            substeps_json TEXT DEFAULT '[]',
            sources_json TEXT DEFAULT '[]',
            brief TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS research_briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            topic TEXT NOT NULL,
            brief TEXT NOT NULL,
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            target TEXT,
            duration_days INTEGER DEFAULT 14,
            status TEXT DEFAULT 'draft',
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            position INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            day_index INTEGER,
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            resource_type TEXT DEFAULT 'web',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_key TEXT NOT NULL UNIQUE,
            roadmap_id INTEGER NOT NULL,
            learning_task_id INTEGER,
            chat_id TEXT,
            topic TEXT NOT NULL,
            objective TEXT NOT NULL,
            planned_minutes INTEGER NOT NULL,
            actual_minutes INTEGER,
            energy_before INTEGER NOT NULL,
            energy_after INTEGER,
            mastery_before REAL NOT NULL DEFAULT 0,
            mastery_after REAL,
            status TEXT NOT NULL DEFAULT 'active',
            reflection TEXT,
            evidence_json TEXT NOT NULL DEFAULT '[]',
            completion_event_id INTEGER,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_sessions_roadmap ON learning_study_sessions(roadmap_id, started_at)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_sessions_single_active ON learning_study_sessions(status) WHERE status='active'",
        """
        CREATE TABLE IF NOT EXISTS entity_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            UNIQUE(source_type, source_id, relation, target_type, target_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_entity_links_target ON entity_links(target_type, target_id)",
        """
        CREATE TABLE IF NOT EXISTS ecosystem_event_consumptions (
            event_id INTEGER NOT NULL,
            reducer TEXT NOT NULL,
            consumed_at TEXT NOT NULL,
            PRIMARY KEY (event_id, reducer)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS os_job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT NOT NULL UNIQUE,
            job_type TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            scheduled_for TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            attempts INTEGER NOT NULL DEFAULT 1,
            lease_until TEXT,
            prepared_output TEXT,
            result_output TEXT,
            last_error TEXT,
            retryable INTEGER NOT NULL DEFAULT 0,
            next_retry_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_os_job_runs_status ON os_job_runs(status, next_retry_at)",
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
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id INTEGER NOT NULL,
            target_node_id INTEGER NOT NULL,
            edge_type TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            sender_id TEXT,
            action_type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            payload_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            approved_at TEXT,
            rejected_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT UNIQUE,
            chat_id TEXT,
            message_id TEXT,
            sender_id TEXT,
            media_type TEXT NOT NULL,
            mime_type TEXT,
            file_name TEXT,
            local_path TEXT NOT NULL,
            caption TEXT,
            extracted_text TEXT,
            summary TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE,
            user_id TEXT NOT NULL,
            scope TEXT DEFAULT 'personal',
            rule_type TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            priority INTEGER DEFAULT 50,
            is_active INTEGER DEFAULT 1,
            created_from TEXT,
            source_message_id TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS style_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            tone TEXT DEFAULT 'friendly-technical',
            language TEXT DEFAULT 'id',
            verbosity TEXT DEFAULT 'adaptive',
            formatting TEXT DEFAULT 'whatsapp-friendly',
            learning_style TEXT DEFAULT 'step-by-step',
            correction_style TEXT DEFAULT 'direct-but-kind',
            examples_preference TEXT DEFAULT 'practical',
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id TEXT UNIQUE,
            user_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            scope TEXT DEFAULT 'personal',
            title TEXT,
            content TEXT NOT NULL,
            importance REAL DEFAULT 0.5,
            confidence REAL DEFAULT 0.8,
            source TEXT,
            source_message_id TEXT,
            tags_json TEXT DEFAULT '[]',
            metadata_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            user_id TEXT,
            summary TEXT NOT NULL,
            topics_json TEXT DEFAULT '[]',
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT UNIQUE,
            user_id TEXT,
            chat_id TEXT,
            message_id TEXT,
            input_text TEXT,
            intent TEXT,
            context_sources_json TEXT DEFAULT '[]',
            tools_used_json TEXT DEFAULT '[]',
            response_text TEXT,
            confidence REAL,
            status TEXT DEFAULT 'ok',
            error_type TEXT,
            error_message TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id TEXT UNIQUE,
            user_id TEXT,
            chat_id TEXT,
            message_id TEXT,
            trace_id TEXT,
            feedback_type TEXT,
            feedback_text TEXT,
            severity TEXT DEFAULT 'medium',
            parsed_issue_json TEXT DEFAULT '{}',
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS improvement_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT UNIQUE,
            source_type TEXT,
            source_id TEXT,
            user_id TEXT,
            title TEXT,
            problem TEXT,
            proposed_change TEXT,
            target_area TEXT,
            patch_json TEXT DEFAULT '{}',
            risk_level TEXT DEFAULT 'low',
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            reviewed_at TEXT,
            reviewed_by TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_preferences (
            user_id TEXT PRIMARY KEY,
            chat_provider TEXT NOT NULL,
            chat_model TEXT NOT NULL,
            coding_agent TEXT NOT NULL DEFAULT 'internal',
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS coding_agent_runs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            runtime TEXT NOT NULL,
            task TEXT NOT NULL,
            workspace TEXT NOT NULL,
            status TEXT NOT NULL,
            output TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            finished_at TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_coding_agent_runs_user ON coding_agent_runs(user_id, created_at)",
    ]
    with connect() as conn:
        for statement in statements:
            conn.execute(statement)
        _migrate_reminders(conn)


def _migrate_reminders(conn) -> None:
    """Add reminder workflow columns to existing local databases."""
    rows = conn.execute("PRAGMA table_info(reminders)").fetchall()
    if not rows:
        return
    existing = {row["name"] for row in rows}
    columns = {
        "user_id": "TEXT",
        "source": "TEXT DEFAULT 'user'",
        "source_ref_id": "TEXT",
        "context_summary": "TEXT",
        "action_label": "TEXT",
        "display_time_label": "TEXT",
        "deadline_label": "TEXT",
        "offset_label": "TEXT",
        "source_reason": "TEXT",
        "raw_user_message": "TEXT",
        "normalized_task_text": "TEXT",
        "deadline_at": "TEXT",
        "priority": "TEXT DEFAULT 'normal'",
        "reminder_type": "TEXT DEFAULT 'explicit'",
        "offset_value": "INTEGER",
        "offset_unit": "TEXT",
        "metadata_json": "TEXT DEFAULT '{}'",
        "sent_at": "TEXT",
        "expired_at": "TEXT",
        "attempt_count": "INTEGER DEFAULT 0",
        "last_error": "TEXT",
        "locked_at": "TEXT",
    }
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE reminders ADD COLUMN {name} {ddl}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, remind_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_chat ON reminders(chat_id, status)"
    )
