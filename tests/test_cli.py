from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from anita.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "anita" in result.stdout


def test_help_shows_generate() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout


def test_generate_missing_key_reports_error(tmp_path: Path, monkeypatch, sample_csv: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    out = tmp_path / "out.apkg"
    result = runner.invoke(app, ["generate", str(sample_csv), str(out)])
    assert result.exit_code == 1
    assert "OPENAI_API_KEY" in (result.stderr or result.stdout)


def test_generate_happy_path(tmp_path: Path, sample_csv: Path, mocker: Any) -> None:
    """The CLI command wires args through to AnkiDeckGenerator and reports success."""
    fake_generator = mocker.MagicMock()
    fake_generator.generate_deck.return_value = tmp_path / "deck.apkg"
    ctor = mocker.patch("anita.cli.AnkiDeckGenerator", return_value=fake_generator)

    out = tmp_path / "deck.apkg"
    result = runner.invoke(
        app,
        [
            "generate",
            str(sample_csv),
            str(out),
            "--deck-name",
            "My Deck",
            "--images",
            "--media-dir",
            str(tmp_path / "media"),
        ],
    )

    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    assert "Deck written" in result.stdout
    # Constructor received the expected wiring.
    ctor.assert_called_once()
    kwargs = ctor.call_args.kwargs
    assert kwargs["deck_name"] == "My Deck"
    assert kwargs["tts_provider"] == "openai"
    assert kwargs["generate_images"] is True
    assert kwargs["media_dir"] == tmp_path / "media"
    fake_generator.generate_deck.assert_called_once_with(sample_csv, out)


def test_generate_verbose_flag_does_not_break(
    tmp_path: Path, sample_csv: Path, mocker: Any
) -> None:
    fake_generator = mocker.MagicMock()
    mocker.patch("anita.cli.AnkiDeckGenerator", return_value=fake_generator)

    out = tmp_path / "deck.apkg"
    result = runner.invoke(app, ["generate", str(sample_csv), str(out), "--verbose"])
    assert result.exit_code == 0


# ------------------------------------------------------------------ cache cmds


@pytest.fixture
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect Anita's default cache dir at a per-test tmp path."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr("anita.cache.default_cache_dir", lambda: cache_dir)
    return cache_dir


def test_cache_path_prints_db_location(isolated_cache: Path) -> None:
    result = runner.invoke(app, ["cache", "path"])
    assert result.exit_code == 0
    assert str(isolated_cache / "generated_cards.db") in result.stdout


def test_cache_show_empty(isolated_cache: Path) -> None:
    result = runner.invoke(app, ["cache", "show"])
    assert result.exit_code == 0
    assert "empty" in result.stdout.lower()


def test_cache_show_table_lists_rows(isolated_cache: Path) -> None:
    from anita.cache import MediaCache

    cache = MediaCache()
    cache.put("apple", "mela", "i.png", "a.mp3")
    cache.put("house", "casa", None, "b.mp3")

    result = runner.invoke(app, ["cache", "show"])
    assert result.exit_code == 0
    assert "apple" in result.stdout
    assert "house" in result.stdout
    assert "2 row" in result.stdout


def test_cache_show_json_is_parseable(isolated_cache: Path) -> None:
    import json

    from anita.cache import MediaCache

    cache = MediaCache()
    cache.put("apple", "mela", "i.png", "a.mp3")

    result = runner.invoke(app, ["cache", "show", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == [
        {
            "source": "apple",
            "target": "mela",
            "image_fname": "i.png",
            "audio_fname": "a.mp3",
        }
    ]


def test_cache_clear_with_yes_flag(isolated_cache: Path) -> None:
    from anita.cache import MediaCache

    cache = MediaCache()
    cache.put("apple", "mela", "i.png", "a.mp3")
    assert cache.db_path.exists()

    result = runner.invoke(app, ["cache", "clear", "--yes"])
    assert result.exit_code == 0
    assert "Removed" in result.stdout
    assert not cache.db_path.exists()


def test_cache_clear_already_empty(isolated_cache: Path) -> None:
    result = runner.invoke(app, ["cache", "clear", "--yes"])
    assert result.exit_code == 0
    assert "already empty" in result.stdout.lower()


def test_cache_clear_prompt_accepts(isolated_cache: Path) -> None:
    from anita.cache import MediaCache

    cache = MediaCache()
    cache.put("apple", "mela", "i.png", "a.mp3")

    result = runner.invoke(app, ["cache", "clear"], input="y\n")
    assert result.exit_code == 0
    assert not cache.db_path.exists()


def test_cache_clear_prompt_aborts(isolated_cache: Path) -> None:
    from anita.cache import MediaCache

    cache = MediaCache()
    cache.put("apple", "mela", "i.png", "a.mp3")

    result = runner.invoke(app, ["cache", "clear"], input="n\n")
    assert result.exit_code == 1
    assert cache.db_path.exists()


def test_cache_prune_removes_missing(tmp_path: Path, isolated_cache: Path) -> None:
    from anita.cache import MediaCache

    media = tmp_path / "media"
    media.mkdir()
    (media / "a1.mp3").write_bytes(b"x")

    cache = MediaCache()
    cache.put("apple", "mela", None, "a1.mp3")  # audio present
    cache.put("house", "casa", "gone.png", "gone.mp3")  # both gone

    result = runner.invoke(app, ["cache", "prune", "--missing-media", str(media)])
    assert result.exit_code == 0
    assert "Pruned 1" in result.stdout
    assert "1 remain" in result.stdout
