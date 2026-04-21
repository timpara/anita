# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/timpara/anita/compare/v0.1.0...v0.2.0) (2026-04-21)


### Features

* **cli:** add 'anita cache' subcommand group ([#51](https://github.com/timpara/anita/issues/51)) ([83ef8b3](https://github.com/timpara/anita/commit/83ef8b3af451e34e0682a51eb01a1bb5ba5a4d9f)), closes [#30](https://github.com/timpara/anita/issues/30)
* **release:** generate and attach CycloneDX SBOM ([#19](https://github.com/timpara/anita/issues/19)) ([#43](https://github.com/timpara/anita/issues/43)) ([d0dec6f](https://github.com/timpara/anita/commit/d0dec6fee28781ce9c2585a92ea8397d92b65e56))


### Bug Fixes

* **cache:** regenerate media when files are deleted from disk ([#47](https://github.com/timpara/anita/issues/47)) ([c3f3646](https://github.com/timpara/anita/commit/c3f3646e5189cb84bed9b0653bb73ba830cda2a7)), closes [#22](https://github.com/timpara/anita/issues/22)


### Documentation

* **readme:** document SQLite cache location and lifecycle ([#48](https://github.com/timpara/anita/issues/48)) ([f74615b](https://github.com/timpara/anita/commit/f74615b06f4c82a196cdfaa22ddf4d321510e535)), closes [#32](https://github.com/timpara/anita/issues/32)

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
