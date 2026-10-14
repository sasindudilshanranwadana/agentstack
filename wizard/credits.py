"""Generate CREDITS.md from the component registry and flag unverified
licenses. Used both to render the credits file and as a CI gate: every
component must carry a complete, verified credit before public release.
"""

from __future__ import annotations

from wizard.components import COMPONENTS

_SENTINEL = "see-CREDITS"

_HEADER = """# Credits

agentstack is orchestration glue — a deployment wizard and a set of Compose
modules. **Every tool it bundles is the work of its original authors.** We only
provide the configuration to run them together. All credit, and thanks, goes to
the upstream projects below.

"""


def render_credits() -> str:
    """Render CREDITS.md listing each upstream tool, author, link, and license."""
    rows: dict[str, tuple[str, str, str]] = {}
    for c in COMPONENTS.values():
        cr = c.credit
        rows[cr.tool] = (cr.author, cr.url, cr.license)
    lines = [_HEADER.rstrip("\n"), ""]
    for tool in sorted(rows):
        author, url, license_ = rows[tool]
        lines.append(f"- **{tool}** by {author} — <{url}> ({license_})")
    lines.append("")
    return "\n".join(lines) + "\n"


def unverified_credits() -> list[str]:
    """Component ids whose credit is incomplete or still carries the sentinel.

    A CI gate fails the build if this is non-empty for a public release.
    """
    bad: list[str] = []
    for c in COMPONENTS.values():
        cr = c.credit
        complete = all((cr.tool, cr.author, cr.url, cr.license))
        if not complete or cr.license == _SENTINEL:
            bad.append(c.id)
    return sorted(bad)
