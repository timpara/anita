from __future__ import annotations

from pathlib import Path
from typing import Any

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
