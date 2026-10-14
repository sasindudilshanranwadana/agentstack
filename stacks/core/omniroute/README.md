# omniroute — LLM gateway (core)

OmniRoute is the single LLM endpoint the whole stack talks to. Clients and
agents point at it (`:20129`, OpenAI/Anthropic-compatible) and it routes to
whichever upstream provider(s) you configured. Management API is on `:20128`,
live websocket on `:20132`.

## Upstream credit

This module deploys **OmniRoute** by **diegosouzapw** —
<https://hub.docker.com/r/diegosouzapw/omniroute>. agentstack only provides the
deployment configuration; all credit for OmniRoute itself goes to its author.
License: see `THIRD_PARTY_NOTICES.md` (verified before release).

## Run

```bash
cp .env.example .env    # fill in your keys
docker network create agentstack 2>/dev/null || true
docker compose up -d
```

Ports bind to `${BIND_ADDR:-127.0.0.1}` (localhost only by default).

## Notes

- Uses the upstream public image. For the optional security-patched build,
  run `scripts/hardened-build.sh` (does not change behavior).
- Secrets live only in your local `.env` and are never committed.
