"""SQLite-backed media cache for generated TTS + images."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from platformdirs import user_cache_dir

_APP_NAME = "anita"


def default_cache_dir() -> Path:
    """Return the platform-appropriate user cache directory for Anita."""
    path = Path(user_cache_dir(_APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


class MediaCache:
    """Tracks previously generated audio/image files for (source, target) pairs.

    Uses a persistent connection with WAL journal mode for better performance
    during batch operations (avoids open/close overhead per query).
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (default_cache_dir() / "generated_cards.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        self._ensure_schema()

    @property
    def _connection(self) -> sqlite3.Connection:
        """Return the persistent connection, creating it if needed."""
        if self._conn is None:
            # check_same_thread=False is required because the deck generator
            # uses a thread pool for concurrent API calls that share this cache.
            # Thread safety is ensured by SQLite's WAL mode and its internal
            # locking (writes are serialized by the database engine).
            self._conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            # WAL mode allows concurrent readers and reduces lock contention.
            self._conn.execute("PRAGMA journal_mode=WAL")
            # Synchronous NORMAL is safe with WAL and faster than FULL.
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    def _ensure_schema(self) -> None:
        conn = self._connection
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

    def close(self) -> None:
        """Close the persistent connection. Safe to call multiple times."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def get(self, source: str, target: str) -> tuple[str | None, str | None] | None:
        """Return (image_fname, audio_fname) for a known pair, or None."""
        with self._lock:
            row = self._connection.execute(
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
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO cards (source, target, image_fname, audio_fname)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source, target) DO UPDATE SET
                    image_fname=excluded.image_fname,
                    audio_fname=excluded.audio_fname
                """,
                (source, target, image_fname, audio_fname),
            )
            self._connection.commit()

    def iter_rows(self) -> list[tuple[str, str, str | None, str | None]]:
        """Return all cached rows as ``(source, target, image_fname, audio_fname)``."""
        return [
            (row[0], row[1], row[2], row[3])
            for row in self._connection.execute(
                "SELECT source, target, image_fname, audio_fname FROM cards ORDER BY source, target"
            )
        ]

    def count(self) -> int:
        """Return the number of rows currently in the cache index."""
        row = self._connection.execute("SELECT COUNT(*) FROM cards").fetchone()
        return int(row[0]) if row else 0

    def clear(self) -> None:
        """Delete the underlying database file, if it exists."""
        self.close()
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
        conn = self._connection
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
