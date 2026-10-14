"""Generate the compose-file list and the .env contents from a resolved
selection plus the user's integration choices and supplied values.

Secret hygiene: generate_env only ever fills a key from `user_values`. A key the
user did not supply is emitted with an empty value, never a fabricated secret.
The result is written to a local .env at install time and is never committed.
"""

from __future__ import annotations

from collections.abc import Iterable

from wizard.components import COMPONENTS, TIERS
from wizard.integrations import render_integration

_TIER_ORDER = {tier: i for i, tier in enumerate(TIERS)}


def compose_files(selected: set[str]) -> list[str]:
    """Return ordered relative paths to each selected component's compose file.

    Ordered by tier (core first) then component id, for stable compose layering.
    """
    ordered = sorted(
        selected, key=lambda cid: (_TIER_ORDER[COMPONENTS[cid].tier], cid)
    )
    return [
        f"stacks/{COMPONENTS[cid].tier}/{cid}/docker-compose.yml" for cid in ordered
    ]


def generate_env(
    selected: set[str],
    integration_choices: dict[str, str | Iterable[str]],
    user_values: dict[str, str],
) -> dict[str, str]:
    """Assemble the env map for a selection.

    Keys come from the selected components plus the chosen integrations. Each
    integration kind may carry a single choice (a str) or several (an iterable
    of str) — providers are multi-select per spec §5, so picking more than one
    wires every chosen provider's keys. Each key's value is taken from
    `user_values` if present, otherwise left empty (never fabricated).
    """
    keys: set[str] = set()
    for cid in selected:
        keys.update(COMPONENTS[cid].env_keys)
    for kind, choice in integration_choices.items():
        choices = (choice,) if isinstance(choice, str) else tuple(choice)
        for one in choices:
            keys.update(render_integration(kind, one).keys())
    return {key: user_values.get(key, "") for key in sorted(keys)}
