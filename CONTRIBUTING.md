# Contributing to Anita

Thanks for your interest in improving Anita! This document explains how to set
up a development environment, the coding conventions we follow, and how to get
your change merged.

## Development setup

Anita uses [uv](https://github.com/astral-sh/uv) for Python environment and
dependency management.

```bash
git clone https://github.com/timpara/anita.git
cd anita
uv sync --all-extras
uv run anita --version
```

Install the git hooks (runs ruff automatically on every commit):

```bash
uv run pre-commit install
```

## Running the checks

All of these are run in CI. Run them locally before opening a PR:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy anita
uv run pytest
```

## Coding conventions

- **Style & formatting:** `ruff` (lint + format). No black, no isort.
- **Types:** type hints on all public symbols; keep `mypy` clean.
- **Imports:** explicit — no wildcard imports.
- **Paths:** always `pathlib.Path`, never `os.path`.
- **Logging:** use the stdlib `logging` module, not `print`.
- **Tests:** pytest; network calls must be mocked (see the `FakeTTS` /
  `FakeImages` helpers in `tests/conftest.py`). CI enforces a **90%
  coverage floor** (`--cov-fail-under=90`); PRs that drop coverage below
  that will fail.

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/). Common
prefixes:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or updating tests
- `chore:` / `ci:` — tooling and infra

Breaking changes: append `!` to the type (`feat!: …`) and describe the break in
the footer.

## Pull request process

1. Fork the repo and create a topic branch: `git checkout -b feat/short-slug`.
2. Make your change with tests and documentation.
3. Ensure the checks above pass locally.
4. Open a PR against `main`. Fill in the PR template.
5. A maintainer will review. Address feedback and keep the branch rebased on
   `main` (squash-and-merge is the default merge strategy).

## Reporting security issues

Please **do not** open a public issue for security vulnerabilities. See
[SECURITY.md](SECURITY.md) for private reporting instructions.

## Code of Conduct

By participating you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).
