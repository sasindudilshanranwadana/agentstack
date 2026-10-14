# host-gateway source

agentstack's own privileged host-access component (MIT). The built image is
produced from this directory (`build.context: ./src/host-gateway`).

## Layout

- `app/server.py` — HTTP server: `/exec`, `/sql`, `/decide`, `/whoami`,
  `/health`. Token-gated, rate-limited, every action written to a redacted
  append-only audit log. Runs approved commands in the host namespaces via
  `nsenter` (hence `privileged` + `pid: host` in the compose module).
- `app/policy.py` — tier policy (`read` / `operate` / `root`), argv allowlists,
  read-only SQL rules, and the gated/owner-only patterns that force approval.
  Protected containers and project dirs default to the agentstack stack and
  extend via `HG_PROTECTED_CONTAINERS` / `HG_PROTECTED_PROJECTS`.
- `app/hgctl.py` — mint/revoke tokens and release approvals from the host.
- `app/test_host_gateway.py` — the component's own test suite (stubs host
  access, needs no privileges): `python3 -m unittest test_host_gateway`.

## Approval model

Protected, reversible commands are held for an **approver**-tier token to
release over the network (`POST /decide`). Irreversible or trust-widening
commands (destroying data, widening the gateway's own trust) are **owner-only**:
only the host operator releases them, on the host, with
`hgctl.py owner-decide`. A backup plus a wait is not permission to delete.

## Security limitations

The tiers reduce *accidental* damage by a *well-behaved* agent; they are **not**
a sandbox for a hostile or compromised one. A `root` token is full host root
(`bash -lc` via `nsenter`); the `read`/`operate` allowlists are best-effort and
escapable; and the approval store is a bind-mounted file a root agent can write,
so it can forge approvals. Output redaction is best-effort. Enable this, and
mint a token, only for an agent and host you fully trust — to contain an
untrusted agent, isolate the whole stack in a disposable VM instead.

See `stacks/optin/host-gateway/README.md` for what it does and its blast radius.
