"""Run the host-gateway component's own test suite as part of the repo suite.

The source lives under src/host-gateway/app and uses plain `import policy` /
`import server`, so it runs from its own directory. We invoke it as a subprocess
rather than importing it here to keep that import root isolated from the wizard.
"""
import os
import subprocess
import sys

APP_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "host-gateway", "app")


def test_host_gateway_unit_suite_passes():
    assert os.path.isdir(APP_DIR), "host-gateway source is missing"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "test_host_gateway"],
        cwd=APP_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_host_gateway_ships_source_not_placeholder():
    for name in ("server.py", "policy.py", "hgctl.py"):
        path = os.path.join(APP_DIR, name)
        assert os.path.isfile(path), f"{name} missing from host-gateway source"
