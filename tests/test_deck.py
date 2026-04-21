from __future__ import annotations

from pathlib import Path

import pytest
from anita.cache import MediaCache
from anita.deck import AnkiDeckGenerator, _read_csv

from tests.conftest import FakeImages, FakeTTS


def _make_generator(
    tmp_path: Path,
    tts: FakeTTS,
    images: FakeImages | None = None,
    *,
    generate_images: bool = False,
) -> AnkiDeckGenerator:
    return AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts,
        generate_images=generate_images,
        image_provider=images,
        media_dir=tmp_path / "media",
        cache=MediaCache(db_path=tmp_path / "cache.db"),
    )


def test_generate_deck_writes_apkg(tmp_path: Path, sample_csv: Path, fake_tts: FakeTTS) -> None:
    out = tmp_path / "out.apkg"
    gen = _make_generator(tmp_path, fake_tts)

    result = gen.generate_deck(sample_csv, out)

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0
    # One TTS call per CSV row
    assert len(fake_tts.calls) == 3


def test_header_row_is_detected_and_skipped(
    tmp_path: Path, sample_csv_with_header: Path, fake_tts: FakeTTS
) -> None:
    out = tmp_path / "out.apkg"
    gen = _make_generator(tmp_path, fake_tts)
    gen.generate_deck(sample_csv_with_header, out)
    # 2 data rows only, header discarded
    assert len(fake_tts.calls) == 2


def test_cache_hit_skips_provider(tmp_path: Path, sample_csv: Path) -> None:
    tts = FakeTTS()
    gen1 = _make_generator(tmp_path, tts)
    gen1.generate_deck(sample_csv, tmp_path / "a.apkg")
    assert len(tts.calls) == 3

    # Second run reuses cache (same DB path)
    tts2 = FakeTTS()
    cache = MediaCache(db_path=tmp_path / "cache.db")
    gen2 = AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts2,
        media_dir=tmp_path / "media",
        cache=cache,
    )
    gen2.generate_deck(sample_csv, tmp_path / "b.apkg")
    assert tts2.calls == []  # all cached


def test_images_flag_invokes_image_provider(
    tmp_path: Path, sample_csv: Path, fake_tts: FakeTTS, fake_images: FakeImages
) -> None:
    gen = _make_generator(tmp_path, fake_tts, fake_images, generate_images=True)
    gen.generate_deck(sample_csv, tmp_path / "out.apkg")
    assert len(fake_images.calls) == 3


def test_missing_csv_raises(tmp_path: Path, fake_tts: FakeTTS) -> None:
    gen = _make_generator(tmp_path, fake_tts)
    with pytest.raises(FileNotFoundError):
        gen.generate_deck(tmp_path / "nope.csv", tmp_path / "out.apkg")


def test_empty_csv_raises(tmp_path: Path, fake_tts: FakeTTS) -> None:
    csv = tmp_path / "empty.csv"
    csv.write_text("", encoding="utf-8")
    gen = _make_generator(tmp_path, fake_tts)
    with pytest.raises(ValueError, match="No usable rows"):
        gen.generate_deck(csv, tmp_path / "out.apkg")


def test_read_csv_skips_malformed_rows(tmp_path: Path) -> None:
    csv = tmp_path / "mixed.csv"
    csv.write_text("apple,mela\nno-comma\n,empty-source\nhouse,casa\n", encoding="utf-8")
    assert _read_csv(csv) == [("apple", "mela"), ("house", "casa")]


def test_tts_failure_drops_audio_but_keeps_card(tmp_path: Path, sample_csv: Path) -> None:
    failing_tts = FakeTTS(should_fail=True)
    gen = _make_generator(tmp_path, failing_tts)
    out = tmp_path / "out.apkg"
    gen.generate_deck(sample_csv, out)
    # Deck still written even with no audio
    assert out.exists()


