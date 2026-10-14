# monitoring — health & update alerts (recommended)

- **Netdata** (`:19999`) — live metrics and health for the host and containers.
- **Diun** — watches your running images and notifies when an update is
  published (it does not auto-update). Notification channel is set by the wizard.

## Upstream credit

- **Netdata** — <https://github.com/netdata/netdata> (GPL-3.0)
- **Diun** by **crazy-max** — <https://github.com/crazy-max/diun> (MIT)

agentstack provides only the deployment config. Licenses: see
`THIRD_PARTY_NOTICES.md`.

## Notes

- Diun mounts the Docker socket **read-only** — that is how it inspects your
  containers' images. Remove the `diun` service if you don't want it.
- Netdata's `/proc`, `/sys` read-only mounts give host-level metrics on Linux;
  on Docker Desktop they reflect the Docker VM.
