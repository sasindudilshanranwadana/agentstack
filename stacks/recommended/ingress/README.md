# ingress — public entry + TLS (recommended)

Nginx Proxy Manager gives you a web UI (`:81`) to publish the stack's services
behind clean domains with automatic Let's Encrypt TLS. Serves `:80`/`:443`.

## Upstream credit

Deploys **Nginx Proxy Manager** by **jc21** —
<https://github.com/NginxProxyManager/nginx-proxy-manager> (MIT). agentstack
provides only the deployment config.

## Run

```bash
docker network create agentstack 2>/dev/null || true
docker compose up -d
# Admin UI at http://localhost:81 — default login admin@example.com / changeme
# (change it immediately).
```

For localhost-only installs you can skip this module entirely.
