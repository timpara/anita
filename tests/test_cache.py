from __future__ import annotations

from pathlib import Path

from anita.cache import MediaCache


def test_miss_returns_none(cache: MediaCache) -> None:
    assert cache.get("apple", "mela") is None


def test_put_then_get_roundtrip(cache: MediaCache) -> None:
    cache.put("apple", "mela", "img.png", "snd.mp3")
    assert cache.get("apple", "mela") == ("img.png", "snd.mp3")


def test_put_is_idempotent_and_updates(cache: MediaCache) -> None:
    cache.put("apple", "mela", "old.png", "old.mp3")
    cache.put("apple", "mela", "new.png", "new.mp3")
    assert cache.get("apple", "mela") == ("new.png", "new.mp3")


def test_null_fnames_allowed(cache: MediaCache) -> None:
    cache.put("apple", "mela", None, "snd.mp3")
    assert cache.get("apple", "mela") == (None, "snd.mp3")


def test_db_file_is_created(tmp_path: Path) -> None:
    db = tmp_path / "nested" / "cache.db"
    MediaCache(db_path=db)
    assert db.exists()


def test_iter_rows_and_count(cache: MediaCache) -> None:
    assert cache.iter_rows() == []
    assert cache.count() == 0
    cache.put("apple", "mela", "i1.png", "a1.mp3")
    cache.put("house", "casa", None, "a2.mp3")
    # Sorted by (source, target).
    assert cache.iter_rows() == [
        ("apple", "mela", "i1.png", "a1.mp3"),
        ("house", "casa", None, "a2.mp3"),
    ]
    assert cache.count() == 2


def test_clear_removes_db_file(tmp_path: Path, cache: MediaCache) -> None:
    cache.put("apple", "mela", "i.png", "a.mp3")
    assert cache.db_path.exists()
    cache.clear()
    assert not cache.db_path.exists()


def test_clear_is_noop_when_db_missing(tmp_path: Path) -> None:
    cache = MediaCache(db_path=tmp_path / "c.db")
    cache.clear()  # creates, removes
    cache.clear()  # no-op, must not raise
    assert not cache.db_path.exists()


def test_prune_missing_removes_fully_gone_rows(tmp_path: Path, cache: MediaCache) -> None:
    media = tmp_path / "media"
    media.mkdir()
    # Row 1: both files exist.
    (media / "i1.png").write_bytes(b"x")
    (media / "a1.mp3").write_bytes(b"x")
    cache.put("apple", "mela", "i1.png", "a1.mp3")
    # Row 2: both files gone.
    cache.put("house", "casa", "i2.png", "a2.mp3")

    removed = cache.prune_missing(media)

    assert removed == 1
    assert cache.get("apple", "mela") == ("i1.png", "a1.mp3")
    assert cache.get("house", "casa") is None


def test_prune_missing_nulls_partial_rows(tmp_path: Path, cache: MediaCache) -> None:
    """A row with one file present and one gone must be rewritten, not deleted."""
    media = tmp_path / "media"
    media.mkdir()
    (media / "a1.mp3").write_bytes(b"x")  # audio only
    cache.put("apple", "mela", "gone.png", "a1.mp3")

    removed = cache.prune_missing(media)

    assert removed == 0
    assert cache.get("apple", "mela") == (None, "a1.mp3")


def test_prune_missing_removes_null_only_rows(tmp_path: Path, cache: MediaCache) -> None:
    """A row that cached (None, None) is always prunable."""
    media = tmp_path / "media"
    media.mkdir()
    cache.put("apple", "mela", None, None)

    removed = cache.prune_missing(media)

    assert removed == 1
    assert cache.get("apple", "mela") is None
