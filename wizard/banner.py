"""ASCII branding banner for the agentstack wizard.

The wordmark art lives in assets/wordmark.txt and is read with stdlib only — no
runtime dependency on a figlet library. FRAMES is a simple line-by-line reveal
used for the launch animation (the wizard prints frames with a small delay;
that UX lives in Plan 3). render_banner() returns the final composed banner with
the product name, tagline, and author credit.
"""

from __future__ import annotations

from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"
WORDMARK = (_ASSETS / "wordmark.txt").read_text(encoding="utf-8").rstrip("\n")

TAGLINE = "agentstack · self-hosted Hermes agent + full AI infrastructure"
CREDIT = "by Sasindu Dilshan Ranwadana (@sasiverse) · sasiverse.com"


def _reveal_frames(wordmark: str) -> tuple[str, ...]:
    """Progressive line-by-line reveal of the wordmark."""
    lines = wordmark.split("\n")
    return tuple("\n".join(lines[: i + 1]) for i in range(len(lines)))


FRAMES: tuple[str, ...] = _reveal_frames(WORDMARK)


def render_banner() -> str:
    """Return the final composed banner: wordmark + tagline + author credit."""
    return f"{WORDMARK}\n\n    {TAGLINE}\n    {CREDIT}\n"
