"""Anita command-line interface."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from anita import __version__
from anita.cache import MediaCache
from anita.deck import AnkiDeckGenerator

app = typer.Typer(
    name="anita",
    help="Generate Anki decks with AI-generated audio and illustrations.",
    no_args_is_help=True,
    add_completion=False,
)

cache_app = typer.Typer(
    name="cache",
    help="Inspect and manage Anita's on-disk media cache.",
    no_args_is_help=True,
)
app.add_typer(cache_app, name="cache")


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


# ------------------------------------------------------------------ cache cmds


@cache_app.command("path")
def cache_path() -> None:
    """Print the full path to Anita's cache database."""
    typer.echo(str(MediaCache().db_path))


@cache_app.command("show")
def cache_show(
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON instead of a table."),
    ] = False,
) -> None:
    """List cached (source, target, audio?, image?) rows."""
    cache = MediaCache()
    rows = cache.iter_rows()

    if as_json:
        payload = [
            {
                "source": s,
                "target": t,
                "image_fname": img,
                "audio_fname": aud,
            }
            for s, t, img, aud in rows
        ]
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if not rows:
        typer.echo("(cache is empty)")
        return

    # Simple left-aligned columns; no deps on rich/tabulate.
    src_w = max(6, max(len(s) for s, _, _, _ in rows))
    tgt_w = max(6, max(len(t) for _, t, _, _ in rows))
    header = f"{'source':<{src_w}}  {'target':<{tgt_w}}  audio  image"
    typer.echo(header)
    typer.echo("-" * len(header))
    for s, t, img, aud in rows:
        typer.echo(
            f"{s:<{src_w}}  {t:<{tgt_w}}  {'yes' if aud else 'no ':<5}  {'yes' if img else 'no'}"
        )
    typer.echo(f"\n{len(rows)} row(s)")


@cache_app.command("clear")
def cache_clear(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
) -> None:
    """Delete Anita's cache database."""
    from anita.cache import default_cache_dir

    # Resolve the path without triggering MediaCache's side-effecting init,
    # so "already empty" reports truthfully on a never-used installation.
    path = default_cache_dir() / "generated_cards.db"
    if not path.exists():
        typer.echo(f"Cache already empty: {path}")
        return
    if not yes:
        confirm = typer.confirm(f"Delete cache database at {path}?", default=False)
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(code=1)
    path.unlink()
    typer.echo(f"Removed {path}")


@cache_app.command("prune")
def cache_prune(
    missing_media: Annotated[
        Path,
        typer.Option(
            "--missing-media",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Media directory to reconcile against.",
        ),
    ],
) -> None:
    """Remove cache entries whose media files are gone from --missing-media."""
    cache = MediaCache()
    removed = cache.prune_missing(missing_media)
    remaining = cache.count()
    typer.echo(f"Pruned {removed} row(s); {remaining} remain.")


if __name__ == "__main__":  # pragma: no cover
    app()
