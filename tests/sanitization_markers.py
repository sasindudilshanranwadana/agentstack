"""Shared markers for the publish-safety scans.

The PUBLIC repo must not itself contain the maintainer's private infra names, so
the tracked lists here hold only **generic, non-identifying** markers and regex
*shapes* that name nothing specific.

Deployment-specific identifiers (your own private host, project, or image names)
go in an untracked file — ``tests/private-markers.txt``, one marker per line,
``#`` for comments — which these scans load when it is present. That keeps your
local run and your private CI catching your own names, while the public source
ships none of them.

This module is not a test (pytest only collects ``test_*.py``); it is imported
by ``test_sanitization.py`` and ``test_stacks_hygiene.py``.
"""

import os
import re

# Generic markers safe to ship publicly: dev-tool home dirs that shipped files
# should never reference, and the private "*-hardened" image-tag suffix (which
# names no specific tool).
GENERIC_MARKERS: tuple[str, ...] = (
    "/root/.claude",
    "/root/.codex",
    "-hardened",
)

# Secret / infra SHAPES — matched by pattern, naming nothing. The first is the
# Tailscale CGNAT range (100.64.0.0/10); the rest are common token shapes.
CGNAT_RE = re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    CGNAT_RE,
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

_LOCAL_FILE = os.path.join(os.path.dirname(__file__), "private-markers.txt")


def extra_markers() -> tuple[str, ...]:
    """Deployment-specific literal markers from the untracked local file, if any."""
    try:
        with open(_LOCAL_FILE, encoding="utf-8") as f:
            return tuple(
                line.strip() for line in f
                if line.strip() and not line.lstrip().startswith("#")
            )
    except FileNotFoundError:
        return ()


def literal_markers() -> tuple[str, ...]:
    """All literal (substring) markers: generic plus any local additions."""
    return GENERIC_MARKERS + extra_markers()
