from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from anita.providers.images import OpenAIImageProvider
from anita.providers.tts import OpenAITTS, build_tts


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


# ---- OpenAITTS -------------------------------------------------------------


class _FakeSpeechResponse:
    def __init__(self, payload: bytes = b"ID3fake") -> None:
        self.payload = payload

    def stream_to_file(self, path: Path) -> None:
        Path(path).write_bytes(self.payload)


def _stub_openai_client(mocker: Any, *, raise_exc: Exception | None = None) -> Any:
    """Return a mock replacement for openai.OpenAI(...)."""
    client = mocker.MagicMock()
    if raise_exc is not None:
        client.audio.speech.create.side_effect = raise_exc
    else:
        client.audio.speech.create.return_value = _FakeSpeechResponse()
    return client


def test_openai_tts_synthesize_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mocker.patch("anita.providers.tts.openai.OpenAI", return_value=_stub_openai_client(mocker))

    provider = OpenAITTS()
    out = tmp_path / "out.mp3"
    assert provider.synthesize("hello", out) is True
    assert out.read_bytes() == b"ID3fake"


def test_openai_tts_synthesize_returns_false_on_api_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mocker.patch(
        "anita.providers.tts.openai.OpenAI",
        return_value=_stub_openai_client(mocker, raise_exc=RuntimeError("boom")),
    )
    provider = OpenAITTS()
    assert provider.synthesize("hello", tmp_path / "out.mp3") is False


def test_build_tts_openai_returns_instance(monkeypatch: pytest.MonkeyPatch, mocker: Any) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mocker.patch("anita.providers.tts.openai.OpenAI", return_value=mocker.MagicMock())
    tts = build_tts("openai")
    assert tts.name == "openai"


# ---- OpenAIImageProvider ---------------------------------------------------


class _FakeImageResponseData:
    def __init__(self, url: str | None) -> None:
        self.url = url


class _FakeImageResponse:
    def __init__(self, url: str | None = "https://example/image.png") -> None:
        self.data = [_FakeImageResponseData(url)] if url is not None else []


def _tiny_png_bytes() -> bytes:
    """A minimal valid PNG that Pillow can open."""
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (16, 16), (255, 255, 255)).save(buf, "PNG")
    return buf.getvalue()


def test_openai_image_provider_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIImageProvider()


def test_openai_image_provider_generate_happy_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = mocker.MagicMock()
    client.images.generate.return_value = _FakeImageResponse()
    mocker.patch("anita.providers.images.openai.OpenAI", return_value=client)

    http_resp = mocker.MagicMock()
    http_resp.content = _tiny_png_bytes()
    http_resp.raise_for_status.return_value = None
    mocker.patch("anita.providers.images.requests.get", return_value=http_resp)

    provider = OpenAIImageProvider()
    out = tmp_path / "img.png"
    assert provider.generate("an apple", out) is True
    assert out.exists()
    # After _optimize the file is a 128x128 PNG.
    from PIL import Image

    with Image.open(out) as img:
        assert img.size == (128, 128)


def test_openai_image_provider_returns_false_when_no_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = mocker.MagicMock()
    client.images.generate.return_value = _FakeImageResponse(url=None)
    mocker.patch("anita.providers.images.openai.OpenAI", return_value=client)

    provider = OpenAIImageProvider()
    assert provider.generate("nothing", tmp_path / "nope.png") is False


def test_openai_image_provider_returns_false_on_http_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = mocker.MagicMock()
    client.images.generate.return_value = _FakeImageResponse()
    mocker.patch("anita.providers.images.openai.OpenAI", return_value=client)
    mocker.patch(
        "anita.providers.images.requests.get",
        side_effect=RuntimeError("connection refused"),
    )

    provider = OpenAIImageProvider()
    assert provider.generate("boom", tmp_path / "out.png") is False


def test_openai_image_provider_optimize_handles_corrupt_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: Any
) -> None:
    """Optimization failure is logged but does not fail the overall call."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = mocker.MagicMock()
    client.images.generate.return_value = _FakeImageResponse()
    mocker.patch("anita.providers.images.openai.OpenAI", return_value=client)

    http_resp = mocker.MagicMock()
    http_resp.content = b"not a real png"
    http_resp.raise_for_status.return_value = None
    mocker.patch("anita.providers.images.requests.get", return_value=http_resp)

    provider = OpenAIImageProvider()
    # generate still returns True — optimization failure only warns.
    assert provider.generate("prompt", tmp_path / "bad.png") is True
