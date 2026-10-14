# Contributing to agentstack

Thanks for your interest! agentstack is orchestration glue over great upstream
tools — contributions that add components, improve the wizard, or sharpen the
docs are welcome.

## Dev setup

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

Tests cover the wizard logic, validate every stack module with
`docker compose config`, and run the repo-wide sanitization scan. Docker is
required for the compose-validation tests (they skip cleanly without it).

## Adding a component

1. Create `stacks/<tier>/<id>/docker-compose.yml`, `.env.example`, `README.md`.
2. Use upstream **public** images, `${BIND_ADDR:-127.0.0.1}`,
   `${AGENTSTACK_DATA:-./data}`, `${TZ:-UTC}` — see `stacks/README.md`.
3. Register it in `wizard/components.py` with a complete upstream **credit**.
4. The data-driven tests pick it up automatically; run `pytest -q`.

## Rules

- No secrets, personal paths, or private infra references in shipped files.
- Credit every upstream tool (tool · author · link · license). The credits gate
  blocks releases with unverified licenses.
- Keep modules portable (bridge networking, no host-only assumptions).

## Commits

Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`.
