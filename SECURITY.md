# Security Policy

## Supported versions

Anita is currently pre-1.0. Only the latest released version receives security
fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please **do not** file a public GitHub issue for security vulnerabilities.

Instead, report privately via GitHub's
[Security Advisories](https://github.com/timpara/anita/security/advisories/new)
flow, or email the maintainer at `t.paraskevopoulos@posteo.de` with the subject
line `[anita security]`.

Include, if possible:

- A description of the issue and its impact
- Steps or a proof-of-concept to reproduce
- The version of Anita affected
- Any suggested mitigation

You should receive an acknowledgement within **5 business days**. We will keep
you informed as we investigate and prepare a fix. Coordinated disclosure is
appreciated.

## Secret scanning

This repository is protected against accidental secret leaks by multiple layers:

- **Pre-commit** — [gitleaks](https://github.com/gitleaks/gitleaks) scans
  staged content on every commit. Install hooks with `pre-commit install`.
- **CI** — the `Secret scan (gitleaks)` job runs on every push and pull
  request against the full git history. It is a required check for merges
  into `main`.
- **GitHub native** — secret scanning and push protection are enabled at the
  repository level, blocking pushes that contain known provider token
  patterns (AWS, GitHub, OpenAI, Stripe, etc.).

Configuration lives in [`.gitleaks.toml`](./.gitleaks.toml). If gitleaks
flags a false positive, open a PR adding a narrow allowlist entry rather
than disabling the scan.
