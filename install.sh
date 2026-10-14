#!/usr/bin/env bash
# agentstack installer (Linux / macOS). Thin launcher: verify Python + Docker,
# then hand off to the cross-platform Python wizard.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it and re-run." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine (Linux) or Docker Desktop (macOS)." >&2
  echo "  https://docs.docker.com/get-docker/" >&2
  exit 1
fi

docker network create agentstack >/dev/null 2>&1 || true
exec python3 -m wizard "$@"
