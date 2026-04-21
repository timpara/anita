"""Anita command-line interface."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from anita import __version__
from anita.deck import AnkiDeckGenerator

app = typer.Typer(
    name="anita",
    help="Generate Anki decks with AI-generated audio and illustrations.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(show: bool) -> None:
    if show:
        typer.echo(f"anita {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
        ),
    ] = False,
) -> None:
    """Anita — AI-powered Anki deck generator."""
    # Auto-load .env from cwd if present; ignored silently otherwise.
    load_dotenv()


@app.command()
def generate(
    input_csv: Annotated[
        Path,
        typer.Argument(
            exists=True, readable=True, dir_okay=False, help="Two-column CSV: source,target."
        ),
    ],
    output_apkg: Annotated[
        Path,
        typer.Argument(dir_okay=False, help="Path to write the Anki .apkg file."),
    ],
    deck_name: Annotated[
        str, typer.Option("--deck-name", "-n", help="Deck name as shown in Anki.")
    ] = "Anita Vocabulary",
    tts: Annotated[
        str, typer.Option("--tts", help="TTS provider: 'openai' or 'elevenlabs'.")
    ] = "openai",
    images: Annotated[
        bool, typer.Option("--images/--no-images", help="Generate DALL·E illustrations.")
    ] = False,
    voice_id: Annotated[
        str | None,
        typer.Option("--voice-id", help="Voice ID (ElevenLabs only)."),
    ] = None,
    media_dir: Annotated[
        Path,
        typer.Option("--media-dir", help="Where to store generated media files."),
    ] = Path("media"),
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging.")] = False,
) -> None:
    """Build an Anki deck from a CSV of source,target word pairs."""
    _configure_logging(verbose)
    try:
        generator = AnkiDeckGenerator(
            deck_name=deck_name,
            tts_provider=tts,
            elevenlabs_voice_id=voice_id,
            generate_images=images,
            media_dir=media_dir,
        )
        generator.generate_deck(input_csv, output_apkg)
        typer.echo(f"✓ Deck written: {output_apkg}")
    except (FileNotFoundError, ValueError, RuntimeError, ImportError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
