# headroom — context compression (recommended)

Headroom sits in front of the LLM gateway and compresses conversation context so
long agent sessions stay cheap. Listens on `:8787`.

## Upstream credit

Deploys **Headroom** by **Headroom Labs** —
<https://github.com/headroomlabs-ai>. agentstack provides only the deployment
config; all credit goes to Headroom Labs. License: see `THIRD_PARTY_NOTICES.md`.

## Run

```bash
docker network create agentstack 2>/dev/null || true
docker compose up -d
```
