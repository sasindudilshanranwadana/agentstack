#!/usr/bin/env bash
# Scheduler loop: run backup.sh once a day at BACKUP_HOUR:00 (local TZ).
# Set BACKUP_RUN_NOW=1 to take a backup immediately on start (handy for a first
# verification run).
set -euo pipefail

: "${BACKUP_HOUR:=3}"

log() { printf '%s [entrypoint] %s\n' "$(date -Is)" "$*"; }

if [ "${BACKUP_RUN_NOW:-0}" = "1" ]; then
  log "BACKUP_RUN_NOW=1 — taking an immediate backup"
  /usr/local/bin/backup.sh || log "immediate backup failed (see above)"
fi

while true; do
  now_h=$(date +%H)
  now_m=$(date +%M)
  # seconds until the next BACKUP_HOUR:00 (10# forces base-10 on 08/09)
  secs=$(( ((24 + BACKUP_HOUR - 10#$now_h) % 24) * 3600 - 10#$now_m * 60 ))
  [ "$secs" -le 0 ] && secs=$((secs + 86400))
  log "next backup in ${secs}s (daily at ${BACKUP_HOUR}:00)"
  sleep "$secs"
  /usr/local/bin/backup.sh || log "scheduled backup failed (see above)"
done
