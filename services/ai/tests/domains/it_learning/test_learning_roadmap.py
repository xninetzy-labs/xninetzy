from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.roadmap_planner import create_roadmap_draft
from app.xninetzy.domains.it_learning.roadmap_store import save_roadmap_draft


def test_roadmap_draft_saved_as_draft():
    init_db()
    run_migrations()
    draft = create_roadmap_draft("AI Agent", 30)
    roadmap_id = save_roadmap_draft(draft, "chat")
    assert roadmap_id > 0
    assert draft.first_day_tasks


def test_roadmap_duration_changes_structure_and_covers_every_day():
    seven = create_roadmap_draft("Graph RAG", 7)
    fourteen = create_roadmap_draft("Graph RAG", 14)
    thirty = create_roadmap_draft("Graph RAG", 30)

    assert [len(seven.phases), len(fourteen.phases), len(thirty.phases)] == [4, 5, 6]
    assert seven.strategy.startswith("sprint")
    assert fourteen.strategy.startswith("balanced")
    assert thirty.strategy.startswith("deep-practice")
    for draft in (seven, fourteen, thirty):
        assert draft.phases[0].start_day == 1
        assert draft.phases[-1].end_day == draft.duration_days


def test_roadmap_uses_bounded_deduplicated_source_references():
    draft = create_roadmap_draft(
        "Machine Learning",
        14,
        "intermediate",
        [
            {"source_id": 7, "title": "ML Notes", "source_type": "obsidian"},
            {"source_id": 7, "title": "Duplicate", "source_type": "pdf"},
            {"source_id": 8, "title": "Course PDF", "source_type": "hebat"},
        ],
    )

    assert [source.source_id for source in draft.source_refs] == [7, 8]
    assert "source-grounded" in draft.strategy
    assert "ML Notes" in draft.first_day_tasks[1]

    roadmap_id = save_roadmap_draft(draft, "source-test")
    with connect() as conn:
        resources = conn.execute(
            "SELECT title, url FROM learning_resources WHERE roadmap_id=? ORDER BY id",
            (roadmap_id,),
        ).fetchall()
    assert [row["title"] for row in resources] == ["ML Notes", "Course PDF"]
    assert resources[0]["url"] == "xninetzy://knowledge/source/7"
