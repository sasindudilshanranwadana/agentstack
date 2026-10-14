#!/usr/bin/env python3
"""agentstack watchdog — the dead-man's-switch.

Netdata shows metrics and Diun notifies about image updates, but neither tells
you when a container has actually gone DOWN or UNHEALTHY. This does: it polls
the Docker Engine API over the (read-only) socket and, when a container on the
agentstack network changes to a bad state — exited, dead, restarting, or
unhealthy — it sends one alert through whichever notification channel the wizard
configured, and one more when the container recovers.

Pure standard library. The notification channel is auto-detected from the env
the wizard already fills in (Discord / Slack / Telegram / SMTP); with none set
it just logs, so the watchdog is still useful via `docker logs`.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import smtplib
import socket
import sys
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage

SOCK = "/var/run/docker.sock"
NETWORK = os.environ.get("WATCHDOG_NETWORK", "agentstack")
INTERVAL = max(5, int(os.environ.get("WATCHDOG_INTERVAL", "30")))
_HEALTH_RE = re.compile(r"\((healthy|unhealthy|health: starting)\)")


def log(msg: str) -> None:
    print(f"[watchdog] {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}", flush=True)


class _UnixHTTP(http.client.HTTPConnection):
    def connect(self) -> None:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect(SOCK)
        self.sock = s


def _docker_get(route: str) -> list | dict:
    conn = _UnixHTTP("localhost")
    conn.request("GET", route)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return json.loads(body)


def _state_of(container: dict) -> str:
    """Collapse a container's Docker state + health into one label."""
    state = container.get("State", "")  # running/exited/dead/restarting/created
    status = container.get("Status", "")
    m = _HEALTH_RE.search(status)
    health = m.group(1) if m else ""
    if health == "unhealthy":
        return "unhealthy"
    if state == "running":
        return "running"
    return state or "unknown"


_BAD = {"exited", "dead", "restarting", "unhealthy"}


def _on_agentstack(container: dict) -> bool:
    nets = (container.get("NetworkSettings") or {}).get("Networks") or {}
    return NETWORK in nets


def _name(container: dict) -> str:
    names = container.get("Names") or []
    return names[0].lstrip("/") if names else container.get("Id", "?")[:12]


# ---- notification (auto-detected channel) ----
def _post_json(url: str, payload: dict) -> None:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=15).read()


def notify(text: str) -> None:
    log(text)
    try:
        if os.environ.get("DISCORD_WEBHOOK_URL"):
            _post_json(os.environ["DISCORD_WEBHOOK_URL"], {"content": text})
        elif os.environ.get("SLACK_WEBHOOK_URL"):
            _post_json(os.environ["SLACK_WEBHOOK_URL"], {"text": text})
        elif os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
            tok = os.environ["TELEGRAM_BOT_TOKEN"]
            data = urllib.parse.urlencode(
                {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text}).encode()
            urllib.request.urlopen(
                f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=15).read()
        elif os.environ.get("SMTP_HOST"):
            _send_email(text)
    except Exception as exc:  # a notifier outage must never kill the watchdog
        log(f"notify failed ({exc}); state change was logged above")


def _send_email(text: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "[agentstack] container state change"
    msg["From"] = os.environ.get("SMTP_USER", "agentstack@localhost")
    msg["To"] = os.environ["SMTP_TO"]
    msg.set_content(text)
    host, port = os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT") or 587)
    with smtplib.SMTP(host, port, timeout=20) as s:
        s.starttls()
        if os.environ.get("SMTP_USER"):
            s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        s.send_message(msg)


def main() -> int:
    log(f"watching docker containers on network '{NETWORK}' every {INTERVAL}s")
    channel = next((c for c, ok in (
        ("Discord", os.environ.get("DISCORD_WEBHOOK_URL")),
        ("Slack", os.environ.get("SLACK_WEBHOOK_URL")),
        ("Telegram", os.environ.get("TELEGRAM_BOT_TOKEN")),
        ("email", os.environ.get("SMTP_HOST"))) if ok), "none (log only)")
    log(f"alert channel: {channel}")

    prev: dict[str, str] = {}
    first = True
    while True:
        try:
            containers = _docker_get("/v1.43/containers/json?all=1")
            seen = {}
            for c in containers:
                if not _on_agentstack(c):
                    continue
                name = _name(c)
                state = _state_of(c)
                seen[name] = state
                was = prev.get(name)
                bad_now = state in _BAD
                bad_before = was in _BAD
                if bad_now and (was != state) and not (first and False):
                    notify(f"\U0001F534 agentstack: `{name}` is {state.upper()}")
                elif bad_before and not bad_now:
                    notify(f"\U0001F7E2 agentstack: `{name}` recovered ({state})")
            # a container that vanished entirely while it was bad is left alone;
            # a running→removed transition is a deliberate `down`, not a fault.
            prev = seen
            first = False
        except Exception as exc:
            log(f"poll error: {exc}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
