# Security

## Secrets

- Your API keys and tokens live **only** in a local, git-ignored `.env`.
- Nothing secret or personal is committed. `.gitignore` excludes `.env`,
  `data/`, `secrets/`, and build caches.
- A repo-wide scan (`tests/test_sanitization.py`) plus gitleaks in CI guard
  against accidental secret/personal-data commits.

## Privileged components

`host-gateway` grants the agent host-level command access and `hexstrike` is
security tooling. Both are **off by default** and require explicit, typed
consent in the wizard. Enable them only if you understand the blast radius, and
only on hosts you control.

## Exposure

By default, service ports bind to `127.0.0.1`. The `ingress` module is the only
intended public entry (`:80`/`:443`). Set `BIND_ADDR`/`INGRESS_BIND` deliberately
before exposing anything beyond localhost.

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository, or contact the
maintainer. Do not file public issues for sensitive reports.
