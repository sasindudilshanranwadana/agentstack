---
name: stack-doctor
description: Diagnose a running agentstack deployment — check that Hermes, OmniRoute, and mem0 are healthy and talking to each other, and find the common causes when they are not. Use when the agent can't reach its model router or its memory, or when a container is unhealthy.
version: 1.0.0
license: MIT
author: agentstack (Sasindu Dilshan Ranwadana)
platforms: [linux, macos, windows]
tags: [agentstack, operations, health, troubleshooting]
---

# Stack Doctor

agentstack is Hermes (the agent) plus two vitals it depends on: **OmniRoute**
(the LLM gateway) and **mem0** (shared memory). When Hermes misbehaves, the
cause is usually one of those links, not Hermes itself. Check from the outside
in.

## Quick pass

Run the bundled check first:

```bash
./scripts/doctor.sh
```

It reports each selected container's health and the Compose project state. If it
is clean and the problem persists, work the links below.

## The links, in order

1. **Containers up and healthy.**
   `docker compose ps` — every service `running`/`healthy`, not `restarting`.
   A crash-looping container: `docker compose logs --tail 100 <service>`.

2. **Hermes → OmniRoute.** Hermes reaches the router at
   `OMNIROUTE_BASE_URL` (default `http://omniroute:20129` on the `agentstack`
   network). From the Hermes container:
   `curl -fsS http://omniroute:20129/health` — a non-200 or a refused
   connection means the router is down or the URL/env is wrong, not that the
   model failed.

3. **Hermes → mem0.** Memory lives at `MEM0_API_URL`
   (default `http://mem0-api:8000`). `curl -fsS http://mem0-api:8000/health`.
   If mem0 is up but empty, memory writes may be failing silently — check the
   mem0 logs for its Postgres connection.

4. **Networking.** All of the above assume the services share the external
   `agentstack` network. `docker network inspect agentstack` should list every
   running service. A service missing from it was started without the network —
   bring it up through the wizard-generated `COMPOSE_FILE`, not by hand.

## Common causes

- **Router returns errors for every model:** no provider API key set, or the
  key is for a provider you didn't enable. Check `.env`.
- **Agent "forgets" across sessions:** mem0 unreachable or its Postgres volume
  not mounted — memory degrades silently, it doesn't error loudly.
- **`host-gateway` calls refused:** it's opt-in and off by default; it must be
  selected in the wizard and given a token (`hgctl.py mint`).

Report what you found and which link failed, not just "it's broken."
