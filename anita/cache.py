"""SQLite-backed media cache for generated TTS + images."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from platformdirs import user_cache_dir

_APP_NAME = "anita"


def default_cache_dir() -> Path:
    """Return the platform-appropriate user cache directory for Anita."""
    path = Path(user_cache_dir(_APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


class MediaCache:
    """Tracks previously generated audio/image files for (source, target) pairs."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (default_cache_dir() / "generated_cards.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    image_fname TEXT,
                    audio_fname TEXT,
                    UNIQUE(source, target)
                )
                """
            )
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get(self, source: str, target: str) -> tuple[str | None, str | None] | None:
        """Return (image_fname, audio_fname) for a known pair, or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT image_fname, audio_fname FROM cards WHERE source=? AND target=?",
                (source, target),
            ).fetchone()
        return (row[0], row[1]) if row else None

    def put(
        self,
        source: str,
        target: str,
        image_fname: str | None,
        audio_fname: str | None,
    ) -> None:
        """Upsert a cache entry for a pair."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cards (source, target, image_fname, audio_fname)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source, target) DO UPDATE SET
                    image_fname=excluded.image_fname,
                    audio_fname=excluded.audio_fname
                """,
                (source, target, image_fname, audio_fname),
            )
            conn.commit()

    def iter_rows(self) -> list[tuple[str, str, str | None, str | None]]:
        """Return all cached rows as ``(source, target, image_fname, audio_fname)``."""
        with self._connect() as conn:
            return [
                (row[0], row[1], row[2], row[3])
                for row in conn.execute(
                    "SELECT source, target, image_fname, audio_fname "
                    "FROM cards ORDER BY source, target"
                )
            ]

    def count(self) -> int:
        """Return the number of rows currently in the cache index."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM cards").fetchone()
        return int(row[0]) if row else 0

    def clear(self) -> None:
        """Delete the underlying database file, if it exists."""
        if self.db_path.exists():
            self.db_path.unlink()

    def prune_missing(self, media_dir: Path) -> int:
        """Remove rows whose media files are no longer present on disk.

        A row is pruned when *both* its image and audio filenames either
        are ``NULL`` or point at files missing from ``media_dir``.
        Partially-present rows (e.g. audio on disk but image gone) are
        rewritten to clear only the missing field; this matches the
        disk-reconciliation semantics used during deck generation.

        Returns the number of rows fully removed.
        """
        removed = 0
        with self._connect() as conn:
            rows = list(
                conn.execute(
                    "SELECT id, image_fname, audio_fname FROM cards",
                )
            )
            for row_id, image_fname, audio_fname in rows:
                image_ok = bool(image_fname) and (media_dir / image_fname).is_file()
                audio_ok = bool(audio_fname) and (media_dir / audio_fname).is_file()
                if not image_ok and not audio_ok:
                    conn.execute("DELETE FROM cards WHERE id=?", (row_id,))
                    removed += 1
                elif image_fname and not image_ok:
                    conn.execute(
                        "UPDATE cards SET image_fname=NULL WHERE id=?",
                        (row_id,),
                    )
                elif audio_fname and not audio_ok:
                    conn.execute(
                        "UPDATE cards SET audio_fname=NULL WHERE id=?",
                        (row_id,),
                    )
            conn.commit()
        return removed
