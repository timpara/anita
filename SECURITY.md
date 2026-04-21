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

## Dependency auditing

Third-party packages in `uv.lock` are audited for known CVEs via
[`pip-audit`](https://pypi.org/project/pip-audit/) using the
[OSV.dev](https://osv.dev/) vulnerability database:

- **On every PR and push to `main`** — the `Dependency audit (pip-audit)`
  job in CI. It is a required check for merges into `main`.
- **Weekly** — the `.github/workflows/audit-weekly.yml` workflow runs every
  Monday at 06:00 UTC and on manual dispatch, catching freshly-disclosed
  CVEs between Dependabot version bumps.

The audit runs against a frozen export of `uv.lock` including all extras,
so both runtime and dev dependencies are covered.

### Suppressing a false positive

If an advisory is not exploitable in Anita's usage (e.g., the affected
code path is unreachable), document the rationale and pass the advisory
ID to `pip-audit` via the `ignore-vulns` input in
[`.github/workflows/ci.yml`](./.github/workflows/ci.yml):

```yaml
- uses: pypa/gh-action-pip-audit@v1.1.0
  with:
    inputs: requirements-audit.txt
    vulnerability-service: osv
    ignore-vulns: |
      GHSA-xxxx-xxxx-xxxx  # Rationale: ...
```

Prefer upgrading over suppressing whenever a fixed release exists.
