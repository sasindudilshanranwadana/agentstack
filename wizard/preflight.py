"""Preflight checks and platform detection for the installer.

Cross-platform: the wizard runs on Linux, macOS, and Windows. This module only
reports what it finds; the caller decides how to present issues.
"""

from __future__ import annotations

import shutil
import subprocess


def detect_platform(plat: str | None = None) -> str:
    """Map a sys.platform-style string to linux | macos | windows."""
    import sys

    p = plat if plat is not None else sys.platform
    if p.startswith("linux"):
        return "linux"
    if p == "darwin":
        return "macos"
    if p.startswith("win"):
        return "windows"
    return "linux"


def has_docker() -> bool:
    return shutil.which("docker") is not None


def has_compose_v2() -> bool:
    if not has_docker():
        return False
    try:
        r = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def preflight() -> list[str]:
    """Return a list of human-readable problems; empty means ready to install."""
    issues: list[str] = []
    if not has_docker():
        issues.append(
            "Docker not found. Install Docker Engine (Linux) or Docker Desktop "
            "(macOS/Windows): https://docs.docker.com/get-docker/"
        )
    elif not has_compose_v2():
        issues.append(
            "Docker Compose v2 not available. Update Docker to a version that "
            "includes `docker compose`."
        )
    return issues
