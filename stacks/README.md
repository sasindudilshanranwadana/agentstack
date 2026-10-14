# agentstack stacks

Each component is a self-contained Docker Compose module:

```
stacks/<tier>/<id>/
├── docker-compose.yml   # upstream public images, parameterized
├── .env.example         # documented placeholder values (no secrets)
└── README.md            # what it is, upstream credit, how to run
```

## Conventions

Every module follows these so the wizard can compose them together:

- **Network:** modules join the external `agentstack` network (the installer
  creates it: `docker network create agentstack`). Private per-stack networks
  may also be declared `internal: true`.
- **Bind address:** published ports bind to `${BIND_ADDR:-127.0.0.1}`. Set
  `BIND_ADDR=0.0.0.0` (or a tailnet IP) to expose beyond localhost.
- **Data:** persistent volumes live under `${AGENTSTACK_DATA:-./data}/<id>`.
- **Timezone:** `${TZ:-UTC}`.
- **Secrets:** never committed. Each module ships `.env.example`; the wizard
  writes a git-ignored `.env` at install time.

All compose files validate with `docker compose -f <file> config -q` using only
their built-in defaults — no `.env` required just to validate.
