from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.xninetzy.db.sqlite import connect
from app.xninetzy.os.academic.mahasiswa_portal.reader import GradeEntry, GradeResult


@dataclass(frozen=True, slots=True)
class GradeRecord:
    course_key: str
    course_code: str
    course_name: str
    credits: str
    grade: str
    values: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class GradeChange:
    kind: str
    course_key: str
    course_code: str
    course_name: str
    previous_grade: str
    current_grade: str


@dataclass(frozen=True, slots=True)
class GradeSnapshotOutcome:
    snapshot_id: int
    created: bool
    period: str
    captured_at: str
    records: tuple[GradeRecord, ...]
    changes: tuple[GradeChange, ...]


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _value(entry: GradeEntry, aliases: tuple[str, ...]) -> str:
    normalized = [(_key(header), value.strip()) for header, value in entry.values]
    for alias in aliases:
        wanted = _key(alias)
        exact = next((value for header, value in normalized if header == wanted), "")
        if exact:
            return exact
    for alias in aliases:
        wanted = _key(alias)
        partial = next(
            (value for header, value in normalized if wanted in header and value),
            "",
        )
        if partial:
            return partial
    return ""


def normalize_grade_entry(entry: GradeEntry) -> GradeRecord:
    course_code = _value(
        entry,
        ("kode mata kuliah", "kode mata ajar", "kode mk", "kode"),
    )
    course_name = _value(
        entry,
        ("nama mata kuliah", "nama mata ajar", "mata kuliah", "mata ajar", "nama"),
    )
    credits = _value(entry, ("sks", "kredit"))
    grade = _value(entry, ("nilai huruf", "huruf", "grade", "nilai"))
    fallback = next(
        (
            value.strip()
            for header, value in entry.values
            if value.strip() and _key(header) not in {"no", "nomor"}
        ),
        "unknown",
    )
    identity = course_code or course_name or fallback
    course_key = re.sub(r"[^a-z0-9]+", "-", identity.casefold()).strip("-")
    return GradeRecord(
        course_key=course_key or "unknown",
        course_code=course_code,
        course_name=course_name or fallback,
        credits=credits,
        grade=grade,
        values=tuple((header.strip(), value.strip()) for header, value in entry.values),
    )


def normalize_grade_result(result: GradeResult) -> tuple[GradeRecord, ...]:
    records = [normalize_grade_entry(entry) for entry in result.entries]
    return tuple(sorted(records, key=lambda item: item.course_key))


def compare_grade_records(
    previous: tuple[GradeRecord, ...],
    current: tuple[GradeRecord, ...],
) -> tuple[GradeChange, ...]:
    before = {record.course_key: record for record in previous}
    after = {record.course_key: record for record in current}
    changes: list[GradeChange] = []
    for course_key in sorted(before.keys() | after.keys()):
        old = before.get(course_key)
        new = after.get(course_key)
        if old is None and new is not None:
            changes.append(
                GradeChange(
                    kind="added",
                    course_key=course_key,
                    course_code=new.course_code,
                    course_name=new.course_name,
                    previous_grade="",
                    current_grade=new.grade,
                )
            )
        elif old is not None and new is None:
            changes.append(
                GradeChange(
                    kind="removed",
                    course_key=course_key,
                    course_code=old.course_code,
                    course_name=old.course_name,
                    previous_grade=old.grade,
                    current_grade="",
                )
            )
        elif old is not None and new is not None and old.grade != new.grade:
            changes.append(
                GradeChange(
                    kind="changed",
                    course_key=course_key,
                    course_code=new.course_code or old.course_code,
                    course_name=new.course_name or old.course_name,
                    previous_grade=old.grade,
                    current_grade=new.grade,
                )
            )
    return tuple(changes)


