"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from anita.cache import MediaCache


@pytest.fixture
def cache(tmp_path: Path) -> MediaCache:
    """A MediaCache backed by a tmp SQLite DB."""
    return MediaCache(db_path=tmp_path / "cache.db")


@pytest.fixture
def media_dir(tmp_path: Path) -> Path:
    path = tmp_path / "media"
    path.mkdir()
    return path


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    csv = tmp_path / "words.csv"
    csv.write_text("apple,mela\nhouse,casa\nbook,libro\n", encoding="utf-8")
    return csv


@pytest.fixture
def sample_csv_with_header(tmp_path: Path) -> Path:
    csv = tmp_path / "words_header.csv"
    csv.write_text("source,target\napple,mela\nhouse,casa\n", encoding="utf-8")
    return csv


class FakeTTS:
    """Stub TTS provider that writes a deterministic payload."""

    name = "fake-tts"

    def __init__(self, should_fail: bool = False) -> None:
        self.calls: list[tuple[str, Path]] = []
        self.should_fail = should_fail

    def synthesize(self, text: str, output_path: Path) -> bool:
        self.calls.append((text, output_path))
        if self.should_fail:
            return False
        output_path.write_bytes(b"ID3fake-mp3-bytes")
        return True


class FakeImages:
    name = "fake-images"

    def __init__(self, should_fail: bool = False) -> None:
        self.calls: list[tuple[str, Path]] = []
        self.should_fail = should_fail

    def generate(self, prompt: str, output_path: Path) -> bool:
        self.calls.append((prompt, output_path))
        if self.should_fail:
            return False
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        return True


@pytest.fixture
def fake_tts() -> FakeTTS:
    return FakeTTS()


@pytest.fixture
def fake_images() -> FakeImages:
    return FakeImages()
