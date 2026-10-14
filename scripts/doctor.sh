#!/usr/bin/env bash
# Quick health check of the running stack.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Docker =="
docker version --format '  client {{.Client.Version}} / server {{.Server.Version}}' 2>/dev/null \
  || { echo "  Docker not reachable" >&2; exit 1; }

echo "== agentstack network =="
docker network inspect agentstack >/dev/null 2>&1 && echo "  present" || echo "  MISSING (run ./install.sh)"

echo "== containers =="
docker compose ps 2>/dev/null || echo "  no compose project up (run scripts/up.sh)"
