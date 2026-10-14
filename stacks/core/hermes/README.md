# hermes — the orchestrator / "the boss" (core)

Hermes is the agent that drives the whole stack. It uses omniroute for LLM
access, mem0 for memory, and the MCP tool pool for tools. Its dashboard runs on
`:9119`.

## Upstream credit

This module deploys the **Hermes Agent** by **Nous Research** —
<https://github.com/NousResearch>. agentstack only provides a portable
deployment; all credit for Hermes goes to Nous Research. This is **not** an
official Nous Research distribution. License: see `THIRD_PARTY_NOTICES.md`.

## Portable by design

Unlike a host-coupled install, this module uses **bridge networking** (not host
networking), a **configurable data dir** (`${AGENTSTACK_DATA}/hermes`, not
personal host paths), and **no docker.sock** — giving the agent host-level
access is the separate, opt-in `host-gateway` module.

## Run

```bash
cp .env.example .env     # set HERMES_DISCORD_TOKEN etc.
docker network create agentstack 2>/dev/null || true
# The installer seeds ${AGENTSTACK_DATA}/hermes with a default config and
# chowns it to the image's UID 10000 before first boot.
docker compose up -d
```

## Agents & skills

The sanitized starter pack mounts read-only at `/opt/data/agents` from
`stacks/core/hermes/agents/`. Add your own agents/skills there.
