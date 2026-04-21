"""Image-generation providers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Protocol

import openai
import requests
from PIL import Image

log = logging.getLogger(__name__)


class ImageProvider(Protocol):
    name: str

    def generate(self, prompt: str, output_path: Path) -> bool: ...


class OpenAIImageProvider:
    """DALL·E 2 illustrations, auto-resized to a small square for Anki."""

    name = "openai-dalle2"

    def __init__(
        self,
        model: str = "dall-e-2",
        size: str = "256x256",
        target_size: tuple[int, int] = (128, 128),
        request_timeout: float = 30.0,
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.size = size
        self.target_size = target_size
        self.request_timeout = request_timeout

    def generate(self, prompt: str, output_path: Path) -> bool:
        try:
            response = self._client.images.generate(  # type: ignore[call-overload]
                model=self.model,
                prompt=f"{prompt}, simple illustration, clean, minimal, white background",
                n=1,
                size=self.size,
            )
            url = response.data[0].url if response.data else None
            if not url:
                log.error("Image generation returned no URL for %r", prompt)
                return False

            resp = requests.get(url, timeout=self.request_timeout)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
            self._optimize(output_path)
            return True
        except Exception as exc:
            log.error("Image generation failed for %r: %s", prompt, exc)
            return False

    def _optimize(self, image_path: Path) -> None:
        try:
            with Image.open(image_path) as img:
                # Pillow 12's stubs distinguish ImageFile (what open() returns)
                # from Image (what convert/resize return), so use a new binding
                # for the transformed image rather than reassigning `img`.
                converted: Image.Image = img.convert("RGB") if img.mode == "RGBA" else img
                resized = converted.resize(self.target_size, Image.Resampling.LANCZOS)
                resized.save(image_path, "PNG", optimize=True)
        except Exception as exc:
            log.warning("Image optimization failed for %s: %s", image_path, exc)
