# hexstrike — security tooling (OPT-IN) ⚠️

**Off by default. The wizard requires explicit consent to enable it.**

HexStrike AI is a large security-tooling MCP server. Use only for **authorized**
security testing, CTF, and research. Listens on `:8899`.

## Credit

Deploys **HexStrike AI** by **0x4m4** —
<https://github.com/0x4m4/hexstrike-ai>. agentstack provides only the deployment
config; all credit goes to its authors. The source is fetched into
`${HEXSTRIKE_SRC}` and built locally. License: see `THIRD_PARTY_NOTICES.md`.

## Run

```bash
docker network create agentstack 2>/dev/null || true
docker compose up -d
```
