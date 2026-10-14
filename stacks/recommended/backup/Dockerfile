# agentstack backup — a tiny Alpine image with just the tools the scripts need.
# No database client is bundled: dumps run inside the database container itself
# (via docker-cli + the socket), which keeps the dump version-matched.
FROM alpine:3.20

RUN apk add --no-cache bash docker-cli sqlite tar gzip coreutils findutils tzdata rclone curl

COPY backup.sh restore.sh entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/restore.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
