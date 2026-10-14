"""agentstack install wizard — interactive entrypoint.

Runs on Linux, macOS, and Windows (`python3 -m wizard`). Thin I/O layer over the
tested pure logic in components/integrations/envgen/plan. Writes a git-ignored
.env and a compose selection, then optionally brings the stack up.
"""

from __future__ import annotations

import itertools
import os
import sys
import threading
import time
from pathlib import Path

from wizard import banner
from wizard.cli import parse_choice
from wizard.components import COMPONENTS, CORE_IDS, OPTIN_IDS, TIERS
from wizard.credits import unverified_credits
from wizard.integrations import INGRESS, NOTIFICATIONS, PROVIDERS
from wizard.plan import build_install_plan
from wizard.preflight import detect_platform, preflight

# The repo root the wizard operates on. Defaults to this checkout; the native
# bootstrapper sets AGENTSTACK_REPO so a frozen build can drive a downloaded one.
REPO = Path(os.environ.get("AGENTSTACK_REPO") or Path(__file__).resolve().parent.parent)

# ---- terminal styling (ANSI, only emitted to a real TTY) ----
_TTY = sys.stdout.isatty()
_CYAN, _VIOLET, _GREEN, _AMBER, _DIM, _BOLD = "96", "95", "92", "93", "2", "1"


def _c(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _TTY else text


class _Spinner:
    """A tiny braille spinner for a step; a plain line when not a TTY."""

    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, label: str) -> None:
        self.label = label
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "_Spinner":
        if _TTY:
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            print(f"  {self.label} ...")
        return self

    def _spin(self) -> None:
        for frame in itertools.cycle(self._FRAMES):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\r  {_c(_CYAN, frame)} {self.label}")
            sys.stdout.flush()
            time.sleep(0.08)

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.3)
        if _TTY:
            sys.stdout.write(f"\r  {_c(_GREEN, '✓')} {self.label}\n")
            sys.stdout.flush()


def _animate_banner() -> None:
    if not _TTY:
        print(banner.render_banner())
        return
    # Two-tone sweep reveal of the wordmark, line by line.
    for frame in banner.FRAMES:
        sys.stdout.write("\x1b[2J\x1b[H" + _c(_CYAN, frame) + "\n")
        sys.stdout.flush()
        time.sleep(0.09)
    # Typewriter tagline, then the credit.
    sys.stdout.write("\n    ")
    for ch in banner.TAGLINE:
        sys.stdout.write(_c(_BOLD, ch))
        sys.stdout.flush()
        time.sleep(0.008)
    sys.stdout.write("\n    " + _c(_DIM, banner.CREDIT) + "\n\n")
    sys.stdout.flush()


def _ask_yes(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    ans = input(f"{prompt} {suffix} ").strip().lower()
    if not ans:
        return default
    return ans in ("y", "yes")


def _choose(prompt: str, options: tuple[str, ...], default: str) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        mark = " (default)" if opt == default else ""
        print(f"  {i}) {opt}{mark}")
    ans = input("Choose a number (Enter for default): ")
    choice = parse_choice(ans, options, default)
    if ans.strip() and choice == default and ans.strip() != default:
        print("  ! invalid choice, using default")
    return choice


def _select_components() -> tuple[list[str], list[str]]:
    selected: list[str] = []
    consented: list[str] = []
    print("\n" + _c(_CYAN, "Core (always installed): ") + ", ".join(sorted(CORE_IDS)))
    for tier in ("recommended", "optin"):
        print("\n" + _c(_BOLD, f"{tier.upper()} components:"))
        for cid, comp in COMPONENTS.items():
            if comp.tier != tier:
                continue
            if tier == "recommended":
                if _ask_yes(f"  include {cid} ({comp.name})?", default=True):
                    selected.append(cid)
            else:  # optin
                print(f"  ⚠  {cid}: {comp.name}")
                for line in _OPTIN_WARNINGS.get(cid, ()):
                    print(f"     {line}")
                if _ask_yes(f"     ENABLE {cid}? (grants extra power)", default=False):
                    typed = input(f"     type '{cid}' to confirm: ").strip()
                    if typed == cid:
                        selected.append(cid)
                        consented.append(cid)
                    else:
                        print("     not confirmed — leaving off")
    return selected, consented


# Honest, per-component blast-radius warnings shown before the typed consent.
_OPTIN_WARNINGS: dict[str, tuple[str, ...]] = {
    "host-gateway": (
        "This gives the agent the ability to run commands on THIS HOST.",
        "The read/operate/root tiers reduce accidental damage by a well-behaved",
        "agent — they are NOT a sandbox. A root token is full host root, and a",
        "determined or compromised agent can escape the lower tiers. Enable it",
        "only for an agent and a host you trust as much as yourself.",
        "See stacks/optin/host-gateway/README.md → 'Security limitations'.",
    ),
    "hexstrike": (
        "Bundles offensive-security tooling. Only run it against systems you are",
        "authorized to test.",
    ),
}


def _write_env(path: Path, content: str) -> None:
    """Write .env with owner-only perms, backing up any existing file first.

    .env holds secrets the user fills in, so it must not be world-readable, and
    an existing one must not be silently clobbered.
    """
    if path.exists():
        backup = path.with_suffix(".env.bak")
        path.replace(backup)
        print(f"  (backed up existing .env to {backup.name})")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)


def run() -> int:
    _animate_banner()
    platform = detect_platform()
    print(f"  {_c(_GREEN, '✓')} platform detected: {_c(_BOLD, platform)}")

    with _Spinner("checking prerequisites (docker, compose)"):
        issues = preflight()
    if issues:
        print(_c(_AMBER, "\nPreflight found problems:"))
        for i in issues:
            print(f"  {_c(_AMBER, '✗')} {i}")
        print("\nFix these and re-run. Aborting.")
        return 1

    selected, consented = _select_components()

    provider = _choose("LLM provider (you can add more later):", PROVIDERS, "openai")
    notification = _choose("Notification channel:", NOTIFICATIONS, "none")
    ingress = _choose("Ingress mode:", INGRESS, "localhost")

    plan = build_install_plan(
        selected=selected,
        consented=consented,
        integration_choices={
            "provider": (provider,),
            "notification": notification,
            "ingress": ingress,
        },
        user_values={},
        platform=platform,
    )

    print("\n" + _c(_GREEN, "✓ planned components: ") + ", ".join(sorted(plan.components)))
    print("Compose files:")
    for f in plan.compose_files:
        print(f"  - {f}")

    env_path = REPO / ".env"
    lines = ["BIND_ADDR=127.0.0.1", "PUBLIC_HOST=localhost", "TZ=UTC", ""]
    lines += [f"{k}={v}" for k, v in plan.env.items()]
    lines.append("")
    lines.append("COMPOSE_FILE=" + ":".join(plan.compose_files))
    _write_env(env_path, "\n".join(lines) + "\n")
    print(f"\n{_c(_GREEN, '✓')} wrote {_c(_BOLD, str(env_path))} (fill in the blank keys before starting).")
    print("Then run:  " + _c(_CYAN, "scripts/up.sh") + "   (or: docker compose up -d)")

    unverified = unverified_credits()
    if unverified:
        print(
            "\nNote: some upstream licenses are still marked for verification: "
            + ", ".join(unverified)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
