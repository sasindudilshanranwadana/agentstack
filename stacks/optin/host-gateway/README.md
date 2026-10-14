# host-gateway — privileged host access (OPT-IN) ⚠️

**Off by default. The wizard requires explicit, typed consent to enable it.**

host-gateway lets the agent run commands on the host through **tiered,
token-gated** access (read / operate / root), with protected operations
requiring approval and every action written to a redacted audit log.

## Blast radius

Enabling this gives an AI agent the ability to execute host-level commands.
Only turn it on if you understand and accept that. It is **Linux hosts only**
and is never on by default.

## Security limitations — read before enabling

The tiers are **convenience guardrails against a well-behaved agent's mistakes,
not a security sandbox against a hostile or compromised one.** Specifically:

- A **root**-tier token runs `bash -lc` in the host namespaces — that is **full
  host root** by design.
- The **read** and **operate** allowlists are best-effort. A determined agent
  can find escapes (crafted `docker`/`ip`/`systemctl` invocations, etc.), so do
  not treat a lower tier as a hard containment boundary.
- The approval store lives in a bind-mounted file the executed commands can
  reach, so a root-tier agent can forge its own approvals.
- Output redaction in the audit log is best-effort, not a guarantee.

**Therefore:** enable host-gateway, and hand out a token, only for an agent and
a host you trust as much as yourself. If you need to contain an *untrusted*
agent, this component is not that boundary — run the whole stack in a disposable
VM instead. These are known limitations, documented on purpose; hardening the
lower tiers into a real boundary is tracked as future work.

## Run

```bash
cp .env.example .env     # set BIND_ADDR / AGENTSTACK_DATA if needed (no secret)
docker network create agentstack 2>/dev/null || true
docker compose up -d

# Mint an access token for an agent (tiers: read | operate | root | approver):
docker exec host-gateway python hgctl.py mint my-agent read
```

Tokens are random, stored only as hashes, and never printed again — keep the
one `mint` prints. See `src/host-gateway/README.md` for the full API and the
approval model.
