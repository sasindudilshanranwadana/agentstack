"""Repo-wide publish-safety gate.

Scans shippable content (not tests, which legitimately contain the markers they
assert against) for personal infra references and secret-shaped strings. This is
the fast local gate; CI additionally runs gitleaks over full history.
"""

import glob
import os

from tests.sanitization_markers import SECRET_PATTERNS, literal_markers

# Dirs/files excluded from the scan: VCS, local venv, scratch, and the test
# suite itself (the shared markers module and the untracked local marker file).
_EXCLUDE_PREFIXES = (
    ".git/",
    ".venv/",
    ".superpowers/",
    "tests/",
    "./tests/",
    "docs/superpowers/",  # internal planning artifacts, not shipped
)


def _shippable_files():
    for path in glob.glob("**/*", recursive=True):
        if not os.path.isfile(path):
            continue
        norm = path.replace("\\", "/")
        if any(norm.startswith(p) for p in _EXCLUDE_PREFIXES):
            continue
        yield path


def _read(path):
    try:
        return open(path, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return ""  # binary / unreadable — nothing to leak as text


def test_no_personal_infra_markers():
    markers = literal_markers()
    hits = []
    for path in _shippable_files():
        text = _read(path)
        for marker in markers:
            if marker in text:
                hits.append(f"{path}: {marker}")
    assert not hits, "personal infra references leaked:\n" + "\n".join(hits)


def test_no_secret_shaped_strings():
    hits = []
    for path in _shippable_files():
        text = _read(path)
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(f"{path}: {pat.pattern}")
    assert not hits, "secret-shaped strings leaked:\n" + "\n".join(hits)
