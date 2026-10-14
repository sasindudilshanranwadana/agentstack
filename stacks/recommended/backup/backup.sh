#!/usr/bin/env bash
# One backup run. Writes a dated, checksummed snapshot under /backups and,
# if RCLONE_REMOTE is set, copies it offsite and verifies the copy.
set -euo pipefail

DATA_IN="${DATA_IN:-/data}"
BACKUP_OUT="${BACKUP_OUT:-/backups}"
: "${BACKUP_RETENTION_DAYS:=7}"
: "${POSTGRES_USER:=postgres}"

RUN="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_OUT/$RUN"

log() { printf '%s [backup] %s\n' "$(date -Is)" "$*"; }

notify() {
  local msg="$1"
  if [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
    curl -fsS -X POST -H 'Content-Type: application/json' \
      -d "{\"content\":\"${msg}\"}" "$DISCORD_WEBHOOK_URL" >/dev/null 2>&1 || true
  elif [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -fsS -X POST -H 'Content-Type: application/json' \
      -d "{\"text\":\"${msg}\"}" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
  elif [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=${msg}" >/dev/null 2>&1 || true
  fi
}

fail() {
  log "FAILED: $*"
  notify "agentstack backup FAILED ($RUN): $*"
  exit 1
}
trap 'fail "unexpected error near line $LINENO"' ERR

mkdir -p "$DEST/databases" "$DEST/sqlite" "$DEST/volumes"
log "starting run $RUN -> $DEST"

# 1) Postgres (mem0) — a consistent dump, run inside the DB container so the
#    pg_dump version always matches the server. Nothing is paused.
if docker inspect mem0-postgres >/dev/null 2>&1; then
  log "dumping Postgres (mem0)"
  if docker exec mem0-postgres pg_dump -U "$POSTGRES_USER" -Fc -d mem0_app \
        > "$DEST/databases/mem0_app.dump" 2>/dev/null; then
    log "  mem0_app.dump written"
  else
    docker exec mem0-postgres pg_dump -U "$POSTGRES_USER" -Fc -d postgres \
      > "$DEST/databases/postgres.dump"
    log "  postgres.dump written"
  fi
  docker exec mem0-postgres pg_dumpall -U "$POSTGRES_USER" --globals-only \
    > "$DEST/databases/globals.sql" 2>/dev/null || true
else
  log "mem0-postgres not present — skipping Postgres dump"
fi

# 2) SQLite databases anywhere under the data dir (OmniRoute, Open WebUI, NPM…).
#    Opened immutable so nothing is written back into the read-only source.
log "snapshotting SQLite databases"
while IFS= read -r f; do
  rel="${f#"$DATA_IN"/}"
  out="$DEST/sqlite/$rel"
  mkdir -p "$(dirname "$out")"
  sqlite3 "file:$f?immutable=1" ".backup '$out'" 2>/dev/null \
    || cp "$f" "$out" 2>/dev/null || true
done < <(find "$DATA_IN" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) 2>/dev/null)

# 3) Data-directory archives. Skip the regenerable ones, and exclude the raw
#    Postgres data dir (the dump above is the consistent copy of that).
log "archiving data directories"
for d in "$DATA_IN"/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  case "$name" in
    ollama|netdata|rclone) continue ;;  # models re-pullable; caches regenerable
    mem0) tar czf "$DEST/volumes/mem0.tar.gz" -C "$DATA_IN" \
            --exclude='mem0/postgres' "mem0" 2>/dev/null || true ;;
    *) tar czf "$DEST/volumes/$name.tar.gz" -C "$DATA_IN" "$name" 2>/dev/null || true ;;
  esac
done

# 4) checksums + success marker (written last, so its presence means "complete")
( cd "$DEST" && find . -type f ! -name SHA256SUMS -exec sha256sum {} + > SHA256SUMS )
printf '{"run":"%s","finished":"%s"}\n' "$RUN" "$(date -Is)" > "$DEST/_SUCCESS"

# 5) retention: drop local runs older than N days
find "$BACKUP_OUT" -maxdepth 1 -type d -name '20*' -mtime "+$BACKUP_RETENTION_DAYS" \
  -exec rm -rf {} + 2>/dev/null || true

# 6) optional offsite copy + verify
if [ -n "${RCLONE_REMOTE:-}" ]; then
  log "copying offsite -> $RCLONE_REMOTE/$RUN"
  rclone copy "$DEST" "$RCLONE_REMOTE/$RUN" || fail "rclone copy failed"
  rclone check "$DEST" "$RCLONE_REMOTE/$RUN" || fail "rclone verify mismatch"
  log "offsite copy verified"
fi

size="$(du -sh "$DEST" 2>/dev/null | cut -f1)"
log "OK ($size) -> $DEST"
notify "agentstack backup OK ($RUN, $size)"
