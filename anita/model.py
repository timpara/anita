"""Anki note model / template factory."""

from __future__ import annotations

import hashlib

import genanki

_CSS = """
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
img {
    max-width: 128px;
    height: auto;
}
"""

_AFMT = """
{{FrontSide}}
<hr id="answer">
{{Target}}<br>
{{Audio}}<br><br>
<div style="max-width: 128px; margin: auto;">
    {{Image}}
</div>
"""


def build_model(model_id: int | None = None) -> genanki.Model:
    """Build the default Anita Anki model.

    Args:
        model_id: Override the deterministic model ID. When ``None`` a stable ID is
            derived from the model name so re-imports update the same model in Anki.
    """
    name = "Anita Vocabulary Model"
    mid = model_id if model_id is not None else stable_id(name)
    return genanki.Model(
        mid,
        name,
        fields=[
            {"name": "Source"},
            {"name": "Target"},
            {"name": "Audio"},
            {"name": "Image"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Source}}",
                "afmt": _AFMT,
            },
        ],
        css=_CSS,
    )


def stable_id(key: str) -> int:
    """Return a deterministic 32-bit unsigned ID derived from a string.

    Using a hash instead of a hard-coded number avoids deck/model ID collisions between
    users while keeping the ID stable across runs for the same name.
    """
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)
