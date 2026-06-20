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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, remind_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_chat ON reminders(chat_id, status)")
