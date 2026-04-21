from __future__ import annotations

from anita.model import build_model, stable_id


def test_stable_id_is_deterministic() -> None:
    assert stable_id("My Deck") == stable_id("My Deck")


def test_stable_id_differs_by_name() -> None:
    assert stable_id("Deck A") != stable_id("Deck B")


def test_stable_id_fits_32_bits() -> None:
    assert 0 <= stable_id("anything") < 2**32


def test_build_model_has_expected_fields() -> None:
    model = build_model()
    field_names = [f["name"] for f in model.fields]
    assert field_names == ["Source", "Target", "Audio", "Image"]
    assert len(model.templates) == 1
