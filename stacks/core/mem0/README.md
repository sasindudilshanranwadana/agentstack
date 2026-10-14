# mem0 — shared memory (core)

mem0 is the persistent memory layer every agent shares. API on `:8888`,
dashboard on `:3000`, backed by a pgvector Postgres. Its own LLM/embedding
calls can route through omniroute (the default).

## Upstream credit

This module deploys **mem0** by the **mem0ai** team —
<https://github.com/mem0ai/mem0> (Apache-2.0). agentstack only provides the
deployment configuration; all credit for mem0 goes to its authors. The mem0 api
and dashboard build from the upstream source, fetched by the installer into
`${MEM0_SRC}` (default `./vendor/mem0`).

## Run

```bash
cp .env.example .env     # set MEM0_POSTGRES_PASSWORD etc.
git clone https://github.com/mem0ai/mem0 vendor/mem0   # installer does this for you
docker network create agentstack 2>/dev/null || true
docker compose up -d
```

Postgres data persists under `${AGENTSTACK_DATA:-./data}/mem0/postgres`.
Secrets live only in your local `.env`.
