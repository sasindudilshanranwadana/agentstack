"""Integration check: the full selection of modules composes together.

test_stacks_hygiene validates each module's docker-compose.yml on its own. This
goes one step further and validates the *combined* file list the wizard emits
for a maximal install (core + recommended + both opt-ins), catching conflicts
that only appear when modules are merged — duplicate service names, port
clashes, or an undefined variable across the set.

Skipped when docker is unavailable (e.g. minimal CI image); the pure-Python
plan assembly is still asserted.
"""
import os
import shutil
import subprocess

import pytest

from wizard.components import COMPONENTS, OPTIN_IDS
from wizard.plan import build_install_plan

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _maximal_plan():
    return build_install_plan(
        selected=list(COMPONENTS),
        consented=list(OPTIN_IDS),
        integration_choices={"notification": "telegram",
                             "provider": ["openai", "anthropic"],
                             "ingress": "localhost"},
        user_values={},
        platform="linux",
    )


def test_maximal_plan_selects_every_module():
    plan = _maximal_plan()
    assert plan.components == frozenset(COMPONENTS)
    assert len(plan.compose_files) == len(COMPONENTS)


@pytest.mark.skipif(not shutil.which("docker"), reason="docker not available")
def test_combined_compose_validates():
    plan = _maximal_plan()
    env = {**os.environ,
           "COMPOSE_FILE": os.pathsep.join(plan.compose_files),
           "BIND_ADDR": "127.0.0.1",
           "MEM0_POSTGRES_PASSWORD": "validation-only"}
    for key, value in plan.env.items():
        env.setdefault(key, value)
    result = subprocess.run(["docker", "compose", "config", "-q"],
                            cwd=REPO_ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
