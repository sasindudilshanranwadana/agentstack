#!/usr/bin/env bash
# Fetch the upstream sources for build-from-source modules into ./vendor.
# Idempotent: skips a source that's already present. Run before `up` for any
# selection that includes mem0 (core) or hexstrike.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor

clone() {  # clone <url> <dir>
  local url="$1" dir="$2"
  if [ -d "$dir/.git" ]; then
    echo "  $dir already present — skipping"
  else
    echo "  cloning $url -> $dir"
    git clone --depth 1 "$url" "$dir"
  fi
}

echo "Fetching upstream sources into ./vendor ..."
# mem0 (core memory layer) — Apache-2.0
clone https://github.com/mem0ai/mem0 ./vendor/mem0
# hexstrike (opt-in security tooling) — MIT
clone https://github.com/0x4m4/hexstrike-ai ./vendor/hexstrike-ai
echo "Done. (agentstack's own host-gateway source ships in ./src/host-gateway)"
