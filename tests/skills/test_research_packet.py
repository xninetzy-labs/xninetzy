from xninetzy.os.research.engine import (
    advance_run,
    build_research_packet,
    discover_perspectives,
    generate_questions,
    start_run,
)
from xninetzy.schemas.research_packet import (
    RESEARCH_MODES,
    RESEARCH_RUN_STATES,
    SourceRecord,
)


def test_research_modes_registered() -> None:
    assert "DEEP_RESEARCH" in RESEARCH_MODES
    assert "LITERATURE_REVIEW" in RESEARCH_MODES


def test_research_states_registered() -> None:
    for state in ["CREATED", "PLANNING", "DISCOVERING_PERSPECTIVES", "COMPLETED"]:
        assert state in RESEARCH_RUN_STATES


def test_discover_perspectives() -> None:
    ps = discover_perspectives("JITAI for diabetes")
    assert 1 <= len(ps) <= 5
    assert all(p.name for p in ps)


def test_generate_questions() -> None:
    ps = discover_perspectives("JITAI for diabetes")
    qs = generate_questions(ps[0], "JITAI for diabetes")
    assert len(qs) >= 1
    assert all(q.question_type for q in qs)


def test_advance_run_completes() -> None:
    run = start_run(topic="X", mode="DEEP_RESEARCH")
    srcs = [SourceRecord(url=f"https://x.com/{i}", excerpt=f"e{i}") for i in range(3)]
    run = advance_run(run, srcs)
    assert run.status == "COMPLETED"
    assert run.evidence_count >= 1


def test_build_research_packet_full() -> None:
    from xninetzy.schemas.research_packet import ResearchBrief, ResearchRun
    brief = ResearchBrief(topic="X", scope="healthcare")
    run = ResearchRun(topic="X", brief=brief)
    srcs = [SourceRecord(url=f"https://x.com/{i}", excerpt=f"finding {i}") for i in range(5)]
    pkt = build_research_packet(run, srcs)
    assert pkt.research_run_id == run.run_id
    assert len(pkt.perspectives) >= 1
    assert len(pkt.questions) >= 1
    assert len(pkt.evidence) >= 1
    assert len(pkt.claims) >= 1
    assert len(pkt.outline.sections) >= 3
