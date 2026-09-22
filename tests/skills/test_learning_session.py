from xninetzy.os.learning import (
    calibrate_confidence,
    decide_hint,
    detect_dependency,
    detect_misconception,
    independence_score,
    mastery_gaps,
    next_action,
    scaffold_fade,
    update_mastery,
)
from xninetzy.schemas.learning_session import (
    HINT_LADDER,
    LEARNING_MODES,
    AttemptRecord,
    ConceptMastery,
    LearningSession,
)


def test_learning_modes_registered() -> None:
    for mode in ["LEARN", "PRACTICE", "QUIZ", "EXAM", "REVIEW", "DEBUG"]:
        assert mode in LEARNING_MODES


def test_hint_ladder_levels() -> None:
    assert len(HINT_LADDER) == 8
    assert HINT_LADDER[0] == "no_hint"
    assert HINT_LADDER[7] == "full_worked_solution"


def test_decide_hint_escalates_on_failure() -> None:
    sess = LearningSession(topic="x")
    sess.current_concept_id = "c"
    sess.attempts.append(AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="wrong", correct=False, independent=False, hint_level_used=2, confidence_before=0.5))
    d = decide_hint(sess)
    assert d.level >= sess.hint_level + 1
    assert d.text


def test_detect_misconception_after_repeated_errors() -> None:
    sess = LearningSession(topic="x")
    for _ in range(4):
        sess.attempts.append(AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="wrong", correct=False, independent=False, error_type="CONCEPTUAL", hint_level_used=0, confidence_before=0.5))
    m = detect_misconception(sess.attempts)
    assert m is not None
    assert m.severity in {"medium", "high"}


def test_calibrate_confidence_overconfident() -> None:
    attempts = [AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="x", correct=False, confidence_before=0.9)]
    r = calibrate_confidence(attempts)
    assert r["overconfident"] == 1.0


def test_mastery_transition_unknown_to_introduced() -> None:
    m = ConceptMastery(concept_id="c")
    upd = update_mastery(m, AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="x", correct=True, confidence_before=0.4, confidence_after=0.5))
    assert upd.old_state == "UNKNOWN"
    assert upd.new_state == "INTRODUCED"


def test_mastery_transition_to_transferable_on_independent() -> None:
    m = ConceptMastery(concept_id="c", understanding=0.7, retrieval=0.7, application=0.7, transfer=0.7, explanation=0.7)
    upd = update_mastery(m, AttemptRecord(session_id="s", concept_id="c", task="transfer", user_answer="long explanation "*5, correct=True, independent=True, confidence_before=0.8, confidence_after=0.9))
    assert upd.new_state in {"STRONG", "TRANSFERABLE"}


def test_independence_score() -> None:
    attempts = [
        AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="a", correct=True, independent=True, hint_level_used=0),
        AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="b", correct=False, independent=False, hint_level_used=5),
    ]
    score = independence_score(attempts)
    assert 0.0 <= score <= 1.0


def test_detect_dependency_when_overreliant() -> None:
    sess = LearningSession(topic="x")
    for _ in range(6):
        sess.attempts.append(AttemptRecord(session_id="s", concept_id="c", task="t", user_answer="a", correct=True, independent=False, hint_level_used=7))
    from xninetzy.schemas.learning_session import HintEvent
    for _ in range(3):
        sess.hints.append(HintEvent(session_id="s", concept_id="c", hint_level=7, hint_text="full"))
    d = detect_dependency(sess)
    assert d["needs_intervention"] is True


def test_next_action_progression() -> None:
    sess = LearningSession(topic="x")
    assert next_action(sess, 0.2) == "prerequisite_review"
    assert next_action(sess, 0.5) == "guided_practice"
    assert next_action(sess, 0.75) == "variation_practice"


def test_scaffold_fade_at_high_mastery() -> None:
    sess = LearningSession(topic="x", hint_level=4)
    assert scaffold_fade(sess, 0.9) <= 2


def test_mastery_gaps() -> None:
    m1 = ConceptMastery(concept_id="a", understanding=0.3, retrieval=0.3, application=0.3, transfer=0.3, explanation=0.3)
    m2 = ConceptMastery(concept_id="b", understanding=0.9, retrieval=0.9, application=0.9, transfer=0.9, explanation=0.9)
    gaps = mastery_gaps({"a": m1, "b": m2}, threshold=0.6)
    assert gaps == ["a"]