def _content_hash(period: str, records: tuple[GradeRecord, ...]) -> str:
    payload = {
        "period": period,
        "records": [
            {
                "course_key": record.course_key,
                "course_code": record.course_code,
                "course_name": record.course_name,
                "credits": record.credits,
                "grade": record.grade,
                "values": list(record.values),
            }
            for record in records
        ],
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class GradeSnapshotRepository:
    def __init__(self, owner_scope: str = "local-owner") -> None:
        self.owner_scope = owner_scope

    def save(self, result: GradeResult) -> GradeSnapshotOutcome:
        records = normalize_grade_result(result)
        content_hash = _content_hash(result.period, records)
        captured_at = datetime.now(UTC).isoformat()
        with connect() as conn:
            latest = conn.execute(
                """
                SELECT id, content_hash, captured_at
                FROM cyber_grade_snapshots
                WHERE owner_scope = ? AND period = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (self.owner_scope, result.period),
            ).fetchone()
            if latest and latest["content_hash"] == content_hash:
                return GradeSnapshotOutcome(
                    snapshot_id=int(latest["id"]),
                    created=False,
                    period=result.period,
                    captured_at=str(latest["captured_at"]),
                    records=records,
                    changes=(),
                )
            previous = self._records(conn, int(latest["id"])) if latest else ()
            cursor = conn.execute(
                """
                INSERT INTO cyber_grade_snapshots(
                    owner_scope, period, content_hash, captured_at
                ) VALUES(?,?,?,?)
                """,
                (self.owner_scope, result.period, content_hash, captured_at),
            )
            snapshot_id = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO cyber_grade_snapshot_items(
                    snapshot_id, course_key, course_code, course_name,
                    credits, grade, values_json
                ) VALUES(?,?,?,?,?,?,?)
                """,
                [
                    (
                        snapshot_id,
                        record.course_key,
                        record.course_code,
                        record.course_name,
                        record.credits,
                        record.grade,
                        json.dumps(
                            list(record.values),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    )
                    for record in records
                ],
            )
        changes = compare_grade_records(previous, records) if latest else ()
        return GradeSnapshotOutcome(
            snapshot_id=snapshot_id,
            created=True,
            period=result.period,
            captured_at=captured_at,
            records=records,
            changes=changes,
        )

    def latest_changes(self, period: str = "") -> GradeSnapshotOutcome | None:
        params: list[str] = [self.owner_scope]
        where = "owner_scope = ?"
        if period.strip():
            where += " AND period = ?"
            params.append(period.strip())
        with connect() as conn:
            latest = conn.execute(
                f"""
                SELECT id, period, captured_at
                FROM cyber_grade_snapshots
                WHERE {where}
                ORDER BY id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
            if latest is None:
                return None
            previous = conn.execute(
                """
                SELECT id
                FROM cyber_grade_snapshots
                WHERE owner_scope = ? AND period = ? AND id < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (self.owner_scope, latest["period"], latest["id"]),
            ).fetchone()
            records = self._records(conn, int(latest["id"]))
            before = self._records(conn, int(previous["id"])) if previous else ()
        changes = compare_grade_records(before, records) if previous else ()
        return GradeSnapshotOutcome(
            snapshot_id=int(latest["id"]),
            created=False,
            period=str(latest["period"]),
            captured_at=str(latest["captured_at"]),
            records=records,
            changes=changes,
        )

    @staticmethod
    def _records(conn, snapshot_id: int) -> tuple[GradeRecord, ...]:
        rows = conn.execute(
            """
            SELECT course_key, course_code, course_name, credits, grade, values_json
            FROM cyber_grade_snapshot_items
            WHERE snapshot_id = ?
            ORDER BY course_key
            """,
            (snapshot_id,),
        ).fetchall()
        return tuple(
            GradeRecord(
                course_key=str(row["course_key"]),
                course_code=str(row["course_code"] or ""),
                course_name=str(row["course_name"] or ""),
                credits=str(row["credits"] or ""),
                grade=str(row["grade"] or ""),
                values=tuple(
                    (str(header), str(value))
                    for header, value in json.loads(row["values_json"] or "[]")
                ),
            )
            for row in rows
        )


GRADE_SNAPSHOT_REPOSITORY = GradeSnapshotRepository()
