# Third-Party Notices

agentstack deploys third-party software. Each tool is the property of its
authors and is governed by its own license. This file collects the required
notices; see [CREDITS.md](CREDITS.md) for the full roster with links.

> Licenses marked **(to verify)** are confirmed against the upstream project
> before each public release — the release CI gate blocks on any unverified
> entry (`wizard.credits.unverified_credits`).

| Tool | Author | License |
|------|--------|---------|
| Hermes Agent | Nous Research | Apache-2.0 |
| OmniRoute | diegosouzapw | MIT |
| Headroom | Headroom Labs | Apache-2.0 |
| mem0 | mem0ai | Apache-2.0 |
| Ollama | Ollama | MIT |
| Open WebUI | Open WebUI Inc. | Open WebUI License (BSD-3-Clause + branding clause) |
| Nginx Proxy Manager | jc21 | MIT |
| Netdata | Netdata | GPL-3.0 |
| Diun | crazy-max | MIT |
| GitHub MCP Server | GitHub | MIT |
| Playwright MCP | Microsoft | Apache-2.0 |
| HexStrike AI | Muhammad Osama (0x4m4) | MIT |

> **Open WebUI branding clause.** Open WebUI's license is BSD-3-Clause with an
> added condition: you may not remove or alter the "Open WebUI" branding unless
> your deployment serves fewer than 50 users in any 30-day window, you obtain the
> copyright holder's permission, or you hold an enterprise license. agentstack
> ships Open WebUI unmodified and does not rebrand it; if you self-host it for a
> larger audience, honor that condition. See the upstream LICENSE.

**Referenced, not bundled.** The agents/skills pack references external skill
catalogs with install instructions instead of redistributing them — notably
ECC (Everything Claude Code, `affaan-m/ECC`, MIT). agentstack ships only its own
original skills; if you copy a third-party skill into your pack, preserve its
license and origin attribution.

agentstack's own code (the wizard, Compose modules, host-gateway) is MIT,
© 2026 Sasindu Dilshan Ranwadana.
