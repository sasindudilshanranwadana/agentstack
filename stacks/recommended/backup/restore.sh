#!/usr/bin/env bash
# Restore from a backup run produced by backup.sh.
#
#   restore.sh /backups/<run>          # restore Postgres + SQLite + archives
#   restore.sh /backups/<run> --db     # only the Postgres dump
#
# Run it from the host (it uses docker) with the stack UP. It overwrites current
# state, so read it before you run it.
set -euo pipefail

RUN_DIR="${1:?usage: restore.sh /backups/<run> [--db|--sqlite|--volumes]}"
WHAT="${2:-all}"
: "${POSTGRES_USER:=postgres}"
DATA_OUT="${DATA_OUT:-./data}"

log() { printf '%s [restore] %s\n' "$(date -Is)" "$*"; }

[ -f "$RUN_DIR/_SUCCESS" ] || { echo "no _SUCCESS in $RUN_DIR — incomplete backup" >&2; exit 1; }

if [ "$WHAT" = "all" ] || [ "$WHAT" = "--db" ]; then
  dump="$(ls "$RUN_DIR"/databases/*.dump 2>/dev/null | head -1 || true)"
  if [ -n "$dump" ]; then
    db="$(basename "$dump" .dump)"
    log "restoring Postgres database '$db' from $(basename "$dump")"
    docker exec -i mem0-postgres pg_restore -U "$POSTGRES_USER" -d "$db" --clean --if-exists \
      < "$dump" || log "pg_restore reported warnings (often harmless on --clean)"
  fi
fi

if [ "$WHAT" = "all" ] || [ "$WHAT" = "--sqlite" ]; then
  if [ -d "$RUN_DIR/sqlite" ]; then
    log "restoring SQLite snapshots into $DATA_OUT (stop the owning containers first)"
    ( cd "$RUN_DIR/sqlite" && find . -type f -print0 \
        | while IFS= read -r -d '' f; do
            mkdir -p "$DATA_OUT/$(dirname "$f")"
            cp "$f" "$DATA_OUT/$f"
          done )
  fi
fi

if [ "$WHAT" = "all" ] || [ "$WHAT" = "--volumes" ]; then
  for arc in "$RUN_DIR"/volumes/*.tar.gz; do
    [ -f "$arc" ] || continue
    log "extracting $(basename "$arc") into $DATA_OUT"
    tar xzf "$arc" -C "$DATA_OUT"
  done
fi

log "done. Restart the stack:  docker compose up -d"
