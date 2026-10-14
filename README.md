<!-- agentstack -->

```
                        _       _             _
  __ _  __ _  ___ _ __ | |_ ___| |_ __ _  ___| | __
 / _` |/ _` |/ _ \ '_ \| __/ __| __/ _` |/ __| |/ /
| (_| | (_| |  __/ | | | |_\__ \ || (_| | (__|   <
 \__,_|\__, |\___|_| |_|\__|___/\__\__,_|\___|_|\_\
       |___/
```

**agentstack** — self-hosted Hermes agent + full AI infrastructure. Pick your
stack, bring your own keys.

> by Sasindu Dilshan Ranwadana ([@sasiverse](https://x.com/sasiverse)) · sasiverse.com · MIT

One repo, one wizard. Choose the components you want, wire in *your own* API
keys, and get a running stack with **Hermes as the orchestrator** — backed by an
LLM gateway (omniroute), shared memory (mem0), tools (MCP), local inference, and
monitoring. Runs on **Linux, macOS, and Windows** (Docker required).

> agentstack is **orchestration glue**. Every bundled tool is the work of its
> original authors — see [CREDITS.md](CREDITS.md). This is not an official
> distribution of any of them.

## Quick start

```bash
git clone https://github.com/sasindudilshanranwadana/agentstack
cd agentstack
./install.sh          # Linux / macOS
#  .\install.ps1      # Windows (PowerShell)
```

The wizard walks you through: pick components → consent for anything privileged
→ choose integrations → enter your keys (written only to a local `.env`) → it
brings up exactly what you selected.

## Components

| Tier | Component | What it is |
|------|-----------|------------|
| **Core** (always) | `hermes` | The orchestrator — the boss |
| | `omniroute` | LLM gateway, one endpoint for any provider |
| | `mem0` | Shared memory across sessions |
| **Recommended** | `headroom` | Context compression (cheaper long sessions) |
| | `mcp` | Tool pool (GitHub, Playwright, …) |
| | `inference` | Local models (Ollama + Open WebUI) |
| | `ingress` | Public entry + TLS (Nginx Proxy Manager) |
| | `monitoring` | Netdata + Diun |
| **Opt-in** ⚠ | `host-gateway` | Privileged, token-gated host access (Linux only) |
| | `hexstrike` | Security tooling (authorized use only) |

Opt-in components are **off by default** and require typed confirmation.

## Swappable integrations

Chosen in the wizard, not hardcoded:

- **Notifications:** Telegram · Discord · Slack · Email · none
- **LLM providers:** OpenAI · Anthropic · Google · OpenRouter · local (multi-select)
- **Ingress:** domain + Let's Encrypt TLS · localhost only

## Requirements

- Docker Engine (Linux) or Docker Desktop (macOS/Windows) with Compose v2
- Python 3.10+

## Secrets & safety

Your keys live **only** in a git-ignored `.env`. Nothing secret or personal is
committed. See [SECURITY.md](SECURITY.md).

## License

MIT © 2026 Sasindu Dilshan Ranwadana. See [LICENSE](LICENSE) and
[CREDITS.md](CREDITS.md).
