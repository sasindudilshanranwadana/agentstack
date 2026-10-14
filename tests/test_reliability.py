"""Reliability guarantees — the holes we must never ship again.

A failure must not be silent (health checks + a down-alert watchdog) and data
must be recoverable (a backup module). These assertions pin that in place.
"""
import os
import py_compile

from wizard.components import COMPONENTS

REPO = os.path.join(os.path.dirname(__file__), "..")


def _read(rel: str) -> str:
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return fh.read()


# Long-running services that must carry a Docker healthcheck. (OmniRoute's app,
# mem0-dashboard, Diun and the MCP servers have no in-container HTTP client, so
# the watchdog covers their down-detection instead.)
_MIN_HEALTHCHECKS = {
    "stacks/core/hermes/docker-compose.yml": 1,
    "stacks/core/mem0/docker-compose.yml": 2,
    "stacks/core/omniroute/docker-compose.yml": 1,
    "stacks/recommended/headroom/docker-compose.yml": 1,
    "stacks/recommended/inference/docker-compose.yml": 2,
    "stacks/recommended/ingress/docker-compose.yml": 1,
    "stacks/recommended/monitoring/docker-compose.yml": 1,
}


def test_key_services_have_healthchecks():
    for path, at_least in _MIN_HEALTHCHECKS.items():
        found = _read(path).count("healthcheck:")
        assert found >= at_least, f"{path}: want >= {at_least} healthcheck(s), found {found}"


def test_watchdog_shipped_with_monitoring():
    compose = _read("stacks/recommended/monitoring/docker-compose.yml")
    assert "agentstack-watchdog" in compose
    assert "/app/watchdog.py" in compose
    assert os.path.exists(os.path.join(REPO, "stacks/recommended/monitoring/watchdog.py"))


def test_watchdog_script_compiles():
    py_compile.compile(
        os.path.join(REPO, "stacks/recommended/monitoring/watchdog.py"), doraise=True
    )


def test_backup_component_and_module_present():
    assert "backup" in COMPONENTS
    assert COMPONENTS["backup"].tier == "recommended"
    for name in ("docker-compose.yml", "Dockerfile", "backup.sh", "restore.sh", "README.md"):
        assert os.path.exists(
            os.path.join(REPO, "stacks/recommended/backup", name)
        ), f"missing stacks/recommended/backup/{name}"
