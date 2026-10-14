"""Component registry for the agentstack wizard.

Single source of truth for which components exist, their tier, their upstream
dependencies, the ports/env keys they need, the platforms they run on, and the
upstream credit each one carries.

NOTE: upstream license strings here are best-effort and are VERIFIED against
each upstream project during the credits/sanitization pass (Plan 4) before the
repo is made public. The registry only guarantees the fields are present.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

TIERS = ("core", "recommended", "optin")

ALL_PLATFORMS = ("linux", "macos", "windows")


@dataclass(frozen=True)
class Credit:
    """Attribution for an upstream tool (see §3.1 of the design spec)."""

    tool: str
    author: str
    url: str
    license: str


@dataclass(frozen=True)
class Component:
    """One installable component, mapped to a compose module under stacks/."""

    id: str
    name: str
    tier: str
    requires: tuple[str, ...]
    ports: tuple[int, ...]
    env_keys: tuple[str, ...]
    credit: Credit
    platforms: tuple[str, ...]


_COMPONENT_LIST: tuple[Component, ...] = (
    # ---- core (always installed: the boss + its vitals) ----
    Component(
        id="hermes",
        name="Hermes Agent",
        tier="core",
        requires=("omniroute", "mem0"),
        ports=(),
        env_keys=("HERMES_DISCORD_TOKEN",),
        credit=Credit(
            tool="Hermes Agent",
            author="Nous Research",
            url="https://github.com/NousResearch",
            license="Apache-2.0",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="omniroute",
        name="OmniRoute LLM gateway",
        tier="core",
        requires=(),
        ports=(20129,),
        env_keys=("OMNIROUTE_API_KEY", "OMNIROUTE_MGMT_API_KEY"),
        credit=Credit(
            tool="OmniRoute",
            author="diegosouzapw",
            url="https://github.com/diegosouzapw/OmniRoute",
            license="MIT",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="mem0",
        name="mem0 shared memory",
        tier="core",
        requires=(),
        ports=(8888,),
        env_keys=("MEM0_POSTGRES_PASSWORD",),
        credit=Credit(
            tool="mem0",
            author="mem0ai",
            url="https://github.com/mem0ai/mem0",
            license="Apache-2.0",
        ),
        platforms=ALL_PLATFORMS,
    ),
    # ---- recommended (default on, toggle off) ----
    Component(
        id="headroom",
        name="Headroom context compression",
        tier="recommended",
        requires=("omniroute",),
        ports=(8787,),
        env_keys=(),
        credit=Credit(
            tool="Headroom",
            author="Headroom Labs",
            url="https://github.com/headroomlabs-ai/headroom",
            license="Apache-2.0",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="mcp",
        name="MCP tool pool",
        tier="recommended",
        requires=(),
        ports=(8082,),
        env_keys=("GITHUB_TOKEN",),
        credit=Credit(
            tool="MCP servers (github, playwright)",
            author="GitHub, Microsoft (see CREDITS.md)",
            url="https://github.com/modelcontextprotocol",
            license="MIT / Apache-2.0 (see CREDITS.md)",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="inference",
        name="Local inference (Ollama + Open WebUI)",
        tier="recommended",
        requires=(),
        ports=(11434, 3101),
        env_keys=(),
        credit=Credit(
            tool="Ollama + Open WebUI",
            author="Ollama & Open WebUI Inc.",
            url="https://github.com/ollama/ollama",
            license="Ollama: MIT / Open WebUI: Open WebUI License, BSD-3 + branding (see THIRD_PARTY_NOTICES.md)",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="ingress",
        name="Ingress (nginx-proxy-manager)",
        tier="recommended",
        requires=(),
        ports=(80, 443),
        env_keys=(),
        credit=Credit(
            tool="Nginx Proxy Manager",
            author="jc21",
            url="https://github.com/NginxProxyManager/nginx-proxy-manager",
            license="MIT",
        ),
        platforms=ALL_PLATFORMS,
    ),
    Component(
        id="monitoring",
        name="Monitoring (Netdata + Diun)",
        tier="recommended",
        requires=(),
        ports=(19999,),
        env_keys=(),
        credit=Credit(
            tool="Netdata + Diun",
            author="Netdata & crazy-max",
            url="https://github.com/netdata/netdata",
            license="GPL-3.0 / MIT (see CREDITS.md)",
        ),
        platforms=ALL_PLATFORMS,
    ),
    # ---- opt-in (off by default, explicit consent) ----
    Component(
        id="host-gateway",
        name="Host gateway (privileged host access)",
        tier="optin",
        requires=(),
        ports=(),
        # No signing secret: access tokens are random and minted with hgctl.py.
        env_keys=(),
        credit=Credit(
            tool="agentstack host-gateway",
            author="Sasindu Dilshan Ranwadana",
            url="https://github.com/sasindudilshanranwadana/agentstack",
            license="MIT",
        ),
        platforms=("linux",),
    ),
    Component(
        id="hexstrike",
        name="HexStrike AI security tooling",
        tier="optin",
        requires=(),
        ports=(8899,),
        env_keys=(),
        credit=Credit(
            tool="HexStrike AI",
            author="Muhammad Osama (0x4m4)",
            url="https://github.com/0x4m4/hexstrike-ai",
            license="MIT",
        ),
        platforms=ALL_PLATFORMS,
    ),
)

COMPONENTS: dict[str, Component] = {c.id: c for c in _COMPONENT_LIST}

CORE_IDS: frozenset[str] = frozenset(
    c.id for c in _COMPONENT_LIST if c.tier == "core"
)
OPTIN_IDS: frozenset[str] = frozenset(
    c.id for c in _COMPONENT_LIST if c.tier == "optin"
)


def resolve_selection(selected: Iterable[str]) -> set[str]:
    """Expand a user selection into the full set to install.

    Adds every transitive requirement, always unions in the core components,
    and raises KeyError on an unknown component id.
    """
    result: set[str] = set(CORE_IDS)
    pending = list(selected)
    while pending:
        cid = pending.pop()
        if cid not in COMPONENTS:
            raise KeyError(cid)
        if cid in result:
            continue
        result.add(cid)
        pending.extend(COMPONENTS[cid].requires)
    return result


def filter_by_platform(ids: set[str], platform: str) -> set[str]:
    """Drop components whose declared platforms exclude the target platform.

    Core components support every platform, so core is never dropped.
    """
    return {cid for cid in ids if platform in COMPONENTS[cid].platforms}


def apply_consent(resolved: set[str], consented: Iterable[str]) -> set[str]:
    """Drop opt-in components the user has not explicitly consented to.

    Opt-in components (host-gateway, hexstrike) grant powerful host/security
    capabilities, so they are never enabled without being named in `consented`.
    Non-opt-in components are unaffected.
    """
    denied = OPTIN_IDS - set(consented)
    return resolved - denied
