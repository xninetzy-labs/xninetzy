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
        CREATE TABLE IF NOT EXISTS research_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            sid TEXT,
            title TEXT,
            url TEXT,
            snippet TEXT,
            source_type TEXT DEFAULT 'web',
            evidence_level TEXT DEFAULT 'snippet',
            authors TEXT,
            year INTEGER,
            doi TEXT,
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
        CREATE TABLE IF NOT EXISTS learning_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            mastery REAL NOT NULL DEFAULT 0,
            evidence_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'planned',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(roadmap_id, slug),
            FOREIGN KEY(roadmap_id) REFERENCES learning_roadmaps(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_concepts_roadmap ON learning_concepts(roadmap_id, mastery, id)",
        """
        CREATE TABLE IF NOT EXISTS learning_concept_prerequisites (
            concept_id INTEGER NOT NULL,
            prerequisite_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(concept_id, prerequisite_id),
            CHECK(concept_id != prerequisite_id),
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE,
            FOREIGN KEY(prerequisite_id) REFERENCES learning_concepts(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_concept_milestones (
            concept_id INTEGER NOT NULL,
            milestone_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(concept_id, milestone_id),
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE,
            FOREIGN KEY(milestone_id) REFERENCES learning_milestones(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_concept_tasks (
            concept_id INTEGER NOT NULL,
            learning_task_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(concept_id, learning_task_id),
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE,
            FOREIGN KEY(learning_task_id) REFERENCES learning_tasks(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_session_concepts (
            session_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(session_id, concept_id),
            FOREIGN KEY(session_id) REFERENCES learning_study_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_concept_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_key TEXT NOT NULL UNIQUE,
            payload_hash TEXT NOT NULL,
            roadmap_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            evidence_type TEXT NOT NULL,
            reference TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            mastery_score REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(roadmap_id) REFERENCES learning_roadmaps(id) ON DELETE CASCADE,
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_evidence_concept ON learning_concept_evidence(concept_id, id)",
        """
        CREATE TABLE IF NOT EXISTS learning_recall_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_key TEXT NOT NULL UNIQUE,
            payload_hash TEXT NOT NULL,
            roadmap_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            expected_answer TEXT NOT NULL,
            keywords_json TEXT NOT NULL DEFAULT '[]',
            source_reference TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            ease_factor REAL NOT NULL DEFAULT 2.5,
            interval_days INTEGER NOT NULL DEFAULT 0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            lapse_count INTEGER NOT NULL DEFAULT 0,
            due_at TEXT NOT NULL,
            last_reviewed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(roadmap_id) REFERENCES learning_roadmaps(id) ON DELETE CASCADE,
            FOREIGN KEY(concept_id) REFERENCES learning_concepts(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_recall_due ON learning_recall_cards(status, due_at, id)",
        "CREATE INDEX IF NOT EXISTS idx_learning_recall_concept ON learning_recall_cards(concept_id, status)",
        """
        CREATE TABLE IF NOT EXISTS learning_recall_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_key TEXT NOT NULL UNIQUE,
            payload_hash TEXT NOT NULL,
            card_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            keyword_coverage REAL NOT NULL,
            quality INTEGER NOT NULL,
            previous_interval_days INTEGER NOT NULL,
            next_interval_days INTEGER NOT NULL,
            next_due_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(card_id) REFERENCES learning_recall_cards(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_recall_attempts_card ON learning_recall_attempts(card_id, id)",
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
        """
        CREATE TABLE IF NOT EXISTS cyber_grade_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_scope TEXT NOT NULL,
            period TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            UNIQUE(owner_scope, period, content_hash)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cyber_grade_snapshot_items (
            snapshot_id INTEGER NOT NULL,
            course_key TEXT NOT NULL,
            course_code TEXT,
            course_name TEXT NOT NULL,
            credits TEXT,
            grade TEXT,
            values_json TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY(snapshot_id, course_key),
            FOREIGN KEY(snapshot_id) REFERENCES cyber_grade_snapshots(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_cyber_grade_snapshots_period ON cyber_grade_snapshots(owner_scope, period, id)",
        """
        CREATE TABLE IF NOT EXISTS krs_watcher_state (
            owner_scope TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            interval_seconds INTEGER NOT NULL DEFAULT 600,
            started_at TEXT,
            last_tick_at TEXT,
            last_fingerprint TEXT,
            last_notified_fingerprint TEXT,
            last_announcement TEXT,
            last_mk_count INTEGER NOT NULL DEFAULT 0,
            last_status TEXT NOT NULL DEFAULT 'idle',
            last_error TEXT,
            session_expired_notified INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        )
        """,
        # =====================================================================
        # GraphRAG V3 — tri-store canonical layer.
        # SQLite here is the SOURCE OF TRUTH. Neo4j + FAISS are rebuildable
        # projections fed exclusively through graph_sync_outbox (never dual
        # written from business logic). These V3 tables live alongside the
        # legacy graph_nodes/graph_edges (V1) which stay untouched.
        # =====================================================================
        """
        CREATE TABLE IF NOT EXISTS graph_nodes_v3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_key TEXT NOT NULL UNIQUE,
            node_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            properties_json TEXT NOT NULL DEFAULT '{}',
            provenance_json TEXT NOT NULL DEFAULT '{}',
            content_hash TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active',
            neo4j_synced_at TEXT,
            faiss_synced_at TEXT,
            faiss_row INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_graph_nodes_v3_type ON graph_nodes_v3(node_type, status)",
        "CREATE INDEX IF NOT EXISTS idx_graph_nodes_v3_faiss ON graph_nodes_v3(faiss_row)",
        # Full-text search over node title+content for the SQLite retrieval leg.
        "CREATE VIRTUAL TABLE IF NOT EXISTS graph_nodes_v3_fts USING fts5(node_key UNINDEXED, title, content)",
        """
        CREATE TABLE IF NOT EXISTS graph_edges_v3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_key TEXT NOT NULL UNIQUE,
            source_key TEXT NOT NULL,
            target_key TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            properties_json TEXT NOT NULL DEFAULT '{}',
            provenance_json TEXT NOT NULL DEFAULT '{}',
            content_hash TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active',
            neo4j_synced_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(source_key, edge_type, target_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_v3_source ON graph_edges_v3(source_key, status)",
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_v3_target ON graph_edges_v3(target_key, status)",
        # Durable outbox: the ONLY channel that mutates the Neo4j/FAISS
        # projections. Written in the same transaction as the canonical row.
        """
        CREATE TABLE IF NOT EXISTS graph_sync_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_key TEXT NOT NULL,
            op TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            dedupe_key TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            lease_until TEXT,
            next_retry_at TEXT,
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_graph_outbox_ready ON graph_sync_outbox(status, next_retry_at, id)",
        # Append-only audit of every canonical write (provenance + reversibility).
        """
        CREATE TABLE IF NOT EXISTS graph_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_key TEXT NOT NULL,
            op TEXT NOT NULL,
            actor TEXT,
            version INTEGER,
            detail_json TEXT,
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_graph_audit_entity ON graph_audit(entity_type, entity_key, id)",
        """
        CREATE TABLE IF NOT EXISTS krs_war_state (
            owner_scope TEXT PRIMARY KEY,
            armed INTEGER NOT NULL DEFAULT 0,
            plan_hash TEXT,
            plan_json TEXT,
            last_armed_at TEXT,
            last_run_window TEXT,
            last_run_at TEXT,
            last_status TEXT NOT NULL DEFAULT 'idle',
            last_summary TEXT,
            updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS krs_war_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_scope TEXT NOT NULL,
            window TEXT NOT NULL,
            action TEXT NOT NULL,
            course_code TEXT,
            class_code TEXT,
            detail TEXT,
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_krs_war_actions_scope_window ON krs_war_actions(owner_scope, window, course_code)",
        """
        CREATE TABLE IF NOT EXISTS krs_war_calibration (
            owner_scope TEXT NOT NULL,
            window TEXT NOT NULL,
            targets_json TEXT NOT NULL DEFAULT '{}',
            strategy TEXT NOT NULL DEFAULT 'none',
            target_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            last_attempt_at TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(owner_scope, window)
        )
        """,
    ]
    with connect() as conn:
        for statement in statements:
            conn.execute(statement)
        _migrate_reminders(conn)
        _migrate_research_sessions(conn)
        _migrate_approval_requests(conn)
        _backfill_learning_concepts(conn)


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


def _migrate_research_sessions(conn) -> None:
    rows = conn.execute("PRAGMA table_info(research_sessions)").fetchall()
    if not rows:
        return
    existing = {row["name"] for row in rows}
    columns = {"citation_report": "TEXT"}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE research_sessions ADD COLUMN {name} {ddl}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_sources_session ON research_sources(session_id)"
    )


def _migrate_approval_requests(conn) -> None:
    rows = conn.execute("PRAGMA table_info(approval_requests)").fetchall()
    if not rows:
        return
    existing = {row["name"] for row in rows}
    columns = {"expires_at": "TEXT", "action_hash": "TEXT", "execution_at": "TEXT", "execution_result": "TEXT"}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE approval_requests ADD COLUMN {name} {ddl}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_status_created ON approval_requests(status, created_at)")

def _backfill_learning_concepts(conn) -> None:
    from app.xninetzy.domains.it_learning.concept_graph import seed_roadmap_concepts

    roadmaps = conn.execute(
        """
        SELECT roadmap.id, roadmap.created_at
        FROM learning_roadmaps roadmap
        WHERE NOT EXISTS (
            SELECT 1 FROM learning_concepts concept
            WHERE concept.roadmap_id=roadmap.id
        )
        ORDER BY roadmap.id
        """
    ).fetchall()
    for roadmap in roadmaps:
        milestones = conn.execute(
            "SELECT id, title FROM learning_milestones WHERE roadmap_id=? ORDER BY position, id",
            (roadmap["id"],),
        ).fetchall()
        tasks = conn.execute(
            "SELECT id, title FROM learning_tasks WHERE roadmap_id=? ORDER BY day_index, id",
            (roadmap["id"],),
        ).fetchall()
        seed_roadmap_concepts(
            conn,
            int(roadmap["id"]),
            [(int(row["id"]), row["title"]) for row in milestones],
            [(int(row["id"]), row["title"]) for row in tasks],
            roadmap["created_at"] or "1970-01-01T00:00:00+00:00",
        )
