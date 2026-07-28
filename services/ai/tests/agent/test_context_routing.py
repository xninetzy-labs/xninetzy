from app.xninetzy.context.builder import build_context_packet
from app.xninetzy.context.domain_classifier import classify_domain
from app.xninetzy.context.intent_classifier import classify_intent
from app.xninetzy.context.mode_router import route_mode


def test_domain_prioritizes_it_learning_for_rag():
    assert classify_domain("buat roadmap belajar RAG") == "it_learning"


def test_domain_academic_for_hebat():
    assert classify_domain("cek tugas HEBAT") == "academic"


def test_research_paper_graph_rag_not_general():
    # "graph rag" is treated as an IT learning topic; must not fall through to general.
    assert classify_domain("riset paper Graph RAG") in {"it_learning", "research"}


def test_intent_create_roadmap():
    assert classify_intent("buat roadmap belajar backend") == "create_roadmap"


def test_mode_study_for_it_learning_roadmap():
    assert route_mode("it_learning", "create_roadmap", "buat roadmap backend") == "study"


def test_build_context_packet():
    packet = build_context_packet("buat roadmap belajar Docker")
    assert packet.domain == "it_learning"
    assert packet.intent == "create_roadmap"
    assert packet.mode == "study"
    assert packet.normalized_message == "buat roadmap belajar Docker"
