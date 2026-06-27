"""Text-to-speech provider implementations."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Protocol

import openai
from openai import APIConnectionError, APITimeoutError, RateLimitError

from anita.providers.retry import TRANSIENT_NETWORK_ERRORS, retry_with_backoff

log = logging.getLogger(__name__)

# OpenAI SDK exceptions that are safe to retry (transient).
_OPENAI_RETRYABLE: tuple[type[Exception], ...] = (
    *TRANSIENT_NETWORK_ERRORS,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
)


class TTSProvider(Protocol):
    """Protocol every TTS backend implements."""

    name: str

    def synthesize(self, text: str, output_path: Path) -> bool:
        """Render ``text`` to the given file. Return True on success."""
        ...


class OpenAITTS:
    """OpenAI ``tts-1`` implementation."""

    name = "openai"

    def __init__(self, voice: str = "alloy", model: str = "tts-1") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        self._client = openai.OpenAI(api_key=api_key)
        self.voice = voice
        self.model = model

    def synthesize(self, text: str, output_path: Path) -> bool:
        def _call() -> bool:
            # pad with whitespace so players don't clip the first/last phoneme
            response = self._client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=f" \n{text}\n ",
            )
            response.stream_to_file(output_path)
            return True

        try:
            return retry_with_backoff(_call, retryable=_OPENAI_RETRYABLE)
        except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
            log.error("OpenAI TTS failed for %r after retries: %s", text, exc)
            return False
        except openai.BadRequestError as exc:
            # Permanent failure (e.g., input too long, invalid params).
            log.error("OpenAI TTS rejected request for %r: %s", text, exc)
            return False
        except openai.AuthenticationError as exc:
            log.error("OpenAI TTS auth failed (check OPENAI_API_KEY): %s", exc)
            return False


class ElevenLabsTTS:
    """ElevenLabs multilingual v2 implementation."""

    name = "elevenlabs"
    DEFAULT_VOICE_ID = "CiwzbDpaN3pQXjTgx3ML"

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str = "eleven_multilingual_v2",
    ) -> None:
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError as exc:
            raise ImportError(
                "The 'elevenlabs' extra is not installed. "
                "Install with: pip install 'anita-anki[elevenlabs]'."
            ) from exc

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise RuntimeError("ELEVENLABS_API_KEY environment variable is not set.")

        self._client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id or self.DEFAULT_VOICE_ID
        self.model_id = model_id

    def synthesize(self, text: str, output_path: Path) -> bool:
        def _call() -> bool:
            audio = self._client.text_to_speech.convert(
                text=f" \n{text}\n ",
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",
            )
            with output_path.open("wb") as fh:
                for chunk in audio:
                    fh.write(chunk)
            return True

        try:
            return retry_with_backoff(_call, retryable=TRANSIENT_NETWORK_ERRORS)
        except (*TRANSIENT_NETWORK_ERRORS,) as exc:
            log.error("ElevenLabs TTS failed for %r after retries: %s", text, exc)
            return False


def build_tts(provider: str, **kwargs: object) -> TTSProvider:
    """Factory: return a configured TTS provider by short name."""
    key = provider.lower()
    if key == "openai":
        return OpenAITTS(**kwargs)  # type: ignore[arg-type]
    if key == "elevenlabs":
        return ElevenLabsTTS(**kwargs)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported TTS provider: {provider!r}. Choose 'openai' or 'elevenlabs'.")
