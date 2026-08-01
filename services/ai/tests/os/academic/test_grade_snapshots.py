from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.academic.mahasiswa_portal.grade_snapshots import (
    GradeSnapshotRepository,
    compare_grade_records,
    normalize_grade_result,
)
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    GradeEntry,
    GradeResult,
)


def _prepare(monkeypatch, tmp_path) -> GradeSnapshotRepository:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "grade-snapshots.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    return GradeSnapshotRepository()


def _result(grade: str, period: str = "2024/2025 - Ganjil") -> GradeResult:
    return GradeResult(
        period=period,
        entries=(
            GradeEntry(
                values=(
                    ("No", "1"),
                    ("Kode MK", "SI101"),
                    ("Nama Mata Kuliah", "Dasar Sistem Informasi"),
                    ("SKS", "3"),
                    ("Nilai Huruf", grade),
                )
            ),
        ),
    )


def test_normalize_grade_result_uses_stable_course_identity():
    records = normalize_grade_result(_result("AB"))

    assert records[0].course_key == "si101"
    assert records[0].course_name == "Dasar Sistem Informasi"
    assert records[0].credits == "3"
    assert records[0].grade == "AB"


def test_compare_grade_records_detects_changed_grade():
    previous = normalize_grade_result(_result("B"))
    current = normalize_grade_result(_result("AB"))

    changes = compare_grade_records(previous, current)

    assert len(changes) == 1
    assert changes[0].kind == "changed"
    assert changes[0].previous_grade == "B"
    assert changes[0].current_grade == "AB"


def test_snapshot_save_is_idempotent_and_tracks_real_change(monkeypatch, tmp_path):
    repository = _prepare(monkeypatch, tmp_path)

    baseline = repository.save(_result("B"))
    replay = repository.save(_result("B"))
    changed = repository.save(_result("AB"))

    assert baseline.created is True
    assert baseline.changes == ()
    assert replay.created is False
    assert replay.snapshot_id == baseline.snapshot_id
    assert changed.created is True
    assert changed.snapshot_id != baseline.snapshot_id
    assert changed.changes[0].kind == "changed"

    latest = repository.latest_changes("2024/2025 - Ganjil")
    assert latest is not None
    assert latest.changes == changed.changes


def test_snapshot_periods_are_compared_independently(monkeypatch, tmp_path):
    repository = _prepare(monkeypatch, tmp_path)

    repository.save(_result("B", "2024/2025 - Ganjil"))
    repository.save(_result("A", "2024/2025 - Genap"))

    latest = repository.latest_changes("2024/2025 - Genap")

    assert latest is not None
    assert latest.period == "2024/2025 - Genap"
    assert latest.changes == ()

def test_snapshot_save_reuses_historical_hash_without_unique_conflict(monkeypatch, tmp_path):
    repository = _prepare(monkeypatch, tmp_path)

    first = repository.save(_result("X"))
    repository.save(_result("Y"))
    replayed = repository.save(_result("X"))

    assert first.created is True
    assert replayed.created is False
    assert replayed.snapshot_id == first.snapshot_id
    assert replayed.changes == ()
