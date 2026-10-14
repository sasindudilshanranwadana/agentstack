# backup — daily, verifiable snapshots

A lost Docker volume should not be a lost stack. This module takes a dated,
checksummed backup once a day and can push a copy offsite.

## What it captures

| Data | How |
|------|-----|
| mem0 Postgres | `pg_dump -Fc` run **inside** the DB container (version-matched, consistent, nothing paused) |
| SQLite DBs (OmniRoute, Open WebUI, Nginx Proxy Manager, …) | opened `immutable=1` and `.backup`'d |
| Data directories | `tar.gz` per directory, excluding the raw Postgres data dir (the dump replaces it) |

**Skipped** (regenerable): `ollama` models (re-pullable), `netdata` cache. Each
run ends with a `SHA256SUMS` and a `_SUCCESS` marker written last, so a half-run
is never mistaken for a complete one.

## Where / when

- **Local:** `${AGENTSTACK_BACKUPS:-./backups}/<timestamp>/`
- **Schedule:** daily at `BACKUP_HOUR` (default `03`), local `TZ`.
- **Retention:** local runs older than `BACKUP_RETENTION_DAYS` (default `7`) are pruned.
- **Offsite (optional):** set `RCLONE_REMOTE` (e.g. `gdrive:agentstack`) and drop
  an `rclone.conf` in `${AGENTSTACK_DATA}/rclone/`. Each run is copied and then
  `rclone check`-verified.
- **Alerts:** success and failure are sent through the notification channel the
  wizard configured (Discord / Slack / Telegram); otherwise they're in the logs.

Take one immediately to verify setup:

```bash
docker compose run --rm -e BACKUP_RUN_NOW=1 backup
```

## Restore

```bash
# full restore from a run (Postgres + SQLite + archives)
stacks/recommended/backup/restore.sh ./backups/<timestamp>

# just the database
stacks/recommended/backup/restore.sh ./backups/<timestamp> --db
```

Restore **overwrites** current state — read `restore.sh` first. Stop the
containers that own the SQLite files before restoring those, then
`docker compose up -d`.

## Security note

To produce a consistent database dump, the container runs `pg_dump` inside the
database container, which requires access to the Docker socket (mounted
read-only). The Docker API is powerful, so this is broad access — review
`backup.sh`. If you want to narrow it, put a Docker socket proxy (e.g.
`tecnativa/docker-socket-proxy`, `EXEC=1`, everything else off) in front and
point the container at it.

Credit: [rclone](https://rclone.org) (MIT), built on `pg_dump`/`sqlite3`/`tar`.
The backup/restore scripts are part of agentstack (MIT).
