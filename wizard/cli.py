"""Small pure helpers for the interactive wizard (kept separate from I/O so
they can be unit-tested).
"""

from __future__ import annotations

from collections.abc import Sequence


def parse_choice(answer: str, options: Sequence[str], default: str) -> str:
    """Resolve a user's menu answer to an option.

    Empty → default. A 1-based index within range → that option. Anything else
    (0, negatives, out-of-range, non-numeric) → default. Never silently returns
    the wrong option.
    """
    answer = answer.strip()
    if not answer:
        return default
    try:
        n = int(answer)
    except ValueError:
        return default
    if 1 <= n <= len(options):
        return options[n - 1]
    return default
