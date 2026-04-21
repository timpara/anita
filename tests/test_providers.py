from __future__ import annotations

import pytest
from anita.providers.tts import build_tts


def test_build_tts_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Unsupported TTS"):
        build_tts("does-not-exist")


def test_build_tts_openai_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_tts("openai")


def test_build_tts_elevenlabs_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    # If elevenlabs package isn't installed the error is ImportError; if it is, it's RuntimeError.
    with pytest.raises((RuntimeError, ImportError)):
        build_tts("elevenlabs")
