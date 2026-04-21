# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-21

### Added

- First public release.
- `anita generate` CLI built on Typer for turning a two-column CSV into an
  Anki `.apkg`.
- Pluggable TTS providers: OpenAI (`tts-1`) and ElevenLabs (`eleven_multilingual_v2`).
- Optional DALL·E 2 illustration generation with automatic 128×128 resizing.
- SQLite-backed media cache under the user cache directory so repeat runs are
  free.
- Language-agnostic model with deterministic deck / model IDs derived from
  names (no ID collisions between users).
- CSV header-row auto-detection; malformed rows are skipped with a warning.
- `.env` auto-loading for API keys.
- Python API: `from anita import AnkiDeckGenerator`.

[Unreleased]: https://github.com/timpara/anita/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/timpara/anita/releases/tag/v0.1.0
