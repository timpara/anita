"""Deck orchestrator — glues CSV input, providers, cache, and genanki together."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import genanki

from anita.cache import MediaCache
from anita.model import build_model, stable_id
from anita.providers.images import ImageProvider, OpenAIImageProvider
from anita.providers.tts import TTSProvider, build_tts

log = logging.getLogger(__name__)


class AnkiDeckGenerator:
    """Generate an Anki ``.apkg`` from a two-column CSV of word pairs."""

    def __init__(
        self,
        deck_name: str = "Anita Vocabulary",
        deck_id: int | None = None,
        media_dir: Path | str | None = None,
        tts_provider: str | TTSProvider = "openai",
        elevenlabs_voice_id: str | None = None,
        generate_images: bool = False,
        image_provider: ImageProvider | None = None,
        cache: MediaCache | None = None,
    ) -> None:
        self.deck_name = deck_name
        self.deck_id = deck_id if deck_id is not None else stable_id(deck_name)
        self.media_dir = Path(media_dir) if media_dir else Path("media")
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.generate_images = generate_images
        self.cache = cache or MediaCache()
        self.model = build_model()
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.package = genanki.Package(self.deck)

        # Resolve TTS provider
        if isinstance(tts_provider, str):
            tts_kwargs: dict[str, object] = {}
            if tts_provider.lower() == "elevenlabs" and elevenlabs_voice_id:
                tts_kwargs["voice_id"] = elevenlabs_voice_id
            self.tts: TTSProvider = build_tts(tts_provider, **tts_kwargs)
        else:
            self.tts = tts_provider

        # Resolve image provider lazily: only instantiate when enabled
        self.images: ImageProvider | None
        if generate_images:
            self.images = image_provider or OpenAIImageProvider()
        else:
            self.images = None

    # ------------------------------------------------------------------ public

    def generate_deck(self, input_csv: Path | str, output_apkg: Path | str) -> Path:
        """Build a deck from ``input_csv`` and write it to ``output_apkg``."""
        input_path = Path(input_csv)
        output_path = Path(output_apkg)

        if not input_path.is_file():
            raise FileNotFoundError(f"Input CSV not found: {input_path}")

        pairs = list(_read_csv(input_path))
        if not pairs:
            raise ValueError(f"No usable rows in CSV: {input_path}")

        log.info("Building deck %r from %d rows", self.deck_name, len(pairs))

        for idx, (source, target) in enumerate(pairs):
            log.info("Processing %d/%d: %s → %s", idx + 1, len(pairs), source, target)
            audio_fname, image_fname = self._materialize_pair(idx, source, target)

            audio_field = f"[sound:{audio_fname}]" if audio_fname else ""
            image_field = f'<img src="{image_fname}">' if image_fname else ""

            note = genanki.Note(
                model=self.model,
                fields=[source, target, audio_field, image_field],
            )
            self.deck.add_note(note)

        self.package.write_to_file(output_path)
        log.info("Deck written to %s", output_path)
        return output_path

    # --------------------------------------------------------------- internals

    def _materialize_pair(
        self, idx: int, source: str, target: str
    ) -> tuple[str | None, str | None]:
        cached = self.cache.get(source, target)
        if cached is not None:
            cached_image, cached_audio = cached
            cache_hit = True
        else:
            cached_image, cached_audio = None, None
            cache_hit = False

        # Reconcile the cache index against the media directory: a filename
        # that is no longer on disk must be regenerated, even on a cache hit.
        # Audio and image are reconciled independently so a missing image
        # doesn't force TTS to re-run (and vice versa).
        audio_fname = self._reconcile_audio(idx, source, target, cached_audio, cache_hit)
        image_fname = self._reconcile_image(idx, source, target, cached_image, cache_hit)

        # Persist whatever the current truth is (new, regenerated, or
        # unchanged) so the index matches disk. Always write on a cache miss
        # so that known-failed generations are remembered.
        if not cache_hit or (image_fname, audio_fname) != (cached_image, cached_audio):
            self.cache.put(source, target, image_fname, audio_fname)

        if audio_fname:
            self.package.media_files.append(str(self.media_dir / audio_fname))
        if image_fname:
            self.package.media_files.append(str(self.media_dir / image_fname))

        return audio_fname, image_fname

    def _reconcile_audio(
        self,
        idx: int,
        source: str,
        target: str,
        cached_fname: str | None,
        cache_hit: bool,
    ) -> str | None:
        """Return the audio filename to use, regenerating if the file is gone.

        A recorded ``None`` in the cache means TTS failed on a prior run and
        is preserved as-is, consistent with the pre-existing behaviour of
        not retrying known-failed generations.
        """
        if cache_hit and cached_fname is None:
            return None
        if cached_fname and (self.media_dir / cached_fname).is_file():
            log.debug("Audio cache hit for %s/%s", source, target)
            return cached_fname

        if cached_fname:
            log.info(
                "Cache listed audio %s for %s/%s but file is missing; regenerating",
                cached_fname,
                source,
                target,
            )

        safe = _safe_slug(source)
        audio_fname = cached_fname or f"audio_{safe}_{idx}.mp3"
        audio_path = self.media_dir / audio_fname
        if self.tts.synthesize(target, audio_path):
            return audio_fname
        return None

    def _reconcile_image(
        self,
        idx: int,
        source: str,
        target: str,
        cached_fname: str | None,
        cache_hit: bool,
    ) -> str | None:
        """Return the image filename to use, regenerating if the file is gone.

        A recorded ``None`` in the cache means image generation failed on a
        prior run and is preserved.
        """
        if not self.generate_images or self.images is None:
            return None

        if cache_hit and cached_fname is None:
            return None
        if cached_fname and (self.media_dir / cached_fname).is_file():
            log.debug("Image cache hit for %s/%s", source, target)
            return cached_fname

        if cached_fname:
            log.info(
                "Cache listed image %s for %s/%s but file is missing; regenerating",
                cached_fname,
                source,
                target,
            )

        safe = _safe_slug(source)
        image_fname = cached_fname or f"image_{safe}_{idx}.png"
        image_path = self.media_dir / image_fname
        if self.images.generate(source, image_path):
            return image_fname
        return None


# ---------------------------------------------------------------------- helpers


def _safe_slug(text: str) -> str:
    return "".join(c for c in text if c.isalnum()) or "item"


def _read_csv(path: Path) -> list[tuple[str, str]]:
    """Read two-column CSV, skipping a header row if detected, dropping bad rows."""
    with path.open(newline="", encoding="utf-8") as fh:
        sample = fh.read(2048)
        fh.seek(0)
        has_header = False
        try:
            has_header = csv.Sniffer().has_header(sample)
        except csv.Error:
            has_header = False

        reader = csv.reader(fh)
        rows = list(reader)

    if has_header and rows:
        rows = rows[1:]

    pairs: list[tuple[str, str]] = []
    for lineno, row in enumerate(rows, start=2 if has_header else 1):
        if len(row) < 2:
            log.warning("Skipping line %d (need 2 columns): %r", lineno, row)
            continue
        source = row[0].strip()
        target = row[1].strip()
        if not source or not target:
            log.warning("Skipping line %d (empty cell): %r", lineno, row)
            continue
        pairs.append((source, target))
    return pairs
