# Anita — AI-Powered Anki Deck Generator

[![CI](https://github.com/timpara/anita/actions/workflows/ci.yml/badge.svg)](https://github.com/timpara/anita/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/badge/packaging-uv-261230)](https://github.com/astral-sh/uv)

Turn a plain CSV of word pairs into a rich, multimedia [Anki](https://apps.ankiweb.net/) deck
with AI-generated native-like pronunciations and optional illustrations — in minutes, for any
language pair.

## Why Anita?

Language learners lose hours building decent flashcards by hand. Anita automates the tedious
part — generating TTS audio (OpenAI or ElevenLabs) and optional DALL·E images — so you can
focus on reviewing, not curating. Feed it a CSV, get back a `.apkg` you can import straight
into Anki on desktop or mobile.

## Table of contents

- [Features](#features)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [Usage](#usage)
- [CSV format](#csv-format)
- [Configuration](#configuration)
- [Cost estimate](#cost-estimate)
- [Cache](#cache)
- [Contributing](#contributing)
- [License](#license)
- [Supply chain](#supply-chain)

## Features

- **CSV in, `.apkg` out** — point it at a two-column CSV and get a ready-to-import Anki deck.
- **Pluggable TTS** — OpenAI `tts-1` by default, ElevenLabs multilingual v2 optional.
- **Optional illustrations** — DALL·E 2 images auto-resized to 128×128 px for clean cards.
- **Local media cache** — every generated asset is cached in a SQLite DB so repeat runs are
  free and fast. See [Cache](#cache) for location and lifecycle.
- **Language-agnostic** — works for any source → target language pair.
- **Clean card template** — distraction-free front/back with audio playback and image.

## Quickstart

```bash
# Install
uv tool install anita-anki  # or: pipx install anita-anki

# Set credentials (or copy `.env.example` → `.env` and edit)
export OPENAI_API_KEY=sk-...
# Optional:
export ELEVENLABS_API_KEY=...

# Generate
anita generate examples/basics.csv my_deck.apkg --deck-name "My Vocabulary"
```

Import `my_deck.apkg` into Anki and start reviewing.

## Installation

### From PyPI (recommended)

```bash
uv tool install anita-anki
# or
pipx install anita-anki
# or
pip install anita-anki
```

> The distribution is published as **`anita-anki`** on PyPI (the name `anita` was taken),
> but the import name and CLI are both `anita`.

### From source (development)

```bash
git clone https://github.com/timpara/anita.git
cd anita
uv sync --all-extras
uv run anita --help
```

## Usage

### CLI

```bash
anita generate INPUT.csv OUTPUT.apkg [OPTIONS]
```

Common options:

| Flag                   | Default                | Description                                         |
| ---------------------- | ---------------------- | --------------------------------------------------- |
| `--deck-name`          | `Anita Vocabulary`     | Deck name shown inside Anki.                        |
| `--tts`                | `openai`               | TTS provider: `openai` or `elevenlabs`.             |
| `--images / --no-images` | `--no-images`        | Generate DALL·E illustrations per card.             |
| `--voice-id`           | *(elevenlabs preset)*  | ElevenLabs voice ID.                                |
| `--verbose`            | `false`                | Enable debug logging.                               |

Run `anita generate --help` for the full list.

### Python API

```python
from anita import AnkiDeckGenerator

generator = AnkiDeckGenerator(
    deck_name="Italian Restaurant",
    tts_provider="elevenlabs",
    generate_images=True,
)
generator.generate_deck("examples/restaurant.csv", "restaurant.apkg")
```

## CSV format

Two columns: source word (prompt side) and target word (answer side). Header row is optional
and auto-detected.

```csv
apple,mela
house,casa
book,libro
water,acqua
```

Working examples live in [`examples/`](examples/).

## Configuration

API keys are read from environment variables. A `.env` file in the working directory is
auto-loaded if present — the fastest way to get started is:

```bash
cp .env.example .env
# then edit .env with your real keys
```

`.env` is git-ignored; never commit it.

| Variable              | Required for            |
| --------------------- | ----------------------- |
| `OPENAI_API_KEY`      | OpenAI TTS, DALL·E      |
| `ELEVENLABS_API_KEY`  | ElevenLabs TTS (optional) |

Generated media is cached under your OS user-cache directory (via
[`platformdirs`](https://pypi.org/project/platformdirs/)) so re-running on the same words
incurs zero API cost.

## Cost estimate

| Service     | Use case          | Model      | Approximate cost              |
| ----------- | ----------------- | ---------- | ----------------------------- |
| OpenAI      | TTS               | `tts-1`    | $0.015 / 1k characters        |
| OpenAI      | Image generation  | DALL·E 2   | $0.020 / image (256×256)      |
| ElevenLabs  | Premium TTS       | v2         | Per your subscription tier    |

A 500-word deck with audio-only (OpenAI) typically costs well under $0.50.

## Cache

Anita keeps a small SQLite index of previously generated media so that
re-running `anita generate` on the same CSV skips paid API calls. The
index stores **only filename mappings** (source text → target text →
`image_fname`, `audio_fname`). It does **not** store API keys, prompts,
generated audio, image bytes, or any other content — the media files
themselves live in the `media/` directory you pass to the CLI.

### Location

The database path is resolved by
[`platformdirs.user_cache_dir("anita")`](https://platformdirs.readthedocs.io/en/latest/api.html#platformdirs.user_cache_dir):

| OS      | Default path                                                |
| ------- | ----------------------------------------------------------- |
| Linux   | `~/.cache/anita/generated_cards.db`                         |
| macOS   | `~/Library/Caches/anita/generated_cards.db`                 |
| Windows | `%LOCALAPPDATA%\anita\anita\Cache\generated_cards.db`       |

Respects `XDG_CACHE_HOME` on Linux.

### Lifecycle and disk reconciliation

Anita checks each cached filename against `media/` on every run. If you
delete a file out of `media/`, the next `anita generate` will regenerate
just that asset (audio and image are handled independently). Known-failed
generations are remembered so a flaky provider doesn't get hammered on
every retry.

### Clearing the cache

There is no `anita cache clear` subcommand yet (tracked separately).
For now, delete the file directly:

```bash
# Linux
rm ~/.cache/anita/generated_cards.db

# macOS
rm ~/Library/Caches/anita/generated_cards.db
```

```powershell
# Windows
Remove-Item "$env:LOCALAPPDATA\anita\anita\Cache\generated_cards.db"
```

Or pass a project-local cache path when using the Python API:

```python
from pathlib import Path
from anita.cache import MediaCache
cache = MediaCache(db_path=Path("./anita-cache.db"))
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, coding style,
and PR conventions. By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

To report a security issue, please see [SECURITY.md](SECURITY.md).

## License

[Apache License 2.0](LICENSE) © 2024–present Anita contributors.

## Supply chain

Anita takes a few concrete steps to be a well-behaved dependency:

- **PyPI OIDC trusted publishing** — releases are uploaded from GitHub
  Actions without any long-lived API token.
- **Sigstore attestations** — every wheel and sdist on PyPI is signed by
  `pypa/gh-action-pypi-publish`, so you can verify provenance.
- **CycloneDX SBOM** — each GitHub Release ships an
  `anita-v<version>-sbom.cdx.json` bill of materials (CycloneDX 1.5)
  listing every locked dependency.
- **Secret scanning** — `gitleaks` runs on every PR, plus GitHub-native
  push protection.
- **Dependency auditing** — `pip-audit` scans `uv.lock` on every PR and
  weekly against OSV.dev.

See [`SECURITY.md`](SECURITY.md) for details and vulnerability reporting.

## Acknowledgments

- [genanki](https://github.com/kerrickstaley/genanki) — Anki deck construction.
- [OpenAI](https://openai.com/) — TTS and image generation.
- [ElevenLabs](https://elevenlabs.io/) — premium multilingual voices.
