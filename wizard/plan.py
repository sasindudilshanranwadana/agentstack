"""The single safe composition of a selection into an install plan.

This is the ONLY path callers should use to turn user answers into something
installable. It composes resolution → consent gating → platform filtering →
compose-file + env generation in the correct order, so a caller cannot
accidentally skip consent gating and enable an opt-in component.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from wizard.components import (
    apply_consent,
    filter_by_platform,
    resolve_selection,
)
from wizard.envgen import compose_files, generate_env


@dataclass(frozen=True)
class InstallPlan:
    components: frozenset[str]
    compose_files: tuple[str, ...]
    env: dict[str, str]


def build_install_plan(
    selected: Iterable[str],
    consented: Iterable[str],
    integration_choices: dict[str, str | Iterable[str]],
    user_values: dict[str, str],
    platform: str,
) -> InstallPlan:
    """Compose the full, safe install plan from the user's answers.

    Order matters: resolve dependencies, drop opt-in components without consent,
    then drop anything the platform can't run. Core always survives.

    Trusted-caller API: `consented` is taken at face value, so a programmatic
    caller that passes an opt-in id here enables that component without a human
    typing anything. The interactive, human-typed consent gate lives in the
    wizard UI (`wizard.__main__`); don't wrap this function in a way that
    bypasses it for privileged components like host-gateway.
    """
    resolved = resolve_selection(selected)
    gated = apply_consent(resolved, consented)
    final = filter_by_platform(gated, platform)
    return InstallPlan(
        components=frozenset(final),
        compose_files=tuple(compose_files(final)),
        env=generate_env(final, integration_choices, user_values),
    )
