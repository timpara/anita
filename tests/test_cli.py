from __future__ import annotations

from pathlib import Path

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
