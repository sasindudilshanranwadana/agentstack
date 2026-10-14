from wizard.components import COMPONENTS, CORE_IDS, OPTIN_IDS, TIERS


def test_core_set_is_exactly_the_three_vitals():
    assert CORE_IDS == frozenset({"hermes", "omniroute", "mem0"})


def test_optin_requires_consent_set():
    assert OPTIN_IDS == frozenset({"host-gateway", "hexstrike"})


def test_every_component_has_valid_tier():
    assert all(c.tier in TIERS for c in COMPONENTS.values())


def test_hermes_requires_omniroute_and_mem0():
    assert set(COMPONENTS["hermes"].requires) == {"omniroute", "mem0"}


def test_every_requirement_target_exists():
    for c in COMPONENTS.values():
        for dep in c.requires:
            assert dep in COMPONENTS


def test_every_component_has_complete_credit():
    for c in COMPONENTS.values():
        cr = c.credit
        assert cr.tool and cr.author and cr.url and cr.license


def test_platforms_are_valid_and_host_gateway_is_linux_only():
    valid = {"linux", "macos", "windows"}
    for c in COMPONENTS.values():
        assert c.platforms and set(c.platforms) <= valid
    assert COMPONENTS["host-gateway"].platforms == ("linux",)
