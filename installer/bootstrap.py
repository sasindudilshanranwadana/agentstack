"""agentstack setup bootstrapper.

This is the entrypoint that gets frozen into the native installers
(`agentstack-setup.exe`, the macOS `.dmg`, and the Linux binary). It bundles
its own Python, so an end user needs only Docker. It:

  1. verifies Docker + Compose v2 are available,
  2. downloads the agentstack repository into a directory of their choosing,
  3. runs the interactive wizard against that checkout, and
  4. offers to bring the selected stack up.

Pure standard library so it freezes cleanly with PyInstaller.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO_SLUG = "sasindudilshanranwadana/agentstack"
ZIP_URL = f"https://github.com/{REPO_SLUG}/archive/refs/heads/main.zip"
DEFAULT_DIR = Path.home() / "agentstack"
DOCKER_URL = "https://docs.docker.com/get-docker/"


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _pause(msg: str = "\nPress Enter to close.") -> None:
    """Keep a double-clicked console window open long enough to read it."""
    try:
        input(msg)
    except EOFError:
        pass


def check_docker() -> str | None:
    """Return an error message if Docker/Compose v2 is unusable, else None."""
    if not _have("docker"):
        return (
            "Docker was not found.\n"
            "  agentstack runs on Docker. Install Docker Desktop (macOS/Windows)\n"
            f"  or Docker Engine (Linux), then re-run this installer:\n    {DOCKER_URL}"
        )
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return (
            "Docker is installed but Compose v2 is not available.\n"
            "  Update Docker Desktop, or install the `docker compose` plugin."
        )
    return None


def _looks_like_checkout(path: Path) -> bool:
    return (path / "wizard").is_dir() and (path / "stacks").is_dir()


def download_repo(dest: Path) -> Path:
    """Download and extract the repo zip into `dest` (replacing it if present)."""
    print(f"\nDownloading agentstack into {dest} ...")
    with urllib.request.urlopen(ZIP_URL, timeout=120) as resp:  # noqa: S310 (trusted URL)
        payload = resp.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        top = archive.namelist()[0].split("/")[0]  # e.g. agentstack-main
        staging = dest.parent / f".{top}.tmp"
        if staging.exists():
            shutil.rmtree(staging)
        archive.extractall(staging)
    extracted = staging / top
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extracted), str(dest))
    shutil.rmtree(staging, ignore_errors=True)
    print("  done.")
    return dest


def _run_wizard(repo: Path) -> int:
    """Run the checkout's wizard (preferred) or the bundled one, on `repo`."""
    os.environ["AGENTSTACK_REPO"] = str(repo)
    sys.path.insert(0, str(repo))
    from wizard.__main__ import run as wizard_run

    return wizard_run()


def _offer_up(repo: Path) -> None:
    ans = input("\nBring the stack up now with `docker compose up -d`? [y/N] ").strip().lower()
    if ans in ("y", "yes"):
        subprocess.run(["docker", "compose", "up", "-d"], cwd=repo, check=False)
        print("\nStarted. Check status with:  docker compose ps")
    else:
        print(f"\nWhen ready:  cd {repo} && docker compose up -d")


def run() -> int:
    print("=== agentstack setup ===\n")

    problem = check_docker()
    if problem:
        print(problem)
        _pause()
        return 1

    target = os.environ.get("AGENTSTACK_DIR", "").strip()
    if not target:
        raw = input(f"Install directory [{DEFAULT_DIR}]: ").strip()
        target_path = Path(raw).expanduser() if raw else DEFAULT_DIR
    else:
        target_path = Path(target).expanduser()

    try:
        if _looks_like_checkout(target_path):
            print(f"Using the existing checkout at {target_path}")
        else:
            download_repo(target_path)
    except Exception as exc:  # network, zip, or filesystem failure
        print(f"\nCould not fetch agentstack: {exc}")
        _pause()
        return 1

    rc = _run_wizard(target_path)
    if rc == 0:
        _offer_up(target_path)
    _pause()
    return rc


if __name__ == "__main__":
    raise SystemExit(run())
