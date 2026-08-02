from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db


@dataclass(frozen=True, slots=True)
class VaultIndexHealth:
    indexed_files: int
    source_files: int
    skipped_files: int
    healthy: bool

    def as_dict(self) -> dict[str, int | bool]:
        return {
            "indexed_files": self.indexed_files,
            "source_files": self.source_files,
            "skipped_files": self.skipped_files,
            "healthy": self.healthy,
        }


class VaultSearchIndex:
    def __init__(self, max_files: int = 2_000) -> None:
        self.max_files = max(1, max_files)

    def sync(
        self,
        files: Iterable[dict],
        read_content: Callable[[str], str],
    ) -> VaultIndexHealth:
        init_db()
        run_migrations()
        all_files = [
            item
            for item in files
            if not str(item["path"]).startswith(".backup/")
        ]
        selected = all_files[: self.max_files]
        selected_paths = {str(item["path"]) for item in selected}
        with connect() as conn:
            existing_rows = conn.execute(
                "SELECT path, content_hash FROM obsidian_note_index"
            ).fetchall()
            existing = {
                str(row["path"]): str(row["content_hash"])
                for row in existing_rows
            }
            for path in set(existing) - selected_paths:
                conn.execute("DELETE FROM obsidian_notes_fts WHERE path=?", (path,))
                conn.execute("DELETE FROM obsidian_note_index WHERE path=?", (path,))
            for item in selected:
                path = str(item["path"])
                content = read_content(path)
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if existing.get(path) == digest:
                    continue
                conn.execute("DELETE FROM obsidian_notes_fts WHERE path=?", (path,))
                conn.execute(
                    "INSERT INTO obsidian_notes_fts(path, content) VALUES (?, ?)",
                    (path, content),
                )
                conn.execute(
                    """
                    INSERT INTO obsidian_note_index(path, content_hash, modified_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                      content_hash=excluded.content_hash,
                      modified_at=excluded.modified_at
                    """,
                    (path, digest, str(item.get("modified_at") or "")),
                )
            indexed_files = int(
                conn.execute("SELECT COUNT(*) FROM obsidian_note_index").fetchone()[0]
            )
        return VaultIndexHealth(
            indexed_files=indexed_files,
            source_files=len(selected),
            skipped_files=max(0, len(all_files) - len(selected)),
            healthy=indexed_files == len(selected),
        )

    def search(self, query: str, limit: int = 20) -> list[dict]:
        keywords = re.findall(r"[\w]+", query, flags=re.UNICODE)
        if not keywords:
            return []
        expression = " AND ".join(f'"{token}"' for token in keywords)
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT path, snippet(obsidian_notes_fts, 1, '', '', ' … ', 24) AS preview
                FROM obsidian_notes_fts
                WHERE obsidian_notes_fts MATCH ?
                ORDER BY bm25(obsidian_notes_fts)
                LIMIT ?
                """,
                (expression, max(1, min(limit, 500))),
            ).fetchall()
        return [dict(row) for row in rows]
