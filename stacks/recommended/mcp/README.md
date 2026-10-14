# mcp — tool pool (recommended)

The standing MCP (Model Context Protocol) servers the agent uses as tools. Ships
the GitHub and Playwright servers; add more (graphify, context7, etc.) as needed.

## Upstream credit

- **GitHub MCP Server** by GitHub — <https://github.com/github/github-mcp-server>
- **Playwright MCP** by Microsoft — <https://github.com/microsoft/playwright-mcp>
- MCP by the **Model Context Protocol** project — <https://modelcontextprotocol.io>

agentstack provides only the deployment config. Credit for each server goes to
its authors. Licenses: see `THIRD_PARTY_NOTICES.md`.

## Adding more servers

`graphify` and other MCP servers can be added as extra services here, or wired
in as hosted/remote connectors. Third-party servers are referenced with install
instructions, not redistributed.
