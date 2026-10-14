"""Hygiene + validity checks for every stack module.

Data-driven: discovers every stacks/**/docker-compose.yml so new modules are
covered automatically. Each module must (1) validate under `docker compose
config` using only built-in defaults, and (2) contain no secrets or personal
references. hermes additionally must be portable (no host networking / sock).
"""

import glob
import os
import shutil
import subprocess

import pytest

from tests.sanitization_markers import CGNAT_RE, literal_markers

COMPOSE_FILES = sorted(glob.glob("stacks/**/docker-compose.yml", recursive=True))

# Values an installer/user would supply; lets `config` validate required vars.
_VALIDATION_ENV = {
    "BIND_ADDR": "127.0.0.1",
    "MEM0_POSTGRES_PASSWORD": "validation-only",
}


def test_stacks_directory_exists():
    assert os.path.isdir("stacks")


def test_compose_files_discovered():
    assert len(COMPOSE_FILES) >= 3, COMPOSE_FILES


@pytest.mark.parametrize("compose", COMPOSE_FILES)
@pytest.mark.skipif(not shutil.which("docker"), reason="docker not available")
def test_compose_validates(compose):
    r = subprocess.run(
        ["docker", "compose", "-f", compose, "config", "-q"],
        capture_output=True,
        text=True,
        env={**os.environ, **_VALIDATION_ENV},
    )
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("compose", COMPOSE_FILES)
def test_no_personal_refs(compose):
    text = open(compose).read()
    env_example = compose.replace("docker-compose.yml", ".env.example")
    if os.path.exists(env_example):
        text += open(env_example).read()
    for bad in literal_markers():
        assert bad not in text, f"{bad!r} leaked in {compose}"
    assert not CGNAT_RE.search(text), f"Tailscale CGNAT IP leaked in {compose}"


def test_hermes_is_portable():
    text = open("stacks/core/hermes/docker-compose.yml").read()
    assert "network_mode: host" not in text
    assert "/var/run/docker.sock" not in text
