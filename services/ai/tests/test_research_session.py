from app.db.migrations import run_migrations
from app.db.sqlite import init_db
from app.research.session import add_substep, create_research_session, get_research_session, update_substep_status


def test_session_saves_substeps():
    init_db()
    run_migrations()
    session_id = create_research_session("chat", "topic", "sender", "Misbahul")
    substep_id = add_substep(session_id, "planning", "Plan")
    update_substep_status(session_id, substep_id, "done")
    row = get_research_session(session_id)
    assert row
    assert "planning" in row["substeps_json"]
    assert "done" in row["substeps_json"]
