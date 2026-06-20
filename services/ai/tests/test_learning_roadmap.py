from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.domains.it_learning.roadmap_planner import create_roadmap_draft
from app.xninetzy.domains.it_learning.roadmap_store import save_roadmap_draft


def test_roadmap_draft_saved_as_draft():
    init_db()
    run_migrations()
    draft = create_roadmap_draft("AI Agent", 30)
    roadmap_id = save_roadmap_draft(draft, "chat")
    assert roadmap_id > 0
    assert draft.first_day_tasks
