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
