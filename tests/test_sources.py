"""Every build-from-source module must have its source available: third-party
sources are cloned by scripts/fetch-sources.sh into ./vendor/*, and agentstack's
own components ship in-repo under ./src/*.
"""

import glob
import os
import re


def _build_contexts():
    pairs = []
    for cf in glob.glob("stacks/**/docker-compose.yml", recursive=True):
        text = open(cf).read()
        for m in re.finditer(r"context:\s*\$\{[A-Z_]+:-([^}]+)\}", text):
            pairs.append((cf, m.group(1)))
    return pairs


def test_vendor_contexts_are_fetched_and_src_ships_in_repo():
    fetch = open("scripts/fetch-sources.sh").read()
    contexts = _build_contexts()
    assert contexts, "expected at least one build-from-source module"
    for cf, ctx in contexts:
        if ctx.startswith("./vendor/"):
            assert ctx in fetch, f"{ctx} ({cf}) is not fetched by fetch-sources.sh"
        elif ctx.startswith("./src/"):
            assert os.path.isdir(ctx), f"{ctx} ({cf}) missing in-repo source dir"
        else:
            raise AssertionError(f"unexpected build context {ctx} in {cf}")
