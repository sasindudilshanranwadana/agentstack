# host-gateway — the privileged host-access component (OPT-IN). Pure stdlib
# Python; util-linux provides nsenter, used to run approved commands in the
# host's namespaces. Reaches the host only when the container is run with
# pid: host and the matching privileges (see the module's docker-compose.yml).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends util-linux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/

ENV HG_STATE=/state HG_AUDIT=/audit
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)" || exit 1

CMD ["python", "-u", "server.py"]
