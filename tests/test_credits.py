from wizard.credits import render_credits, unverified_credits


def test_credits_lists_known_tools():
    out = render_credits()
    assert "mem0" in out
    assert "Nous Research" in out
    assert "Ollama" in out


def test_credits_has_header_and_links():
    out = render_credits()
    assert out.startswith("# Credits")
    assert "https://" in out


def test_all_upstream_licenses_are_verified():
    # Every shipped tool's license is confirmed against its upstream source,
    # so the release gate (unverified_credits) has nothing to block on.
    # OmniRoute is MIT (github.com/diegosouzapw/OmniRoute), confirmed 2026-10-14.
    assert unverified_credits() == []


def test_mcp_credit_only_lists_shipped_servers():
    out = render_credits()
    # graphify is referenced as "can be added", not shipped — don't credit it
    # as if it ships.
    assert "graphify" not in out
