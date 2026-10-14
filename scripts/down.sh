#!/usr/bin/env bash
# Stop the stacks (reads COMPOSE_FILE from .env). Data volumes are preserved.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down
echo "Stopped. Data under \${AGENTSTACK_DATA:-./data} is preserved."
