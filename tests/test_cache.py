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
