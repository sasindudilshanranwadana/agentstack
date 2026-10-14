#!/usr/bin/env bash
# Bring up the selected stacks (reads COMPOSE_FILE from .env).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "No .env — run ./install.sh first." >&2; exit 1; }
# Ensure build-from-source modules (mem0, hexstrike) have their sources.
scripts/fetch-sources.sh
docker network create agentstack >/dev/null 2>&1 || true
docker compose up -d
echo "Up. Check health with scripts/doctor.sh"