def test_deleted_audio_is_regenerated_on_next_run(tmp_path: Path, sample_csv: Path) -> None:
    """Cache hit + audio file missing from disk must trigger regeneration (#22)."""
    tts1 = FakeTTS()
    gen1 = _make_generator(tmp_path, tts1)
    gen1.generate_deck(sample_csv, tmp_path / "a.apkg")
    assert len(tts1.calls) == 3

    # Simulate a user wiping the media directory.
    media = tmp_path / "media"
    for f in media.glob("audio_*.mp3"):
        f.unlink()

    tts2 = FakeTTS()
    cache = MediaCache(db_path=tmp_path / "cache.db")
    gen2 = AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts2,
        media_dir=media,
        cache=cache,
    )
    out2 = tmp_path / "b.apkg"
    gen2.generate_deck(sample_csv, out2)

    # All three audio files must have been regenerated and exist on disk.
    assert len(tts2.calls) == 3
    assert sorted(p.name for p in media.glob("audio_*.mp3")) == [
        "audio_apple_0.mp3",
        "audio_book_2.mp3",
        "audio_house_1.mp3",
    ]
    assert out2.exists()


def test_deleted_image_regenerates_only_image_not_audio(tmp_path: Path, sample_csv: Path) -> None:
    """Missing image must not force TTS to re-run (#22 independence)."""
    tts1 = FakeTTS()
    imgs1 = FakeImages()
    gen1 = _make_generator(tmp_path, tts1, imgs1, generate_images=True)
    gen1.generate_deck(sample_csv, tmp_path / "a.apkg")
    assert len(tts1.calls) == 3
    assert len(imgs1.calls) == 3

    # Delete only the images.
    media = tmp_path / "media"
    for f in media.glob("image_*.png"):
        f.unlink()

    tts2 = FakeTTS()
    imgs2 = FakeImages()
    cache = MediaCache(db_path=tmp_path / "cache.db")
    gen2 = AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts2,
        generate_images=True,
        image_provider=imgs2,
        media_dir=media,
        cache=cache,
    )
    gen2.generate_deck(sample_csv, tmp_path / "b.apkg")

    # Audio still cached -> TTS not invoked.
    assert tts2.calls == []
    # Images regenerated.
    assert len(imgs2.calls) == 3
    assert len(list(media.glob("image_*.png"))) == 3


def test_deleted_audio_regenerates_only_audio_not_image(tmp_path: Path, sample_csv: Path) -> None:
    """Missing audio must not force image generation to re-run (#22 independence)."""
    tts1 = FakeTTS()
    imgs1 = FakeImages()
    gen1 = _make_generator(tmp_path, tts1, imgs1, generate_images=True)
    gen1.generate_deck(sample_csv, tmp_path / "a.apkg")

    media = tmp_path / "media"
    for f in media.glob("audio_*.mp3"):
        f.unlink()

    tts2 = FakeTTS()
    imgs2 = FakeImages()
    cache = MediaCache(db_path=tmp_path / "cache.db")
    gen2 = AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts2,
        generate_images=True,
        image_provider=imgs2,
        media_dir=media,
        cache=cache,
    )
    gen2.generate_deck(sample_csv, tmp_path / "b.apkg")

    assert len(tts2.calls) == 3
    assert imgs2.calls == []
    assert len(list(media.glob("audio_*.mp3"))) == 3


def test_previous_tts_failure_is_not_retried_on_cache_hit(tmp_path: Path, sample_csv: Path) -> None:
    """Cache recording ``None`` for audio is preserved, matching prior behaviour."""
    failing = FakeTTS(should_fail=True)
    gen1 = _make_generator(tmp_path, failing)
    gen1.generate_deck(sample_csv, tmp_path / "a.apkg")
    assert len(failing.calls) == 3  # attempted but all failed

    tts2 = FakeTTS()  # would succeed if called
    cache = MediaCache(db_path=tmp_path / "cache.db")
    gen2 = AnkiDeckGenerator(
        deck_name="Test Deck",
        tts_provider=tts2,
        media_dir=tmp_path / "media",
        cache=cache,
    )
    gen2.generate_deck(sample_csv, tmp_path / "b.apkg")
    # Prior None entries are cache hits; no retry.
    assert tts2.calls == []
