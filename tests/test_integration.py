"""End-to-end integration test for produced .apkg archives.

Unlike the unit tests, this exercises the full deck-build pipeline and then
cracks open the resulting ``.apkg`` (a zip of a SQLite collection plus media
blobs) to assert the on-disk structure that Anki will actually consume.

The provider stubs from ``conftest`` keep this offline and fast.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

from anita.cache import MediaCache
from anita.deck import AnkiDeckGenerator

from .conftest import FakeImages, FakeTTS

# Anki stores note fields separated by the unit-separator control char.
FIELD_SEPARATOR = "\x1f"


def test_generated_apkg_has_valid_structure(tmp_path: Path) -> None:
    """Build a deck end-to-end and validate the .apkg archive contents."""
    csv_path = tmp_path / "words.csv"
    csv_path.write_text("apple,mela\nhouse,casa\n", encoding="utf-8")

    apkg_path = tmp_path / "deck.apkg"
    deck_name = "Integration Test Deck"

    generator = AnkiDeckGenerator(
        deck_name=deck_name,
        tts_provider=FakeTTS(),
        generate_images=True,
        image_provider=FakeImages(),
        media_dir=tmp_path / "media",
        cache=MediaCache(db_path=tmp_path / "cache.db"),
    )
    generator.generate_deck(csv_path, apkg_path)

    assert apkg_path.exists(), "generator should produce an .apkg file"

    with zipfile.ZipFile(apkg_path) as archive:
        names = set(archive.namelist())

        # Archive must contain the collection, the media manifest, and the
        # numbered media blobs (one audio + one image per note = 4 blobs).
        assert "collection.anki2" in names
        assert "media" in names
        for idx in range(4):
            assert str(idx) in names, f"missing media blob {idx}"

        manifest = json.loads(archive.read("media").decode("utf-8"))
        # Manifest maps stringified indices to filenames used inside note fields.
        filenames = set(manifest.values())
        assert any(name.startswith("audio_apple") for name in filenames)
        assert any(name.startswith("audio_house") for name in filenames)
        assert any(name.startswith("image_apple") for name in filenames)
        assert any(name.startswith("image_house") for name in filenames)
        # Each manifest entry must correspond to a real blob in the archive.
        assert set(manifest.keys()) == {str(i) for i in range(len(manifest))}

        # Extract the SQLite collection so we can query it.
        extract_dir = tmp_path / "extracted"
        archive.extractall(extract_dir)

    collection_path = extract_dir / "collection.anki2"
    connection = sqlite3.connect(collection_path)
    try:
        cursor = connection.cursor()

        # Two CSV rows → two notes → two cards.
        (note_count,) = cursor.execute("SELECT COUNT(*) FROM notes").fetchone()
        (card_count,) = cursor.execute("SELECT COUNT(*) FROM cards").fetchone()
        assert note_count == 2
        assert card_count == 2

        # Validate the four fields per note: Source, Target, Audio, Image.
        rows = [row[0].split(FIELD_SEPARATOR) for row in cursor.execute("SELECT flds FROM notes")]
        sources = {row[0] for row in rows}
        targets = {row[1] for row in rows}
        assert sources == {"apple", "house"}
        assert targets == {"mela", "casa"}
        for fields in rows:
            assert len(fields) == 4, f"expected 4 fields, got {fields!r}"
            audio, image = fields[2], fields[3]
            assert audio.startswith("[sound:") and audio.endswith(".mp3]")
            assert '<img src="' in image and image.endswith('.png">')

        # The `col` row carries model + deck metadata as JSON blobs.
        models_json, decks_json = cursor.execute("SELECT models, decks FROM col").fetchone()
        models = json.loads(models_json)
        assert len(models) == 1, "expected exactly one note model"
        (model,) = models.values()
        assert model["name"] == "Anita Vocabulary Model"
        assert [f["name"] for f in model["flds"]] == ["Source", "Target", "Audio", "Image"]

        decks = json.loads(decks_json)
        deck_names = {deck["name"] for deck in decks.values()}
        # genanki always ships a "Default" deck alongside the one we requested.
        assert deck_name in deck_names
    finally:
        connection.close()
